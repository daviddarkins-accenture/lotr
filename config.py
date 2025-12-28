"""
Configuration module for LOTR Data Cloud POC
Loads and validates environment variables with LOTR-themed error messages.
"""

from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()


class Config:
    """Centralized configuration with validation"""
    
    # LOTR API
    LOTR_API_KEY = os.getenv("LOTR_API_KEY")
    LOTR_API_BASE_URL = "https://the-one-api.dev/v2"
    
    # Data Cloud OAuth
    DC_CLIENT_ID = os.getenv("DATA_CLOUD_CLIENT_ID")
    DC_CLIENT_SECRET = os.getenv("DATA_CLOUD_CLIENT_SECRET")
    DC_AUTH_URL = os.getenv("DATA_CLOUD_AUTH_URL", "https://login.salesforce.com")
    
    # Data Cloud Ingestion API
    DC_INGESTION_URL = os.getenv("DATA_CLOUD_INGESTION_URL")
    DC_SOURCE_NAME = os.getenv("DATA_CLOUD_SOURCE_NAME", "lotr_characters")
    DC_OBJECT_NAME = os.getenv("DATA_CLOUD_OBJECT_NAME", "LotrCharacter")
    
    # Quote ingestion (Engagement DMO for Related Lists)
    # Uses same source as characters - just different object
    DC_QUOTE_SOURCE_NAME = os.getenv("DATA_CLOUD_QUOTE_SOURCE_NAME", "lotr")
    DC_QUOTE_OBJECT_NAME = os.getenv("DATA_CLOUD_QUOTE_OBJECT_NAME", "LotrQuote")
    
    # Cache settings - with type conversion
    CACHE_DIR = "data"
    CACHE_FILE = "data/lotr_raw.json"
    CACHE_MAX_AGE_HOURS = int(os.getenv("CACHE_MAX_AGE_HOURS", "24"))
    
    # Logging
    LOG_DIR = "logs"
    ERROR_LOG_FILE = "logs/ingestion_errors.json"
    
    # Ingestion settings - with type conversion
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "200"))
    DELETE_BATCH_SIZE = int(os.getenv("DELETE_BATCH_SIZE", "200"))  # API max: 200 for streaming delete
    
    # Request limits
    MAX_CHARACTERS = int(os.getenv("MAX_CHARACTERS", "10000"))
    
    @classmethod
    def validate(cls):
        """
        Validate required configuration with LOTR-themed errors.
        Raises ValueError if any required config is missing.
        """
        errors = []
        
        if not cls.LOTR_API_KEY:
            errors.append(
                "🧙‍♂️ Gandalf says: You must speak the words (LOTR_API_KEY missing)"
            )
        
        if not cls.DC_CLIENT_ID:
            errors.append(
                "🔐 The gates of Data Cloud remain locked (DATA_CLOUD_CLIENT_ID missing)"
            )
        
        if not cls.DC_CLIENT_SECRET:
            errors.append(
                "🗝️  The secret words are missing (DATA_CLOUD_CLIENT_SECRET missing)"
            )
        
        if not cls.DC_AUTH_URL:
            errors.append(
                "🌍 We need a path to the realm (DATA_CLOUD_AUTH_URL missing)"
            )
        
        if not cls.DC_INGESTION_URL:
            errors.append(
                "🏰 The destination is unknown (DATA_CLOUD_INGESTION_URL missing)"
            )
        
        # Validate numeric values
        if cls.CACHE_MAX_AGE_HOURS < 0:
            errors.append("⏰ Cache max age must be non-negative")
        
        if cls.BATCH_SIZE < 1 or cls.BATCH_SIZE > 1000:
            errors.append("📦 Batch size must be between 1 and 1000")
        
        if cls.DELETE_BATCH_SIZE < 1 or cls.DELETE_BATCH_SIZE > 200:
            errors.append("🧹 Delete batch size must be between 1 and 1000")
        
        if cls.MAX_CHARACTERS < 1:
            errors.append("👥 Max characters must be positive")
        
        if errors:
            error_message = (
                "\n\n⚠️  Configuration Incomplete!\n\n" +
                "\n".join(errors) +
                "\n\n💡 Run 'python setup.py' to configure your environment.\n"
            )
            raise ValueError(error_message)
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        os.makedirs(cls.CACHE_DIR, exist_ok=True)
        os.makedirs(cls.LOG_DIR, exist_ok=True)
