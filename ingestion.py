"""
Data Cloud Ingestion Pipeline
Transforms LOTR data and sends to Data Cloud Ingestion API.
"""

import requests
import json
import logging
from datetime import datetime
from config import Config
from auth import get_auth
from lotr_client import fetch_characters as fetch_from_api

logger = logging.getLogger(__name__)


def format_datetime_for_datacloud(dt=None):
    """
    Format datetime for Data Cloud Ingestion API.
    Required format: yyyy-MM-dd'T'HH:mm:ss.SSS'Z' (ISO 8601 with milliseconds)
    
    Args:
        dt: datetime object (defaults to utcnow())
    
    Returns:
        String in format: 2025-01-01T12:00:00.000Z
    """
    if dt is None:
        dt = datetime.utcnow()
    # Format with exactly 3 decimal places (milliseconds)
    return dt.strftime('%Y-%m-%dT%H:%M:%S.') + f'{dt.microsecond // 1000:03d}Z'


def transform_character(lotr_char):
    """
    Transform a LOTR API character object to our schema.
    
    Args:
        lotr_char: Dict from LOTR API
    
    Returns:
        Dict matching LotrCharacter schema (ALL fields included, empty string if missing)
    
    Raises:
        ValueError: If required fields are missing
    """
    # Validate required fields
    if '_id' not in lotr_char:
        raise ValueError("Character missing required '_id' field")
    
    if 'name' not in lotr_char or not lotr_char['name']:
        raise ValueError("Character missing required 'name' field")
    
    # Helper to clean values - convert NaN/null to empty string
    def clean_value(val):
        if val is None or val == 'NaN' or (isinstance(val, str) and not val.strip()):
            return ''
        return str(val)
    
    # Include ALL fields - Data Cloud schema requires them
    transformed = {
        'characterId': lotr_char['_id'],
        'name': lotr_char.get('name', 'Unknown'),
        'ingestedAt': format_datetime_for_datacloud(),
        # All optional fields with empty string defaults
        'race': clean_value(lotr_char.get('race')),
        'gender': clean_value(lotr_char.get('gender')),
        'birth': clean_value(lotr_char.get('birth')),
        'death': clean_value(lotr_char.get('death')),
        'realm': clean_value(lotr_char.get('realm')),
        'wikiUrl': clean_value(lotr_char.get('wikiUrl')),
        'height': clean_value(lotr_char.get('height')),
        'hair': clean_value(lotr_char.get('hair')),
        'spouse': clean_value(lotr_char.get('spouse')),
    }
    
    return transformed


def extract_quotes_from_characters(characters):
    """
    Extract quotes from character data into flat quote records.
    Each quote becomes its own record linked to the character.
    
    Args:
        characters: List of character dicts with sampleQuotes
    
    Returns:
        List of quote dicts matching LotrQuote schema
    """
    quotes = []
    ingested_at = format_datetime_for_datacloud()
    
    for char in characters:
        char_id = char.get('_id', '')
        char_name = char.get('name', 'Unknown')
        sample_quotes = char.get('sampleQuotes', [])
        
        if not sample_quotes:
            continue
        
        for idx, quote in enumerate(sample_quotes):
            if not quote.get('dialog'):
                continue
            
            # Generate unique quote ID: characterId_index
            quote_id = f"{char_id}_{idx}"
            
            quotes.append({
                'quoteId': quote_id,
                'characterId': char_id,
                'dialog': quote.get('dialog', ''),
                'movie': quote.get('movie', ''),
                'characterName': char_name,
                'ingestedAt': ingested_at
            })
    
    return quotes


def send_quote_batch_to_ingestion_api(batch, batch_num, total_batches):
    """
    Send a batch of quote records to the Ingestion API.
    Uses the quote-specific source and object names.
    """
    auth = get_auth()
    
    dc_instance_url = auth.get_instance_url()
    if dc_instance_url:
        base_url = f"https://{dc_instance_url}"
    else:
        base_url = Config.DC_INGESTION_URL
    
    # Quote-specific ingestion URL
    url = (
        f"{base_url}/api/v1/ingest/sources/"
        f"{Config.DC_QUOTE_SOURCE_NAME}/{Config.DC_QUOTE_OBJECT_NAME}"
    )
    
    payload = {"data": batch}
    
    logger.info(f"📜 Inscribing the ancient words (batch {batch_num}/{total_batches})...")
    logger.info(f"   Sending {len(batch)} quotes to Ingestion API")
    logger.info(f"   URL: {url}")
    
    try:
        response = requests.post(
            url,
            headers=auth.get_headers(),
            json=payload,
            timeout=60
        )
        
        response.raise_for_status()
        result = response.json()
        logger.info(f"✅ Quote batch {batch_num}/{total_batches} ingested successfully")
        
        return {'success': True, 'batch_num': batch_num, 'count': len(batch), 'response': result}
    
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text[:500]}"
        logger.error(f"❌ Quote batch {batch_num}/{total_batches} failed: {error_msg}")
        return {'success': False, 'batch_num': batch_num, 'count': len(batch), 'error': error_msg}
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Quote batch {batch_num}/{total_batches} failed: {error_msg}")
        return {'success': False, 'batch_num': batch_num, 'count': len(batch), 'error': error_msg}


