#!/bin/bash
# LOTR Data Cloud POC - Quick Start Script

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🌋 LOTR Data Cloud POC Launcher                          ║"
echo "║  'One Ring to Rule Them All'                              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "🔨 Creating virtual environment..."
    python3 -m venv venv
    
    echo "📦 Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
    echo ""
else
    source venv/bin/activate
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found!"
    echo ""
    echo "You must run Gandalf's configuration wizard first:"
    echo "  python setup.py"
    echo ""
    echo "After configuration, run this script again to start the server."
    exit 1
fi

# Start Flask app
echo "🚀 Starting Flask application..."
echo ""
echo "Open your browser to: http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop the server."
echo ""

python app.py

