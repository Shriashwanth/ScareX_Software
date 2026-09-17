# ScareX Platform — System Architectural & Technical Explanation Report

**System Name**: ScareX Edge-AI Crop Protection & Monitoring Platform  
**Target Hardware**: Raspberry Pi 5 (Raspberry Pi OS 64-bit, Bookworm)  
**Supported Sensors**: USB Webcam, USB Microphone, USB Speakers, Motor Actuators  

---

## Executive Summary

ScareX is a unified autonomous software platform designed to solve two core agricultural challenges:
1. **Module A — Bird Detection & Deterrence**: Protecting crops from bird damage using 6-class vision detection, real-time audio classification, motorcycle engine sound filtering, synthetic mock audio generator, and a 7-tier decision safety chain.
2. **Module B — Tomato Crop Monitoring**: Monitoring tomato maturity with 3-class classification (`b_green`, `b_half_ripened`, `b_fully_ripened`), evaluating 6 Crop Condition States, calculating ripening percentages, and prioritizing harvesting rows.

---

## 1. System Architecture & Workflow

```text
               +----------------------------------+
               |        USB Webcam & Mic          |
               +----------------------------------+
                                |
               +----------------------------------+
               |   Unified Media Processing Layer |
               +----------------------------------+
                 /                              \
                v                                v
  +--------------------------+      +--------------------------+
  |  Module A: Bird Engine   |      | Module B: Tomato Engine  |
  +--------------------------+      +--------------------------+
  | • 6-Species Vision       |      | • 3-Class Maturity       |
  | • Real Audio Classifier  |      | • 6 Crop Condition States|
  | • Motorcycle Noise Filter|      | • Row-Wise Priority (1-4)|
  | • Mock Audio Generator   |      | • Ripening Ratio Metrics |
  +--------------------------+      +--------------------------+
                 \                              /
                  v                            v
               +----------------------------------+
               |   7-Tier Central Decision Engine |
               +----------------------------------+
                                |
               +----------------------------------+
               |  SQLite Dual-Module Database Log |
               +----------------------------------+
                                |
               +----------------------------------+
               | 12-Tab Web Dashboard & PDF Report|
               +----------------------------------+
```

---

## 2. 12 Integrated Software Modules

| Module # | Module Name | Primary Responsibilities |
| :--- | :--- | :--- |
| **Module 1** | **6-Class Bird Vision Detection** | Detects `house_sparrow`, `common_myna`, `crow`, `parrot`, `pigeon`, `peacock` from USB webcam feed or uploaded images/videos. Returns bounding boxes and confidence scores. |
| **Module 2** | **Real Audio Classifier & Motorcycle Rejection** | Classifies real bird sounds and explicitly rejects motorcycle engine noises using low-frequency spectral ratio checks. |
| **Module 3** | **Non-Bird Noise Filtering** | Filters environmental noise (rain, wind, thunder, speech, barking) to prevent false deterrence triggers. |
| **Module 4** | **Synthetic Mock Audio Generator** | Generates synthetic WAV audio files with `MOCK AUDIO — SYNTHETIC TEST DATA` badges. Safe by default (blocked from deterrence unless Manual Test Mode is ON). |
| **Module 5** | **7-Tier Central Decision Engine** | Enforces priority hierarchy: `Emergency Stop > Mute > Manual Test Mode > Real Camera > Real Audio > Mock Audio > OFF`. Default state is OFF. |
| **Module 6** | **3-Class Tomato Maturity Detector** | Classifies tomatoes into `b_fully_ripened`, `b_half_ripened`, `b_green` with bounding boxes and row assignment. |
| **Module 7** | **Tomato Ripening Ratio Analyzer** | Calculates percentage ratios of fully ripened, half-ripened, and green tomatoes across the field. |
| **Module 8** | **6 Crop Condition States Engine** | Evaluates overall field state: `State 1 — Healthy`, `State 2 — Ripening Stage`, `State 3 — Harvest Ready`, `State 4 — Early Growth`, `State 5 — Crop Monitoring Required`, `State 6 — Insufficient Data`. |
| **Module 9** | **Row-Wise Priority Engine** | Assigns harvesting priority (`Low`, `Medium`, `High`, `Critical`) to Rows 1–4 based on maturity density and ripeness ratio. |
| **Module 10** | **SQLite Dual-Module Database Manager** | Stores bird events, tomato detections, crop state logs, row priorities, and manual test diagnostic results in `scarex.db`. |
| **Module 11** | **Unified PDF & CSV Report Generator** | Generates executive PDF reports and full raw CSV log datasets combining bird deterrence and tomato crop telemetry. |
| **Module 12** | **12-Tab Web Dashboard & Raspberry Pi 5** | Provides a responsive dark-theme dashboard with 12 tabs: Overview, Bird Detection, Bird Audio, Mock Audio, Deterrence, Tomato Recognition, Crop Condition, Row Priority, Detection History, Reports, Settings, System Health. |

---

## 3. Database Schema

The system uses an SQLite database (`data/scarex.db`) containing five primary tables:
1. `detection_history`: Stores Module A bird vision and audio detection events.
2. `tomato_detections`: Stores Module B tomato maturity detection events.
3. `crop_state_logs`: Stores field-level 6 Crop Condition State snapshots.
4. `row_statistics_logs`: Stores row-wise (Row 1–4) tomato counts and priority levels.
5. `manual_test_logs`: Stores diagnostic test executions and pass/fail statuses.

---

## 4. Raspberry Pi 5 Compatibility

- Tested on Raspberry Pi OS 64-bit (Bookworm).
- Operates smoothly with standard USB webcams (`/dev/video0`) and USB speakers.
- Optimized for NCNN lightweight inference models on Pi 5 ARM Cortex-A76 cores.
- Fully compatible with Python 3.11+.

---

## 5. Verification Results

All 12 modules have been verified via automated unit testing (`tests/test_scarex.py`):
- **Total Tests**: 12
- **Passed**: 12
- **Failures**: 0
- **Errors**: 0
- **Result**: 100% PASS
