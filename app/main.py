import os
import time
import logging
from pathlib import Path
from flask import Flask, render_template, Response, jsonify, request, send_file, werkzeug

try:
    from ScareX.config import config
    from ScareX.camera.detector import CameraBirdDetector
    from ScareX.audio.real_audio import RealAudioClassifier
    from ScareX.audio.mock_audio import MockAudioGenerator
    from ScareX.deterrence.decision_engine import CentralDecisionEngine
    from ScareX.deterrence.actuator import DeterrenceActuatorController
    from ScareX.deterrence.multimodal import MultimodalFusionEngine
    from ScareX.database.manager import ScareXDatabaseManager
    from ScareX.dashboard.reports import ScareXReportGenerator
except ImportError:
    from config import config
    from camera.detector import CameraBirdDetector
    from audio.real_audio import RealAudioClassifier
    from audio.mock_audio import MockAudioGenerator
    from deterrence.decision_engine import CentralDecisionEngine
    from deterrence.actuator import DeterrenceActuatorController
    from deterrence.multimodal import MultimodalFusionEngine
    from database.manager import ScareXDatabaseManager
    from dashboard.reports import ScareXReportGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ScareX.App")

template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dashboard", "templates")
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dashboard", "static")

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# Initialize core system singletons
db_manager = ScareXDatabaseManager()
camera_detector = CameraBirdDetector()
real_audio_classifier = RealAudioClassifier()
mock_audio_generator = MockAudioGenerator()
decision_engine = CentralDecisionEngine()
actuator = DeterrenceActuatorController()
fusion_engine = MultimodalFusionEngine()
report_generator = ScareXReportGenerator(db_manager)

# Global State Containers
latest_camera_dets = []
latest_audio_res = {"status": "success", "is_bird": False, "species": "none", "display_name": "No sound", "confidence": 0.0}
camera_cap = None
camera_connected = False

def init_camera():
    global camera_cap, camera_connected
    try:
        import cv2
        idx = config.camera_index
        camera_cap = cv2.VideoCapture(idx)
        if not camera_cap.isOpened() and isinstance(idx, int):
            camera_cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        camera_connected = camera_cap.isOpened()
        if camera_connected:
            camera_cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.frame_width)
            camera_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.frame_height)
            logger.info(f"[App] USB Webcam opened on index {idx}.")
        else:
            logger.warning(f"[App] Could not open USB webcam at index {idx}.")
    except Exception as e:
        logger.error(f"[App] Error opening camera: {e}")
        camera_connected = False

init_camera()

