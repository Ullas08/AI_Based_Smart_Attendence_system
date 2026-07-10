#!/bin/bash
echo "================================================"
echo "  AI-Based Smart Attendance System"
echo "  Starting up..."
echo "================================================"

# Activate venv if exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "[OK] Virtual environment activated"
fi

# Check dependencies
python3 -c "import flask" 2>/dev/null || pip3 install -r requirements.txt

echo "[OK] Starting Flask server..."
echo "[INFO] Open browser at: http://127.0.0.1:5000"
python3 app.py
