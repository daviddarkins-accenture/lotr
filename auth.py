"""
Data Cloud OAuth2 Authentication Module
Handles token acquisition using client credentials flow + Data Cloud token exchange.
"""

import requests
import logging
from datetime import datetime, timedelta
from config import Config

logger = logging.getLogger(__name__)


class DataCloudAuth:
    """OAuth2 authentication handler for Data Cloud"""
    
    def __init__(self):
        self.access_token = None
        self.dc_access_token = None  # Data Cloud specific token
        self.dc_instance_url = None  # Data Cloud instance URL
        self.token_expires_at = None
    
    def get_token(self):
        """
        Get a valid Data Cloud access token.
        This is a two-step process:
        1. Get Salesforce access token
        2. Exchange it for Data Cloud access token
        
        Returns: Data Cloud access token string
        Raises: Exception if authentication fails
        """
        # Return cached token if still valid
        if self.dc_access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                logger.debug("Using cached Data Cloud access token")
                return self.dc_access_token
        
        # Step 1: Acquire Salesforce access token
        logger.info("Step 1: Acquiring Salesforce access token...")
        
        token_url = f"{Config.DC_AUTH_URL}/services/oauth2/token"
        
        payload = {
            'grant_type': 'client_credentials',
            'client_id': Config.DC_CLIENT_ID,
            'client_secret': Config.DC_CLIENT_SECRET
        }
        
        try:
            response = requests.post(
                token_url,
                data=payload,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            response.raise_for_status()
            
            sf_token_data = response.json()
            sf_access_token = sf_token_data['access_token']
            sf_instance_url = sf_token_data.get('instance_url', Config.DC_AUTH_URL)
            
            logger.info("✅ Salesforce access token acquired")
            logger.info(f"   Instance URL: {sf_instance_url}")
            
            # Step 2: Exchange for Data Cloud access token
            logger.info("Step 2: Exchanging for Data Cloud access token...")
            
            exchange_url = f"{sf_instance_url}/services/a360/token"
            
            exchange_payload = {
                'grant_type': 'urn:salesforce:grant-type:external:cdp',
                'subject_token': sf_access_token,
                'subject_token_type': 'urn:ietf:params:oauth:token-type:access_token'
            }
            
            exchange_response = requests.post(
                exchange_url,
                data=exchange_payload,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            exchange_response.raise_for_status()
            
            dc_token_data = exchange_response.json()
            self.dc_access_token = dc_token_data['access_token']
            self.dc_instance_url = dc_token_data.get('instance_url')
            
            # Set expiration (default 2 hours minus 5 min buffer)
            expires_in = dc_token_data.get('expires_in', 7200)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
            
            logger.info("✅ Data Cloud access token acquired successfully")
            logger.info(f"   Data Cloud Instance URL: {self.dc_instance_url}")
            
            return self.dc_access_token
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"Failed to acquire access token: {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_msg += f" - {error_detail}"
            except:
                error_msg += f" - {e.response.text}"
            
            logger.error(error_msg)
            raise Exception(f"🚫 The gates of Data Cloud remain locked: {error_msg}")
        
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            raise Exception(f"🔥 An unexpected shadow fell upon authentication: {str(e)}")
    
    def get_instance_url(self):
        """Get the Data Cloud instance URL (call get_token first)"""
        if not self.dc_instance_url:
            self.get_token()
        return self.dc_instance_url
    
    def get_headers(self):
        """
        Get authorization headers for API requests.
        Returns: Dict with Authorization header
        """
        token = self.get_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }


# Singleton instance
_auth_instance = None


def get_auth():
    """Get the singleton auth instance"""
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = DataCloudAuth()
    return _auth_instance