def ingest_quotes(characters):
    """
    Extract and ingest quotes from character data into Data Cloud.
    Quotes are ingested as an Engagement DMO for Related Lists.
    
    Args:
        characters: List of character dicts with sampleQuotes
    
    Returns:
        Dict with ingestion summary
    """
    logs = []
    
    try:
        logs.append("📜 Gathering the wisdom of Middle-earth...")
        logger.info("Starting quote extraction and ingestion")
        
        # Extract quotes from characters
        quotes = extract_quotes_from_characters(characters)
        
        if len(quotes) == 0:
            logs.append("⚠️ No quotes found in character data")
            return {
                'status': 'warning',
                'ingestedCount': 0,
                'message': 'No quotes found to ingest',
                'logs': logs
            }
        
        logs.append(f"✨ {len(quotes)} quotes extracted from {len(characters)} characters")
        
        # Batch the quotes
        batches = list(batch_records(quotes, Config.BATCH_SIZE))
        total_batches = len(batches)
        logs.append(f"📦 Split into {total_batches} batches")
        
        # Send batches
        results = []
        for i, batch in enumerate(batches, 1):
            result = send_quote_batch_to_ingestion_api(batch, i, total_batches)
            results.append(result)
        
        # Summary
        successful = sum(1 for r in results if r['success'])
        failed = sum(1 for r in results if not r['success'])
        successful_records = sum(r['count'] for r in results if r['success'])
        
        if failed == 0:
            logs.append(f"🎉 {successful_records} quotes have been preserved in the archives")
            status = "success"
        else:
            logs.append(f"⚠️ Partial success: {successful}/{total_batches} batches succeeded")
            status = "partial"
        
        return {
            'status': status,
            'ingestedCount': successful_records,
            'totalQuotes': len(quotes),
            'successfulBatches': successful,
            'failedBatches': failed,
            'totalBatches': total_batches,
            'timestamp': format_datetime_for_datacloud(),
            'logs': logs
        }
    
    except Exception as e:
        error_msg = str(e)
        logs.append(f"🔥 The words were lost: {error_msg}")
        logger.error(f"Quote ingestion failed: {e}", exc_info=True)
        
        return {
            'status': 'error',
            'error': error_msg,
            'logs': logs
        }


def batch_records(records, batch_size):
    """
    Split records into batches.
    """
    for i in range(0, len(records), batch_size):
        yield records[i:i + batch_size]


def send_batch_to_ingestion_api(batch, batch_num, total_batches):
    """
    Send a batch of records to the Ingestion API.
    """
    auth = get_auth()
    
    # Get the Data Cloud instance URL from token exchange
    # This is the correct URL returned by the token exchange
    dc_instance_url = auth.get_instance_url()
    if dc_instance_url:
        # Use the URL from token exchange (preferred)
        base_url = f"https://{dc_instance_url}"
    else:
        # Fallback to config
        base_url = Config.DC_INGESTION_URL
    
    # Actual ingestion URL
    url = (
        f"{base_url}/api/v1/ingest/sources/"
        f"{Config.DC_SOURCE_NAME}/{Config.DC_OBJECT_NAME}"
    )
    
    # Payload structure with data wrapper (required for streaming)
    payload = {
        "data": batch
    }
    
    logger.info(f"🔥 Forging the records in the fires of Mount Doom (batch {batch_num}/{total_batches})...")
    logger.info(f"   Sending {len(batch)} records to Ingestion API")
    logger.info(f"   URL: {url}")
    logger.info(f"   Sample record: {json.dumps(batch[0], indent=2)[:500]}")
    
    try:
        response = requests.post(
            url,
            headers=auth.get_headers(),
            json=payload,
            timeout=60
        )
        
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"✅ Batch {batch_num}/{total_batches} ingested successfully")
        
        return {
            'success': True,
            'batch_num': batch_num,
            'count': len(batch),
            'response': result
        }
    
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP {e.response.status_code}"
        # Log full response for debugging
        logger.error(f"   Response headers: {dict(e.response.headers)}")
        logger.error(f"   Response body: {e.response.text}")
        try:
            error_detail = e.response.json()
            error_msg += f": {json.dumps(error_detail)}"
        except (ValueError, json.JSONDecodeError):
            error_msg += f": {e.response.text[:500]}"
        
        logger.error(f"❌ Batch {batch_num}/{total_batches} failed: {error_msg}")
        log_error(batch_num, error_msg, batch)
        
        return {
            'success': False,
            'batch_num': batch_num,
            'count': len(batch),
            'error': error_msg
        }
    
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error: {str(e)}"
        logger.error(f"❌ Batch {batch_num}/{total_batches} failed: {error_msg}")
        log_error(batch_num, error_msg, batch)
        
        return {
            'success': False,
            'batch_num': batch_num,
            'count': len(batch),
            'error': error_msg
        }
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Batch {batch_num}/{total_batches} failed: {error_msg}", exc_info=True)
        log_error(batch_num, error_msg, batch)
        
        return {
            'success': False,
            'batch_num': batch_num,
            'count': len(batch),
            'error': error_msg
        }


