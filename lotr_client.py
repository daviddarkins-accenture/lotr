"""
LOTR API Client
Fetches character, quote, and movie data from The One API with caching support.
"""

import requests
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from config import Config

logger = logging.getLogger(__name__)


class LOTRClient:
    """Client for The One API"""
    
    def __init__(self):
        self.api_key = Config.LOTR_API_KEY
        self.base_url = Config.LOTR_API_BASE_URL
        self.cache_file = Path(Config.CACHE_FILE)
    
    def _get_headers(self):
        """Get request headers with API key"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json'
        }
    
    def _is_cache_valid(self):
        """Check if cached data exists and is fresh"""
        if not self.cache_file.exists():
            return False
        
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            cached_at = datetime.fromisoformat(cache_data['cached_at'])
            max_age = timedelta(hours=Config.CACHE_MAX_AGE_HOURS)
            
            if datetime.now() - cached_at < max_age:
                logger.info(f"✅ Cache is fresh (age: {datetime.now() - cached_at})")
                return True
            else:
                logger.info(f"⏰ Cache is stale (age: {datetime.now() - cached_at})")
                return False
        
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
            return False
    
    def _load_from_cache(self):
        """Load all data from cache"""
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            logger.info(f"📦 Loaded data from cache")
            return cache_data
        
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            return None
    
    def _save_to_cache(self, data):
        """Save all data to cache"""
        try:
            Config.ensure_directories()
            
            data['cached_at'] = datetime.now().isoformat()
            
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"💾 Cached all LOTR data")
        
        except Exception as e:
            logger.warning(f"Error saving cache: {e}")
    
    def _fetch_endpoint(self, endpoint, description):
        """Fetch data from a specific endpoint with pagination"""
        all_items = []
        page = 1
        total_pages = 1
        
        while page <= total_pages:
            url = f"{self.base_url}/{endpoint}"
            params = {'limit': 1000, 'page': page}
            
            logger.info(f"📖 Fetching {description} (page {page}/{total_pages})...")
            
            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            items = data.get('docs', [])
            all_items.extend(items)
            
            total_pages = data.get('pages', 1)
            page += 1
            
            # Rate limiting: be nice to the API
            if page <= total_pages:
                time.sleep(0.5)
        
        logger.info(f"✅ Fetched {len(all_items)} {description}")
        return all_items
    
    def fetch_all_data(self, force_refresh=False):
        """
        Fetch all LOTR data: characters, quotes, and movies.
        Uses cache if available.
        
        Returns:
            Dict with characters, quotes, movies, and enriched data
        """
        # Try cache first if not forcing refresh
        if not force_refresh and self._is_cache_valid():
            cached = self._load_from_cache()
            if cached:
                return cached
        
        logger.info("🌍 The journey through Middle-earth commences...")
        logger.info("Fetching all data from The One API...")
        
        try:
            # Fetch all data types
            characters = self._fetch_endpoint('character', 'characters')
            time.sleep(1)  # Rate limit pause between endpoints
            
            quotes = self._fetch_endpoint('quote', 'quotes')
            time.sleep(1)
            
            movies = self._fetch_endpoint('movie', 'movies')
            
            # Create lookup maps
            movie_map = {m['_id']: m for m in movies}
            
            # Count quotes per character and collect sample quotes
            quote_counts = {}
            sample_quotes = {}
            for quote in quotes:
                char_id = quote.get('character')
                if char_id:
                    quote_counts[char_id] = quote_counts.get(char_id, 0) + 1
                    if char_id not in sample_quotes:
                        sample_quotes[char_id] = []
                    # Keep all quotes for each character
                    movie_name = movie_map.get(quote.get('movie'), {}).get('name', 'Unknown')
                    sample_quotes[char_id].append({
                        'dialog': quote.get('dialog', ''),
                        'movie': movie_name
                    })
            
            # Enrich characters with quote counts
            for char in characters:
                char_id = char['_id']
                char['quoteCount'] = quote_counts.get(char_id, 0)
                char['sampleQuotes'] = sample_quotes.get(char_id, [])
            
            # Build the complete data package
            data = {
                'characters': characters,
                'quotes': quotes,
                'movies': movies,
                'stats': {
                    'characterCount': len(characters),
                    'quoteCount': len(quotes),
                    'movieCount': len(movies),
                    'charactersWithQuotes': len(quote_counts)
                }
            }
            
            logger.info(f"🎉 Fetched {len(characters)} characters, {len(quotes)} quotes, {len(movies)} movies")
            
            # Cache the results
            self._save_to_cache(data)
            
            return data
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise Exception(
                    "🚫 LOTR API authentication failed. "
                    "Verify your API key at https://the-one-api.dev/account"
                )
            else:
                raise Exception(f"❌ LOTR API error: {e.response.status_code} - {e.response.text}")
        
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            raise Exception(f"🔥 The journey has encountered darkness: {str(e)}")
    
    def fetch_characters(self, force_refresh=False):
        """
        Fetch all LOTR characters (legacy method for compatibility).
        """
        data = self.fetch_all_data(force_refresh)
        return data['characters']
    
    def get_character_ids(self):
        """
        Get list of character IDs (for deletion operations).
        """
        data = self.fetch_all_data()
        return [char['_id'] for char in data['characters'] if '_id' in char]
    
    def get_characters(self):
        """
        Get full character data including sampleQuotes (for deletion operations).
        """
        data = self.fetch_all_data()
        return data['characters']


# Convenience functions
def fetch_characters(force_refresh=False):
    """Fetch LOTR characters (convenience function)"""
    client = LOTRClient()
    return client.fetch_characters(force_refresh)


def fetch_all_data(force_refresh=False):
    """Fetch all LOTR data (convenience function)"""
    client = LOTRClient()
    return client.fetch_all_data(force_refresh)
