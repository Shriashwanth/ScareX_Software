#!/bin/bash
# ScareX Execution Launcher for Raspberry Pi 5

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
echo "Starting ScareX 6-Species Bird Detection & Sound Filtering System..."
python3 app/main.py