def generate_mjpeg_stream():
    global latest_camera_dets
    import cv2
    while True:
        if camera_cap and camera_connected:
            ret, frame = camera_cap.read()
            if ret and frame is not None:
                dets, counts, ann_frame = camera_detector.detect_frame(frame)
                latest_camera_dets = dets

                # Run decision evaluation
                decision = decision_engine.evaluate({"detections": dets}, latest_audio_res)
                actuator.update_actuators(decision)

                # Log event if deterrence state changes
                if decision["deterrence_active"]:
                    sp = decision["primary_species"]
                    db_manager.log_event(
                        species=sp, display_name=decision["display_name"],
                        confidence=0.90, source="Camera", prediction_mode="Real Inference",
                        bird_confirmed=True, deterrence_triggered=True,
                        motor_state=decision["motor_active"], speaker_state=decision["speaker_active"],
                        mock_mode=False, manual_test_mode=decision["manual_test_mode"],
                        emergency_stop=decision["emergency_stop"], reason=decision["reason"],
                        model_type=camera_detector.backend
                    )

                ret_enc, jpeg = cv2.imencode(".jpg", ann_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                if ret_enc:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                    time.sleep(0.04)
                    continue

        # Fallback blank frame stream
        import numpy as np
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(blank, "ScareX Camera Offline / Reconnecting...", (100, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        ret_enc, jpeg = cv2.imencode(".jpg", blank)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        time.sleep(0.2)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/video_feed")
def video_feed():
    return Response(generate_mjpeg_stream(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/api/status")
def api_status():
    decision = decision_engine.evaluate({"detections": latest_camera_dets}, latest_audio_res)
    fusion = fusion_engine.fuse_predictions(latest_camera_dets, latest_audio_res)
    stats = db_manager.get_summary_stats()

    model_health = {
        "camera_model": camera_detector.backend != "none",
        "audio_model": real_audio_classifier.backend != "unavailable",
        "mock_audio_gen": True,
        "database": True,
        "camera_connection": camera_connected,
        "speaker_connection": actuator.is_pygame_active or os.name == 'posix'
    }

    return jsonify({
        "status": "online",
        "decision": decision,
        "fusion": fusion,
        "telemetry": stats,
        "model_health": model_health,
        "controls": {
            "emergency_stop": decision_engine.emergency_stop,
            "mute_mode": decision_engine.mute_mode,
            "manual_test_mode": decision_engine.manual_test_mode,
            "vision_threshold": camera_detector.conf_threshold,
            "audio_threshold": real_audio_classifier.conf_threshold
        }
    })

@app.route("/api/detect/image", methods=["POST"])
def api_detect_image():
    if "file" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files["file"]
    upload_dir = Path(config.detections_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"upload_img_{int(time.time())}_{werkzeug.utils.secure_filename(file.filename)}"
    file.save(str(file_path))

    dets, counts, _ = camera_detector.detect_image_file(str(file_path))
    decision = decision_engine.evaluate({"detections": dets}, latest_audio_res)

    best_sp = dets[0]["species"] if len(dets) > 0 else "none"
    best_disp = dets[0]["display_name"] if len(dets) > 0 else "No bird"
    best_conf = dets[0]["confidence"] if len(dets) > 0 else 0.0

    db_manager.log_event(
        species=best_sp, display_name=best_disp, confidence=best_conf,
        source="Image Upload", prediction_mode="Real Inference", media_path=str(file_path),
        bird_confirmed=len(dets) > 0, deterrence_triggered=decision["deterrence_active"],
        motor_state=decision["motor_active"], speaker_state=decision["speaker_active"],
        mock_mode=False, manual_test_mode=decision["manual_test_mode"],
        emergency_stop=decision["emergency_stop"], reason=decision["reason"]
    )

    return jsonify({
        "status": "success",
        "detections": dets,
        "counts": counts,
        "decision": decision
    })

@app.route("/api/detect/audio", methods=["POST"])
def api_detect_audio():
    global latest_audio_res

    if "file" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    file = request.files["file"]
    upload_dir = Path(config.detections_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"upload_aud_{int(time.time())}_{werkzeug.utils.secure_filename(file.filename)}"
    file.save(str(file_path))

    res = real_audio_classifier.classify_audio_file(str(file_path))
    latest_audio_res = res
    decision = decision_engine.evaluate({"detections": latest_camera_dets}, latest_audio_res)

    db_manager.log_event(
        species=res.get("species", "unknown_sound"), display_name=res.get("display_name", "Unknown Sound"),
        confidence=res.get("confidence", 0.0), source="Real Audio Upload",
        prediction_mode="Real Inference", media_path=str(file_path),
        bird_confirmed=res.get("is_bird", False), deterrence_triggered=decision["deterrence_active"],
        motor_state=decision["motor_active"], speaker_state=decision["speaker_active"],
        mock_mode=False, manual_test_mode=decision["manual_test_mode"],
        emergency_stop=decision["emergency_stop"], reason=decision["reason"]
    )

    return jsonify({
        "status": "success",
        "audio_result": res,
        "decision": decision
    })

@app.route("/api/mock_audio/generate", methods=["POST"])
def api_generate_mock_audio():
    global latest_audio_res
    data = request.json or {}
    target_class = data.get("species", "crow")
    duration = float(data.get("duration", 3.0))
    sample_rate = int(data.get("sample_rate", 22050))
    mock_conf = float(data.get("confidence", 0.90))

    res = mock_audio_generator.generate_mock_audio(
        target_class=target_class, duration_sec=duration,
        sample_rate=sample_rate, mock_conf=mock_conf
    )

    latest_audio_res = {
        "status": "success",
        "is_bird": res["is_bird"],
        "species": res["species"],
        "display_name": res["display_name"],
        "confidence": res["confidence"],
        "is_motorcycle": res["is_motorcycle"],
        "is_mock": True,
        "message": res["warning"]
    }

    decision = decision_engine.evaluate({"detections": latest_camera_dets}, latest_audio_res)

    db_manager.log_event(
        species=res["species"], display_name=res["display_name"], confidence=res["confidence"],
        source="Mock Audio Generator", prediction_mode="Demo / Synthetic", media_path=res["file_path"],
        bird_confirmed=res["is_bird"], deterrence_triggered=decision["deterrence_active"],
        motor_state=decision["motor_active"], speaker_state=decision["speaker_active"],
        mock_mode=True, manual_test_mode=decision["manual_test_mode"],
        emergency_stop=decision["emergency_stop"], reason=decision["reason"]
    )

    return jsonify({
        "status": "success",
        "mock_result": res,
        "decision": decision
    })

@app.route("/api/controls/emergency_stop", methods=["POST"])
def api_emergency_stop():
    data = request.json or {}
    enable = data.get("enable", not decision_engine.emergency_stop)
    decision_engine.emergency_stop = enable
    if enable:
        actuator.stop_all()
    logger.info(f"[App] Emergency Stop toggled to {enable}.")
    return jsonify({"status": "success", "emergency_stop": decision_engine.emergency_stop})

@app.route("/api/controls/mute", methods=["POST"])
def api_mute():
    data = request.json or {}
    enable = data.get("enable", not decision_engine.mute_mode)
    decision_engine.mute_mode = enable
    if enable:
        actuator.stop_deterrence_sound()
    logger.info(f"[App] Mute Mode toggled to {enable}.")
    return jsonify({"status": "success", "mute_mode": decision_engine.mute_mode})

@app.route("/api/controls/manual_test_mode", methods=["POST"])
def api_manual_test_mode():
    data = request.json or {}
    enable = data.get("enable", not decision_engine.manual_test_mode)
    decision_engine.manual_test_mode = enable
    logger.info(f"[App] Manual Test Mode toggled to {enable}.")
    return jsonify({"status": "success", "manual_test_mode": decision_engine.manual_test_mode})

@app.route("/api/manual_test/run", methods=["POST"])
def api_run_manual_test():
    data = request.json or {}
    test_type = data.get("test_type", "motorcycle_audio")

    expected = "OFF"
    actual = "OFF"
    status = "PASS"
    input_desc = test_type.replace("_", " ").title()

    if test_type == "test_camera_crow":
        input_desc = "Test Camera Crow Detection"
        expected = "Deterrence ON"
        test_cam_dets = [{"species": "crow", "display_name": "Crow", "confidence": 0.94, "bbox": [50, 50, 200, 200]}]
        decision = decision_engine.evaluate({"detections": test_cam_dets}, {})
        actual = "Deterrence ON" if decision["deterrence_active"] else "Deterrence OFF"
        status = "PASS" if decision["deterrence_active"] else "FAIL"

    elif test_type == "test_motorcycle_audio":
        input_desc = "Test Motorcycle Audio Noise"
        expected = "Deterrence OFF (Non-bird sound)"
        aud = {"status": "success", "is_bird": False, "species": "motorcycle_engine", "display_name": "Motorcycle Engine Sound", "confidence": 0.98, "is_motorcycle": True, "is_mock": False}
        decision = decision_engine.evaluate({}, aud)
        actual = "Deterrence OFF" if not decision["deterrence_active"] else "Deterrence ON"
        status = "PASS" if not decision["deterrence_active"] else "FAIL"

    elif test_type == "test_mock_audio_normal":
        input_desc = "Test Mock Audio (Normal Mode)"
        expected = "Deterrence OFF (Ignored)"
        aud = {"status": "success", "is_bird": True, "species": "peacock", "display_name": "Peacock", "confidence": 0.95, "is_mock": True}
        decision_engine.manual_test_mode = False
        decision = decision_engine.evaluate({}, aud)
        actual = "Deterrence OFF" if not decision["deterrence_active"] else "Deterrence ON"
        status = "PASS" if not decision["deterrence_active"] else "FAIL"

    elif test_type == "test_emergency_stop":
        input_desc = "Test Emergency Stop Priority"
        expected = "All Actuators OFF"
        decision_engine.emergency_stop = True
        test_cam_dets = [{"species": "crow", "display_name": "Crow", "confidence": 0.99, "bbox": [50, 50, 200, 200]}]
        decision = decision_engine.evaluate({"detections": test_cam_dets}, {})
        actual = "All Actuators OFF" if not decision["deterrence_active"] else "Actuators ON"
        status = "PASS" if not decision["deterrence_active"] else "FAIL"

    db_manager.log_manual_test(
        input_type=input_desc, expected_result=expected, actual_result=actual,
        deterrence_state="ON" if "ON" in actual else "OFF",
        motor_state="ON" if "ON" in actual else "OFF",
        audio_state="OFF" if decision_engine.mute_mode else "ACTIVE", status=status
    )

    return jsonify({
        "status": "success",
        "test_name": input_desc,
        "expected": expected,
        "actual": actual,
        "result_status": status
    })

@app.route("/api/reports/generate", methods=["POST"])
def api_generate_reports():
    res = report_generator.generate_all_reports()
    return jsonify({
        "status": "success",
        "message": "Reports generated successfully",
        "reports": {
            "pdf": "/api/reports/download/pdf",
            "csv": "/api/reports/download/csv"
        },
        "stats": res["stats"]
    })

@app.route("/api/reports/download/<file_type>")
def api_download_report(file_type):
    target = Path(config.reports_dir) / f"latest_report.{file_type.lower()}"
    if target.exists():
        return send_file(target, as_attachment=True)
    else:
        report_generator.generate_all_reports()
        if target.exists():
            return send_file(target, as_attachment=True)
        return jsonify({"error": "Report file not found"}), 404

if __name__ == "__main__":
    logger.info(f"[App] Starting ScareX Web Server on http://{config.dashboard_host}:{config.flask_port}")
    app.run(host=config.dashboard_host, port=config.flask_port, debug=False, threaded=True)
