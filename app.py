#!/usr/bin/env python3
"""
LOTR Data Cloud POC - Flask Web Application
Main web UI for ingesting and deleting LOTR data.
Two-step flow: Fetch from API → Preview → Send to Data Cloud
"""

from flask import Flask, render_template, jsonify, request
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Import and validate config first
try:
    from config import Config
    Config.validate()
    Config.ensure_directories()
    logger.info("✅ Configuration validated successfully")
except ValueError as e:
    logger.error(str(e))
    sys.exit(1)
except Exception as e:
    logger.error(f"Configuration error: {e}")
    sys.exit(1)

# Import pipeline modules
from ingestion import ingest_characters, ingest_quotes
from deletion import delete_lotr_data
from lotr_client import fetch_all_data

# Create Flask app
app = Flask(__name__)

# Constants
MAX_CHARACTERS = 10000
MAX_REQUEST_SIZE = 50 * 1024 * 1024  # 50MB max request size


def sanitize_error_message(error, is_debug=False):
    """
    Sanitize error messages for client responses.
    Only show detailed errors in debug mode.
    """
    if is_debug:
        return str(error)
    else:
        # Return generic message in production
        if isinstance(error, ValueError):
            return "Invalid input provided"
        elif isinstance(error, KeyError):
            return "Missing required data"
        else:
            return "An internal error occurred. Please try again later."


@app.route('/')
def index():
    """Serve the main UI"""
    return render_template('index.html')


@app.route('/fetch', methods=['POST'])
def fetch():
    """
    Step 1: Fetch all data from The One API.
    Returns characters, quotes, and movies for preview.
    """
    try:
        logger.info("📜 Fetch endpoint called - getting all data from The One API")
        
        # Validate request size
        if request.content_length and request.content_length > MAX_REQUEST_SIZE:
            return jsonify({
                'status': 'error',
                'error': 'Request too large',
                'logs': ['🔥 Request exceeds maximum size']
            }), 413
        
        force_refresh = False
        if request.is_json:
            force_refresh = request.json.get('force_refresh', False)
        
        # Fetch all data (characters, quotes, movies)
        data = fetch_all_data(force_refresh)
        
        # Validate response data
        if not isinstance(data, dict) or 'characters' not in data:
            raise ValueError("Invalid data structure returned from API")
        
        if len(data['characters']) > MAX_CHARACTERS:
            logger.warning(f"Received {len(data['characters'])} characters, limiting to {MAX_CHARACTERS}")
            data['characters'] = data['characters'][:MAX_CHARACTERS]
        
        logs = [
            "🌍 The journey through Middle-earth commences...",
            f"📚 Gathered {data['stats']['characterCount']} characters",
            f"💬 Collected {data['stats']['quoteCount']} quotes",
            f"🎬 Found {data['stats']['movieCount']} movies",
            f"✨ {data['stats']['charactersWithQuotes']} characters have spoken in the films!"
        ]
        
        return jsonify({
            'status': 'success',
            'characters': data['characters'],
            'movies': data['movies'],
            'stats': data['stats'],
            'logs': logs
        })
    
    except ValueError as e:
        logger.error(f"Validation error in fetch: {e}")
        return jsonify({
            'status': 'error',
            'error': sanitize_error_message(e, app.debug),
            'logs': [f"🔥 Validation error: {sanitize_error_message(e, app.debug)}"]
        }), 400
    
    except Exception as e:
        logger.error(f"Fetch endpoint error: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': sanitize_error_message(e, app.debug),
            'logs': [f"🔥 Failed to fetch from The One API: {sanitize_error_message(e, app.debug)}"]
        }), 500