def log_error(batch_num, error_msg, batch_data):
    """Log an ingestion error to file"""
    try:
        Config.ensure_directories()
        
        error_entry = {
            'timestamp': format_datetime_for_datacloud(),
            'batch_num': batch_num,
            'error': error_msg,
            'record_count': len(batch_data),
            'sample_ids': [r.get('characterId') for r in batch_data[:3]]
        }
        
        errors = []
        try:
            with open(Config.ERROR_LOG_FILE, 'r') as f:
                errors = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        errors.append(error_entry)
        
        with open(Config.ERROR_LOG_FILE, 'w') as f:
            json.dump(errors, f, indent=2)
    
    except Exception as e:
        logger.warning(f"Could not write error log: {e}")


def ingest_characters(characters):
    """
    Ingest pre-fetched characters into Data Cloud.
    Called from the /ingest endpoint after user confirms.
    
    Args:
        characters: List of character dicts from LOTR API
    
    Returns:
        Dict with ingestion summary
    
    Raises:
        ValueError: If input validation fails
    """
    logs = []
    
    try:
        # Validate input
        if not isinstance(characters, list):
            raise ValueError("Characters must be a list")
        
        if len(characters) == 0:
            raise ValueError("Character list cannot be empty")
        
        if len(characters) > Config.MAX_CHARACTERS:
            raise ValueError(f"Too many characters: {len(characters)} exceeds limit of {Config.MAX_CHARACTERS}")
        
        logs.append("⚔️ So it begins... Sending to Data Cloud")
        logger.info("Starting Data Cloud ingestion")
        
        # Transform to our schema
        logs.append("🔄 Transforming the ancient texts...")
        transformed = []
        for i, char in enumerate(characters):
            try:
                transformed.append(transform_character(char))
            except ValueError as e:
                logger.warning(f"Skipping invalid character at index {i}: {e}")
                continue
        
        if len(transformed) == 0:
            raise ValueError("No valid characters to ingest after transformation")
        
        logs.append(f"✨ {len(transformed)} records prepared for ingestion")
        
        # Batch the records
        batches = list(batch_records(transformed, Config.BATCH_SIZE))
        total_batches = len(batches)
        logs.append(f"📦 Split into {total_batches} batches")
        
        # Send batches to Ingestion API
        results = []
        for i, batch in enumerate(batches, 1):
            result = send_batch_to_ingestion_api(batch, i, total_batches)
            results.append(result)
        
        # Calculate summary
        successful = sum(1 for r in results if r['success'])
        failed = sum(1 for r in results if not r['success'])
        total_records = sum(r['count'] for r in results)
        successful_records = sum(r['count'] for r in results if r['success'])
        
        if failed == 0:
            logs.append(f"🎉 It is done. {successful_records} records have passed into the West")
            logs.append("✨ You bow to no one. (ingestion complete)")
            status = "success"
        else:
            logs.append(f"⚠️ Partial success: {successful}/{total_batches} batches succeeded")
            logs.append(f"   {successful_records}/{total_records} records ingested")
            status = "partial"
        
        return {
            'status': status,
            'ingestedCount': successful_records,
            'totalRecords': total_records,
            'successfulBatches': successful,
            'failedBatches': failed,
            'totalBatches': total_batches,
            'timestamp': format_datetime_for_datacloud(),
            'logs': logs
        }
    
    except ValueError as e:
        error_msg = str(e)
        logs.append(f"🔥 Validation error: {error_msg}")
        logger.error(f"Ingestion validation failed: {e}")
        
        return {
            'status': 'error',
            'error': error_msg,
            'logs': logs
        }
    
    except Exception as e:
        error_msg = str(e)
        logs.append(f"🔥 One does not simply... ingest data without errors: {error_msg}")
        logger.error(f"Ingestion pipeline failed: {e}", exc_info=True)
        
        return {
            'status': 'error',
            'error': error_msg,
            'logs': logs
        }


def ingest_lotr_data(force_refresh=False):
    """
    Legacy function: Fetch and ingest in one step.
    Kept for backward compatibility.
    """
    logs = []
    
    try:
        logs.append("⚔️ So it begins...")
        logger.info("Starting LOTR data ingestion pipeline")
        
        # Fetch characters
        logs.append("🌍 The journey through Middle-earth commences...")
        characters = fetch_from_api(force_refresh)
        logs.append(f"📚 Gathered {len(characters)} tales from The One API")
        
        # Use the new ingest function
        result = ingest_characters(characters)
        
        # Merge logs
        result['logs'] = logs + result.get('logs', [])
        result['sampleCharacters'] = characters[:3]
        
        return result
    
    except Exception as e:
        error_msg = str(e)
        logs.append(f"🔥 One does not simply... ingest data without errors: {error_msg}")
        logger.error(f"Ingestion pipeline failed: {e}", exc_info=True)
        
        return {
            'status': 'error',
            'error': error_msg,
            'logs': logs
        }
