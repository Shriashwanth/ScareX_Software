# ScareX: Autonomous Bird Deterrence & Tomato Crop Monitoring Platform

**Target Hardware**: Raspberry Pi 5 (Raspberry Pi OS 64-bit, Bookworm)  
**Sensors & Actuators**: USB Webcam, USB Speakers, Motor Actuators, SQLite Database

---

## 🌟 System Overview

**ScareX** is a production-grade, edge-AI platform for autonomous crop protection and crop monitoring designed for Raspberry Pi 5. It integrates two complete modules into a single unified web platform:

- **Module A — Bird Species Detection, Noise Filtering & Sound Deterrence**:
  - 6-Class Vision Bird Species Recognition (`house_sparrow`, `common_myna`, `crow`, `parrot`, `pigeon`, `peacock`)
  - Real Audio Classification with Non-Bird Noise Rejection (Motorcycle engine, speech, rain, weather)
  - Synthetic Mock Audio Generator with prominent synthetic warnings
  - 7-Tier Central Decision Engine with safety priority chain
  - Motor & Speaker Actuator Control with default OFF safeguards
- **Module B — Tomato Crop Monitoring & Maturity Classification**:
  - 3-Class Tomato Maturity Detector (`b_green`, `b_half_ripened`, `b_fully_ripened`)
  - 6 Crop Condition States Engine (`Healthy`, `Ripening Stage`, `Harvest Ready`, `Early Growth`, `Crop Monitoring Required`, `Insufficient Data`)
  - Row-Wise Harvesting Priority Engine (`Low`, `Medium`, `High`, `Critical`)
  - Row statistics logging and action recommendations
- **12-Tab Multi-Module Dark Theme Web Dashboard**:
  - `1. Overview`, `2. Bird Detection`, `3. Bird Audio`, `4. Mock Audio Testing`, `5. Bird Deterrence`, `6. Tomato Recognition`, `7. Crop Condition`, `8. Row Priority`, `9. Detection History`, `10. Reports`, `11. Settings`, `12. System Health`
- **Unified PDF & CSV Report Generator**:
  - Exports combined executive reports and full raw telemetry datasets

---

## 🦅 Module A: 6-Class Bird Species

| Class ID | Class Name | Display Name |
| :--- | :--- | :--- |
| `0` | `house_sparrow` | House Sparrow |
| `1` | `common_myna` | Common Myna |
| `2` | `crow` | Crow |
| `3` | `parrot` | Parrot |
| `4` | `pigeon` | Pigeon |
| `5` | `peacock` | Peacock |

---

## 🍅 Module B: 3-Class Tomato Maturity & 6 Crop Condition States

### Maturity Classes

| Class ID | Class Name | Display Name |
| :--- | :--- | :--- |
| `0` | `b_fully_ripened` | Fully Ripened |
| `1` | `b_half_ripened` | Half Ripened |
| `2` | `b_green` | Green |

### 6 Crop Condition States

1. **State 1 — Healthy / Normal**: Balanced tomato maturity across stages.
2. **State 2 — Ripening Stage**: >35% half-ripened tomatoes.
3. **State 3 — Harvest Ready**: >40% fully-ripened tomatoes.
4. **State 4 — Early Growth / Mostly Green**: >60% green tomatoes.
5. **State 5 — Crop Monitoring Required**: Average detection confidence <40% or sparse density.
6. **State 6 — Insufficient Data**: Camera offline or 0 tomatoes detected.

---

## 🛡️ 7-Tier Central Decision Engine

1. **Emergency Stop** (Highest Priority -> ALL Actuators OFF immediately)
2. **Mute State** (Deterrence Audio Muted)
3. **Manual Test Mode** (Simulation override for synthetic audio testing)
4. **Real Camera Bird Detection** (Confirmed bird -> Deterrence ON, Motor ON)
5. **Real Audio Bird Detection** (Confirmed bird sound -> Deterrence ON, Motor ON)
6. **Mock Audio Test Detection** (Ignored in normal mode -> Deterrence OFF)
7. **Default Safety State** (All actuators OFF)

---

## 🏗️ Project Directory Structure

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
├── tomato/
│   ├── __init__.py
│   ├── detector.py          # 3-Class Tomato Maturity Detector
│   ├── maturity.py          # Maturity Ratio Analyzer
│   ├── crop_state.py        # 6 Crop Condition States Engine
│   └── row_priority.py      # Row-Wise Priority Engine
├── deterrence/
│   ├── __init__.py
│   ├── decision_engine.py   # Central 7-Tier Safety Priority Engine
│   ├── actuator.py          # Speaker & Motor Actuator Controller
│   └── multimodal.py        # Multimodal Fusion Telemetry Engine
├── dashboard/
│   ├── __init__.py
│   ├── reports.py           # PDF & CSV Telemetry & Crop Reports
│   ├── templates/
│   │   └── index.html       # 12-Tab Web Dashboard UI
│   └── static/
│       ├── style.css
│       └── script.js
├── database/
│   ├── __init__.py
│   └── manager.py           # SQLite Dual-Module Telemetry Database Manager
├── tests/
│   └── test_scarex.py       # 12-Module Automated Test Suite
├── config.py                # Global configuration settings
├── requirements.txt         # Python package dependencies
├── install.sh               # Raspberry Pi 5 automated setup script
├── run.sh                   # Execution launcher
├── PROJECT_EXPLANATION.md   # Comprehensive System Architectural Report
└── README.md                # System Documentation
```

---

## 🚀 Quick Start Guide for Raspberry Pi 5

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
python app/main.py
```

Navigate to `http://<raspberry-pi-ip>:5000` in your web browser.

---

## 📜 License

Distributed under the [MIT License](LICENSE).