@app.route('/ingest', methods=['POST'])
def ingest():
    """
    Step 2: Send pre-fetched characters to Data Cloud.
    Expects characters array in request body.
    """
    try:
        logger.info("🌋 Ingest endpoint called - sending to Data Cloud")
        
        # Validate request size
        if request.content_length and request.content_length > MAX_REQUEST_SIZE:
            return jsonify({
                'status': 'error',
                'error': 'Request too large',
                'logs': ['🔥 Request exceeds maximum size']
            }), 413
        
        # Validate request format
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'error': 'Invalid request format. Expected JSON.',
                'logs': ['🔥 Invalid request format']
            }), 400
        
        if 'characters' not in request.json:
            return jsonify({
                'status': 'error',
                'error': 'No character data provided. Fetch first!',
                'logs': ['🔥 No data to ingest. Click "Fetch LOTR Data" first.']
            }), 400
        
        characters = request.json['characters']
        
        # Validate characters array
        if not isinstance(characters, list):
            return jsonify({
                'status': 'error',
                'error': 'Characters must be an array',
                'logs': ['🔥 Invalid data format']
            }), 400
        
        if len(characters) > MAX_CHARACTERS:
            return jsonify({
                'status': 'error',
                'error': f'Too many characters: {len(characters)} exceeds limit of {MAX_CHARACTERS}',
                'logs': [f'🔥 Too many characters: {len(characters)}']
            }), 400
        
        if len(characters) == 0:
            return jsonify({
                'status': 'error',
                'error': 'No characters to ingest',
                'logs': ['🔥 Character list is empty']
            }), 400
        
        # Run ingestion with pre-fetched data
        result = ingest_characters(characters)
        
        return jsonify(result)
    
    except ValueError as e:
        logger.error(f"Validation error in ingest: {e}")
        return jsonify({
            'status': 'error',
            'error': sanitize_error_message(e, app.debug),
            'logs': [f"🔥 Validation error: {sanitize_error_message(e, app.debug)}"]
        }), 400
    
    except Exception as e:
        logger.error(f"Ingest endpoint error: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': sanitize_error_message(e, app.debug),
            'logs': [f"🔥 The beacons are lit! An error has occurred: {sanitize_error_message(e, app.debug)}"]
        }), 500


@app.route('/ingest-quotes', methods=['POST'])
def ingest_quotes_endpoint():
    """
    Ingest quotes as Engagement DMO for Data Cloud Related Lists.
    Expects characters array with sampleQuotes in request body.
    """
    try:
        logger.info("📜 Quote ingest endpoint called - sending quotes to Data Cloud")
        
        # Validate request size
        if request.content_length and request.content_length > MAX_REQUEST_SIZE:
            return jsonify({
                'status': 'error',
                'error': 'Request too large',
                'logs': ['🔥 Request exceeds maximum size']
            }), 413
        
        # Validate request format
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'error': 'Invalid request format. Expected JSON.',
                'logs': ['🔥 Invalid request format']
            }), 400
        
        if 'characters' not in request.json:
            return jsonify({
                'status': 'error',
                'error': 'No character data provided. Fetch first!',
                'logs': ['🔥 No data to ingest. Click "Fetch LOTR Data" first.']
            }), 400
        
        characters = request.json['characters']
        
        # Validate characters array
        if not isinstance(characters, list):
            return jsonify({
                'status': 'error',
                'error': 'Characters must be an array',
                'logs': ['🔥 Invalid data format']
            }), 400
        
        if len(characters) == 0:
            return jsonify({
                'status': 'error',
                'error': 'No characters to extract quotes from',
                'logs': ['🔥 Character list is empty']
            }), 400
        
        # Run quote ingestion
        result = ingest_quotes(characters)
        
        return jsonify(result)
    
    except ValueError as e:
        logger.error(f"Validation error in quote ingest: {e}")
        return jsonify({
            'status': 'error',
            'error': sanitize_error_message(e, app.debug),
            'logs': [f"🔥 Validation error: {sanitize_error_message(e, app.debug)}"]
        }), 400
    
    except Exception as e:
        logger.error(f"Quote ingest endpoint error: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': sanitize_error_message(e, app.debug),
            'logs': [f"🔥 The ancient texts were lost: {sanitize_error_message(e, app.debug)}"]
        }), 500


@app.route('/wipe', methods=['POST'])
def wipe():
    """
    Trigger the deletion pipeline.
    """
    try:
        logger.info("🧹 Wipe endpoint called")
        result = delete_lotr_data()
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Wipe endpoint error: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': sanitize_error_message(e, app.debug),
            'logs': [f"🔥 The shadow grows: {sanitize_error_message(e, app.debug)}"]
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'The Grey Pilgrim stands ready'
    })


if __name__ == '__main__':
    # Determine debug mode from environment
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    if debug_mode:
        logger.warning("⚠️  Debug mode is ENABLED. Do not use in production!")
    
    print("""
╔════════════════════════════════════════════════════════════╗
║  🌋 LOTR Data Cloud POC                                    ║
║                                                            ║
║  "One Ring to Rule Them All, One POC to Bind Them"       ║
╚════════════════════════════════════════════════════════════╝

Starting Flask application...
Open your browser to: http://localhost:5001

Press Ctrl+C to stop the server.
""")
    
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=debug_mode
    )
