"""
Data Cloud Deletion Pipeline
Removes LOTR character data from Data Cloud AND Salesforce Accounts.

Uses Bulk API for Data Cloud deletes (required for Profile category with Record Modified Field).
"""

import requests
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from config import Config
from auth import get_auth
from lotr_client import LOTRClient

logger = logging.getLogger(__name__)


def get_salesforce_token():
    """Get Salesforce access token (not Data Cloud token)."""
    token_url = f"{Config.DC_AUTH_URL}/services/oauth2/token"
    payload = {
        'grant_type': 'client_credentials',
        'client_id': Config.DC_CLIENT_ID,
        'client_secret': Config.DC_CLIENT_SECRET
    }
    response = requests.post(
        token_url,
        data=payload,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=30
    )
    response.raise_for_status()
    return response.json()


def delete_salesforce_accounts():
    """
    Delete all Salesforce Account records where characterId__c is populated.
    
    Returns:
        Dict with deletion results
    """
    logger.info("🏰 Searching for Accounts with LOTR characters...")
    
    try:
        # Get Salesforce token
        token_data = get_salesforce_token()
        sf_token = token_data['access_token']
        sf_instance = token_data['instance_url']
        
        headers = {
            'Authorization': f'Bearer {sf_token}',
            'Content-Type': 'application/json'
        }
        
        # Query for Accounts with characterId__c populated
        query = "SELECT Id, Name, characterId__c FROM Account WHERE characterId__c != null"
        query_url = f"{sf_instance}/services/data/v59.0/query?q={requests.utils.quote(query)}"
        
        logger.info(f"   Querying: {query}")
        query_response = requests.get(query_url, headers=headers, timeout=30)
        query_response.raise_for_status()
        
        results = query_response.json()
        records = results.get('records', [])
        total_count = results.get('totalSize', 0)
        
        logger.info(f"   Found {total_count} Account(s) with characterId__c")
        
        if total_count == 0:
            return {
                'success': True,
                'deleted_count': 0,
                'message': 'No Accounts found with characterId__c'
            }
        
        # Delete each Account
        deleted_count = 0
        failed_count = 0
        
        for record in records:
            account_id = record['Id']
            account_name = record.get('Name', 'Unknown')
            
            delete_url = f"{sf_instance}/services/data/v59.0/sobjects/Account/{account_id}"
            
            try:
                delete_response = requests.delete(delete_url, headers=headers, timeout=30)
                delete_response.raise_for_status()
                deleted_count += 1
                logger.info(f"   ✅ Deleted Account: {account_name}")
            except Exception as e:
                failed_count += 1
                logger.error(f"   ❌ Failed to delete Account {account_name}: {e}")
        
        return {
            'success': failed_count == 0,
            'deleted_count': deleted_count,
            'failed_count': failed_count,
            'total_found': total_count
        }
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
        logger.error(f"Failed to delete Salesforce Accounts: {error_msg}")
        return {
            'success': False,
            'error': error_msg,
            'deleted_count': 0
        }
    except Exception as e:
        logger.error(f"Failed to delete Salesforce Accounts: {e}")
        return {
            'success': False,
            'error': str(e),
            'deleted_count': 0
        }


