from flask import Flask, render_template, Response, jsonify
import cv2
import threading
import time
import os
from src.core.logger import logger
from src.logging.db_logger import db_logger
from src.hardware.hardware import hardware_controller
from src.core.config_manager import ConfigManager

# App initialization
app = Flask(__name__)
config = ConfigManager()

# Global references to engine and modules (set in main.py)
fusion_engine_ref = None
vision_module_ref = None
audio_module_ref = None

def generate_video_stream():
    """Generator function to yield video frames for the web stream."""
    while True:
        if vision_module_ref:
            frame = vision_module_ref.get_current_frame()
            if frame is not None:
                # Convert RGB back to BGR for encoding if needed, or directly encode
                # Since get_current_frame() might return RGB, check and convert
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                else:
                    frame_bgr = frame
                    
                ret, buffer = cv2.imencode('.jpg', frame_bgr)
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.05)
  
@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route."""
    return Response(generate_video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/status')
def system_status():
    """API endpoint to get current system status."""
    try:
        events = db_logger.get_recent_events(limit=100)
        activations = sum(1 for e in events if e[2] == "SCARE_ACTIVATED")
        last_deterrent = "None"
        detection_source = "None"
        for e in events:
            if e[2] == "SCARE_ACTIVATED":
                last_deterrent = e[5] if len(e) > 5 else "None"
                detection_source = e[7] if len(e) > 7 else "UNKNOWN"
                break

        current_time = time.time()
        last_scare = getattr(fusion_engine_ref, 'last_scare_time', 0) if fusion_engine_ref else 0
        cooldown = config.get('deterrent_cooldown', 10.0)
        cooldown_remaining = max(0, int(cooldown - (current_time - last_scare)))
        
        status_data = {
            "engine_running": fusion_engine_ref.is_running if fusion_engine_ref else False,
            "scare_active": fusion_engine_ref.scare_active if fusion_engine_ref else False,
            "battery_level": "95%", # Mock battery
            "vision_bird": "None",
            "vision_conf": 0.0,
            "audio_bird": "None",
            "audio_conf": 0.0,
            "distance_m": hardware_controller.get_distance(),
            "activations": activations,
            "last_deterrent": last_deterrent,
            "detection_source": detection_source,
            "cooldown_remaining": cooldown_remaining
        }
        
        if vision_module_ref:
            v_bird, v_conf = vision_module_ref.get_latest_detection()
            status_data["vision_bird"] = v_bird
            status_data["vision_conf"] = round(float(v_conf) * 100, 1) if v_conf is not None else 0.0
            
        if audio_module_ref:
            a_bird, a_conf = audio_module_ref.get_latest_detection()
            status_data["audio_bird"] = a_bird
            status_data["audio_conf"] = round(float(a_conf) * 100, 1) if a_conf is not None else 0.0

        return jsonify(status_data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return str(e), 500

@app.route('/api/logs')
def get_logs():
    """API endpoint to fetch recent event logs."""
    try:
        events = db_logger.get_recent_events(limit=15)
        # Convert tuples to list of dicts
        logs = []
        for row in events:
            # Sanitize row data (decode bytes if any)
            sanitized_row = [x.decode('utf-8') if isinstance(x, bytes) else x for x in row]
            logs.append({
                "id": sanitized_row[0],
                "timestamp": sanitized_row[1],
                "event_type": sanitized_row[2],
                "species": sanitized_row[3],
                "confidence": sanitized_row[4],
                "alarm_played": sanitized_row[5],
                "system_status": sanitized_row[6],
                "detection_source": sanitized_row[7] if len(sanitized_row) > 7 else "UNKNOWN"
            })
        return jsonify(logs)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return str(e), 500

def start_flask_app(fusion, vision, audio):
    global fusion_engine_ref, vision_module_ref, audio_module_ref
    fusion_engine_ref = fusion
    vision_module_ref = vision
    audio_module_ref = audio
    
    port = config.get("flask_port", 5000)
    logger.info(f"Starting Flask Dashboard on port {port}...")
    
    # Run in a separate thread so it doesn't block
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False), daemon=True).start()
