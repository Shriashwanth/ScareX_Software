# ScareX: Autonomous Bird Detection, Sound Filtering & Deterrence System

**Target Hardware**: Raspberry Pi 5 (Raspberry Pi OS 64-bit, Bookworm)  
**Supported Sensors & Actuators**: USB Webcam, USB Speakers, Motors/Servos/LEDs (No motor active during default/safe states)

---

## 🌟 System Overview

**ScareX** is a production-grade, edge-AI autonomous crop protection system designed for Raspberry Pi 5. It integrates **6-class vision bird species recognition**, **real audio classification with non-bird sound rejection (motorcycle/engine/speech filtering)**, **synthetic mock audio generation**, **central 7-tier decision engine with safety priority chain**, **manual testing panel**, and **automated PDF/CSV report generation**.

---

## 🦅 1. Supported 6 Bird Species

Both vision and audio detection models classify across these 6 target species:

| Class ID | Class Name | Display Name |
| :--- | :--- | :--- |
| `0` | `house_sparrow` | House Sparrow |
| `1` | `common_myna` | Common Myna |
| `2` | `crow` | Crow |
| `3` | `parrot` | Parrot |
| `4` | `pigeon` | Pigeon |
| `5` | `peacock` | Peacock |

> **Low Confidence / Unmapped Class Handling**: Displays `Unknown Bird` (or `Unknown Sound`) when confidence falls below the configured threshold.

---

## 🔊 2. Sound Rejection & Non-Bird Filtering

The audio model explicitly filters non-bird sounds:
- **Motorcycle Engine Sound** (Returns `Motorcycle Engine Sound` -> **Deterrence OFF**)
- Car Engine / Truck Engine / Tractor Engine
- Human Speech / Shouting
- Dog Barking / Cat Sound
- Rain / Wind / Thunder / Weather
- Construction Noise / Machine Noise
- Music / Silence

> **Safety Rule**: Motorcycle engine sounds and environmental noises will **NEVER** trigger deterrence audio or motor activation.

---

## 🛡️ 3. Central Decision Engine & Priority Chain

The decision engine evaluates camera and audio inputs according to a strict 7-tier priority chain:

1. **Emergency Stop** (Highest Priority -> ALL Actuators OFF immediately)
2. **Mute State** (Deterrence Audio Muted -> Motor safety policy)
3. **Manual Test Mode** (User-driven simulation override)
4. **Real Camera Bird Detection** (Confirmed 6-class bird above threshold -> Deterrence ON, Motor ON)
5. **Real Audio Bird Detection** (Confirmed 6-class bird sound above threshold -> Deterrence ON, Motor ON)
6. **Mock Audio Test Detection** (Ignored in normal operation -> Deterrence OFF by default)
7. **No Detection / Non-Bird Sound / Error** (Deterrence OFF, Motor OFF)

---

## 🔊 4. Synthetic Mock Audio Generator

- Generates synthetic WAV audio files stored in `data/mock_audio/`.
- Prominently displays `MOCK AUDIO — SYNTHETIC TEST DATA` badges.
- **Default Behavior**: `Mock Audio -> Deterrence OFF` (Activates deterrence ONLY when `Manual Test Mode` is enabled).

---

## 🏗️ 5. Project Directory Structure

```text
ScareX/
├── app/
│   ├── __init__.py
│   └── main.py              # Flask Web Server & REST API
├── camera/
│   ├── __init__.py
│   └── detector.py          # 6-Class Vision Bird Detector (NCNN/PyTorch)
├── audio/
│   ├── __init__.py
│   ├── real_audio.py        # Real Audio Classification & Noise Rejection
│   └── mock_audio.py        # Synthetic Mock Audio Generator
├── deterrence/
│   ├── __init__.py
│   ├── decision_engine.py   # Central 7-Tier Safety Priority Engine
│   ├── actuator.py          # Speaker & Motor Actuator Controller
│   └── multimodal.py        # Multimodal Fusion Telemetry Engine
├── dashboard/
│   ├── __init__.py
│   ├── reports.py           # PDF & CSV Telemetry & Rejection Reports
│   ├── templates/
│   │   └── index.html       # Responsive Dark-Theme Web Dashboard UI
│   └── static/
│       ├── style.css
│       └── script.js
├── database/
│   ├── __init__.py
│   └── manager.py           # SQLite Telemetry, Prediction Mode & Reason Logger
├── datasets/
│   └── bird_species/
│       └── data.yaml        # 6-Class Dataset Configuration
├── data/
│   ├── mock_audio/          # Synthetic WAV test files
│   ├── detections/        # Media uploads
│   └── reports/           # PDF & CSV report outputs
├── scripts/
│   ├── train_vision.py      # Vision model training script
│   ├── val_vision.py        # Evaluation (Precision, Recall, mAP, F1)
│   ├── export_ncnn.py       # NCNN model converter for RPi 5
│   ├── test_camera.py       # USB webcam diagnostic
│   ├── test_mic.py          # USB microphone diagnostic
│   ├── test_speaker.py      # USB speaker test
│   └── test_inference.py    # Benchmark latency test
├── tests/
│   └── test_scarex.py       # Comprehensive Automated Test Suite
├── config.py                # Global configuration settings
├── requirements.txt         # Python package dependencies
├── install.sh               # Raspberry Pi 5 automated setup script
├── run.sh                   # Execution launcher
├── scarex.service           # Systemd autostart unit file
├── README.md                # Documentation
└── LICENSE                  # MIT License
```

---

## 🚀 6. Quick Start Guide for Raspberry Pi 5

### 1. Installation

```bash
git clone https://github.com/Shriashwanth/ScareX_Software.git ScareX
cd ScareX
chmod +x install.sh run.sh
./install.sh
```

### 2. Running Automated Test Suite

```bash
python tests/test_scarex.py
```

### 3. Launching Web Dashboard

```bash
./run.sh
```

Navigate to `http://<raspberry-pi-ip>:5000` in your web browser.

---

## 📜 License

Distributed under the [MIT License](LICENSE).