def format_datetime_for_datacloud(dt=None):
    """
    Format datetime for Data Cloud Ingestion API.
    Required format: yyyy-MM-dd'T'HH:mm:ss.SSS'Z' (ISO 8601 with milliseconds)
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.strftime('%Y-%m-%dT%H:%M:%S.') + f'{dt.microsecond // 1000:03d}Z'


def delete_from_datacloud_bulk(record_ids, object_name, source_name):
    """
    Delete records from Data Cloud using Bulk API.
    
    For Profile category with Record Modified Field (ingestedAt):
    - CSV format: NO HEADER
    - Column 1: Primary key value
    - Column 2: DateTime greater than the original ingestedAt
    
    Args:
        record_ids: List of record IDs to delete
        object_name: The Data Cloud object name (e.g., 'LotrCharacter', 'LotrQuote')
        source_name: The Data Cloud source name
    
    Returns:
        Dict with deletion results
    """
    auth = get_auth()
    token = auth.get_token()
    instance_url = auth.get_instance_url()
    
    base_url = f"https://{instance_url}"
    headers_json = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    headers_csv = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'text/csv'
    }
    
    try:
        # Step 1: Create bulk delete job
        logger.info(f"📋 Creating bulk delete job for {object_name}...")
        
        job_payload = {
            'object': object_name,
            'sourceName': source_name,
            'operation': 'delete'
        }
        
        job_resp = requests.post(
            f"{base_url}/api/v1/ingest/jobs",
            headers=headers_json,
            json=job_payload,
            timeout=30
        )
        job_resp.raise_for_status()
        
        job_data = job_resp.json()
        job_id = job_data['id']
        logger.info(f"   Job ID: {job_id}")
        
        # Step 2: Prepare CSV (NO HEADER, 2 columns for Profile category)
        # Column 1: Primary key value
        # Column 2: DateTime greater than original ingestedAt
        logger.info("📝 Preparing delete CSV (no header, 2 columns)...")
        
        # Use a future datetime to ensure it's greater than any ingestedAt
        future_dt = (datetime.now(timezone.utc) + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        # Build CSV: "primary_key","future_datetime"
        csv_lines = [f'"{record_id}","{future_dt}"' for record_id in record_ids]
        csv_content = '\n'.join(csv_lines)
        
        logger.info(f"   Total records: {len(record_ids)}")
        logger.info(f"   Sample: {csv_lines[0] if csv_lines else 'N/A'}")
        
        # Step 3: Upload CSV
        logger.info("📤 Uploading CSV to job...")
        
        upload_resp = requests.put(
            f"{base_url}/api/v1/ingest/jobs/{job_id}/batches",
            headers=headers_csv,
            data=csv_content,
            timeout=120
        )
        upload_resp.raise_for_status()
        logger.info("   ✅ CSV uploaded")
        
        # Step 4: Close job to trigger processing
        logger.info("🔒 Closing job to trigger processing...")
        
        close_resp = requests.patch(
            f"{base_url}/api/v1/ingest/jobs/{job_id}",
            headers=headers_json,
            json={'state': 'UploadComplete'},
            timeout=30
        )
        close_resp.raise_for_status()
        logger.info("   ✅ Job closed - processing started")
        
        # Step 5: Poll for completion (optional, with timeout)
        logger.info("⏳ Waiting for job to complete...")
        
        job_url = f"{base_url}/api/v1/ingest/jobs/{job_id}"
        max_polls = 36  # ~6 minutes max
        
        for i in range(max_polls):
            time.sleep(10)
            
            status_resp = requests.get(job_url, headers=headers_json, timeout=30)
            job_status = status_resp.json()
            state = job_status.get('state')
            
            if state == 'JobComplete':
                logger.info(f"   🎉 Job complete! Processing time: {job_status.get('totalProcessingTime')}")
                return {
                    'success': True,
                    'job_id': job_id,
                    'state': state,
                    'records_submitted': len(record_ids),
                    'processing_time': job_status.get('totalProcessingTime')
                }
            elif state == 'Failed':
                logger.error(f"   ❌ Job failed!")
                return {
                    'success': False,
                    'job_id': job_id,
                    'state': state,
                    'error': 'Job failed'
                }
            else:
                logger.info(f"   [{i+1}/{max_polls}] State: {state}...")
        
        # Timeout - job still running
        logger.warning("   ⏱️ Job still running after timeout - check Data Cloud UI")
        return {
            'success': True,  # Job submitted successfully, just taking long
            'job_id': job_id,
            'state': 'InProgress',
            'records_submitted': len(record_ids),
            'message': 'Job submitted - check Data Stream Refresh History for completion'
        }
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
        logger.error(f"Bulk delete failed: {error_msg}")
        return {
            'success': False,
            'error': error_msg
        }
    except Exception as e:
        logger.error(f"Bulk delete failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def get_quote_ids_from_characters(characters):
    """
    Generate quote IDs based on character data.
    Quote IDs are formatted as: {characterId}_{index}
    
    Args:
        characters: List of character dicts with sampleQuotes
    
    Returns:
        List of quote IDs
    """
    quote_ids = []
    for char in characters:
        char_id = char.get('_id', '')
        sample_quotes = char.get('sampleQuotes', [])
        for idx in range(len(sample_quotes)):
            quote_ids.append(f"{char_id}_{idx}")
    return quote_ids


def delete_lotr_data():
    """
    Main deletion function:
    1. Delete Salesforce Accounts where characterId__c is populated
    2. Delete LOTR characters from Data Cloud using Bulk API
    3. Delete LOTR quotes from Data Cloud using Bulk API
    
    Returns:
        Dict with deletion summary
    """
    logs = []
    
    try:
        logs.append("🔥 The fires are lit! Beginning the great purge...")
        logger.info("Starting LOTR data deletion pipeline")
        
        # Step 1: Delete Salesforce Accounts with characterId__c
        logs.append("🏰 Step 1: Purging Salesforce Accounts...")
        account_result = delete_salesforce_accounts()
        
        if account_result.get('deleted_count', 0) > 0:
            logs.append(f"   ✅ Deleted {account_result['deleted_count']} Account(s) from Salesforce")
        else:
            logs.append(f"   ℹ️  No Accounts with characterId__c found")
        
        if account_result.get('failed_count', 0) > 0:
            logs.append(f"   ⚠️  Failed to delete {account_result['failed_count']} Account(s)")
        
        # Get character data for both character and quote deletion
        logs.append("📋 Gathering the names of those who must depart...")
        client = LOTRClient()
        characters = client.get_characters()
        character_ids = [c.get('_id') for c in characters if c.get('_id')]
        
        # Also include any test records that might exist
        test_ids = ['test123', 'test_validation_123', 'test_validation_456', 'test_flow_001']
        all_character_ids = character_ids + test_ids
        
        # Step 2: Delete Characters from Data Cloud
        logs.append("☁️  Step 2: Purging Character records from Data Cloud...")
        logs.append(f"📝 {len(all_character_ids)} characters marked for removal")
        
        char_result = {'success': True, 'records_submitted': 0}
        if all_character_ids:
            char_result = delete_from_datacloud_bulk(
                all_character_ids, 
                Config.DC_OBJECT_NAME, 
                Config.DC_SOURCE_NAME
            )
            
            if char_result.get('success'):
                logs.append(f"   ✅ Character delete job submitted ({len(all_character_ids)} records)")
            else:
                logs.append(f"   ❌ Character delete failed: {char_result.get('error', 'Unknown')}")
        else:
            logs.append("   ℹ️  No characters to delete")
        
        # Step 3: Delete Quotes from Data Cloud
        logs.append("💬 Step 3: Purging Quote records from Data Cloud...")
        quote_ids = get_quote_ids_from_characters(characters)
        logs.append(f"📝 {len(quote_ids)} quotes marked for removal")
        
        quote_result = {'success': True, 'records_submitted': 0}
        if quote_ids:
            quote_result = delete_from_datacloud_bulk(
                quote_ids,
                Config.DC_QUOTE_OBJECT_NAME,
                Config.DC_QUOTE_SOURCE_NAME
            )
            
            if quote_result.get('success'):
                logs.append(f"   ✅ Quote delete job submitted ({len(quote_ids)} records)")
            else:
                logs.append(f"   ❌ Quote delete failed: {quote_result.get('error', 'Unknown')}")
        else:
            logs.append("   ℹ️  No quotes to delete")
        
        # Summary
        if char_result.get('success') and quote_result.get('success'):
            logs.append("✨ The age of LOTR data is over.")
            logs.append(f"   {account_result.get('deleted_count', 0)} Salesforce Accounts banished")
            logs.append(f"   {len(all_character_ids)} characters queued for deletion")
            logs.append(f"   {len(quote_ids)} quotes queued for deletion")
            status = "success"
        else:
            status = "partial" if (char_result.get('success') or quote_result.get('success')) else "error"
        
        return {
            'status': status,
            'deletedCount': len(all_character_ids) + len(quote_ids),
            'charactersDeleted': len(all_character_ids) if char_result.get('success') else 0,
            'quotesDeleted': len(quote_ids) if quote_result.get('success') else 0,
            'accountsDeleted': account_result.get('deleted_count', 0),
            'characterJobId': char_result.get('job_id'),
            'quoteJobId': quote_result.get('job_id'),
            'timestamp': format_datetime_for_datacloud(),
            'logs': logs
        }
    
    except Exception as e:
        error_msg = str(e)
        logs.append(f"🔥 The shadow grows: {error_msg}")
        logger.error(f"Deletion pipeline failed: {e}", exc_info=True)
        
        return {
            'status': 'error',
            'error': error_msg,
            'logs': logs
        }
