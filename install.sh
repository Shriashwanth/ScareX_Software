#!/bin/bash
# ScareX Raspberry Pi 5 Installation & Automated Setup Script
# Target OS: Raspberry Pi OS 64-bit (Bookworm)

set -e

echo "============================================================"
echo "      ScareX Raspberry Pi 5 Installation & Setup            "
echo "============================================================"

# 1. System Packages & Libraries
echo "[1/4] Installing system dependencies (APT)..."
sudo apt update
sudo apt install -y python3-pip python3-venv python3-opencv \
                    libatlas-base-dev libopenblas-dev \
                    v4l-utils alsa-utils ffmpeg libsdl2-mixer-2.0-0 \
                    libsndfile1

# 2. Virtual Environment Setup
echo "[2/4] Initializing Python virtual environment (venv)..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

# 3. Python Package Dependencies
echo "[3/4] Installing Python requirements..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Data Directories Setup
echo "[4/4] Creating data directories..."
mkdir -p data/mock_audio data/detections data/reports models sounds

echo "============================================================"
echo " ScareX Installation Completed Successfully!               "
echo " To start system: ./run.sh                                  "
echo " To enable as system service: sudo cp scarex.service /etc/systemd/system/ "
echo "============================================================"
