import cv2
import os
import time
import threading
import pygame
from ultralytics import YOLO
from flask import Flask, Response, jsonify, render_template

# Initialize Flask App
app = Flask(__name__, template_folder='src/dashboard/templates')

# Global State for the Dashboard
class DashboardState:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.pt_model_path = os.path.join(self.base_dir, "models", "best.pt")
        self.ncnn_model_dir = os.path.join(self.base_dir, "models", "best_ncnn_model")
        self.audio_path = os.path.join(self.base_dir, "assets", "audio", "hawk_eagle.mp3")
        
        # Detection & Sensitivity Parameters
        self.conf_threshold = 0.15
        self.required_consecutive_detections = 1
        self.lost_detection_frames = 3
        
        # State Machine Flags
        self.bird_detected = False
        self.audio_playing = False
        self.consecutive_detections = 0
        self.lost_frames = 0
        self.manual_trigger = False
        
        self.current_frame = None
        self.latest_bird = "None"
        self.latest_conf = 0.0
        self.fps = 0
        self.is_running = True
        self.class_names = {0: 'Crow', 1: 'Common Myna', 2: 'Rose Ringed Parakeet', 3: 'Peacock', 4: 'Pigeon'}
        
        # Audio Initialization
        os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
        try:
            pygame.mixer.init()
            if os.path.exists(self.audio_path):
                pygame.mixer.music.load(self.audio_path)
                pygame.mixer.music.set_volume(1.0)
            self.audio_initialized = True
        except Exception as e:
            print(f"Failed to initialize Pygame audio mixer: {e}")
            self.audio_initialized = False

        # Load Primary Custom NCNN Model
        self.init_models()

    def init_models(self):
        # Load Primary NCNN Custom Model
        param_file = os.path.join(self.ncnn_model_dir, "model.ncnn.param")
        bin_file = os.path.join(self.ncnn_model_dir, "model.ncnn.bin")
        
        if not (os.path.exists(param_file) and os.path.exists(bin_file)):
            if os.path.exists(self.pt_model_path):
                print(f"Exporting custom PyTorch model {self.pt_model_path} to NCNN format...")
                try:
                    pt_model = YOLO(self.pt_model_path)
                    pt_model.export(format="ncnn")
                except Exception as e:
                    print(f"Error exporting model to NCNN: {e}")

        self.ncnn_model = None
        if os.path.exists(self.ncnn_model_dir):
            try:
                print(f"Loading Primary Custom ScareX NCNN Model from: {self.ncnn_model_dir}")
                self.ncnn_model = YOLO(self.ncnn_model_dir, task="detect")
                if hasattr(self.ncnn_model, 'names') and self.ncnn_model.names:
                    self.class_names = self.ncnn_model.names
                print(f"NCNN Custom Class Mapping: {self.class_names}")
            except Exception as e:
                print(f"Failed to load NCNN model: {e}")

state = DashboardState()

def start_audio():
    """Audio State Machine: Start playing continuous deterrent sound if not already playing."""
    if not state.audio_playing and state.audio_initialized and pygame.mixer.get_init():
        try:
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play(-1)
            state.audio_playing = True
            print("[AUDIO STATE MACHINE] Deterrence audio STARTED at 100% volume.")
        except Exception as e:
            print(f"[AUDIO ERROR] Failed to start audio: {e}")

def stop_audio():
    """Audio State Machine: Stop continuous deterrent sound immediately."""
    if state.audio_playing and state.audio_initialized and pygame.mixer.get_init():
        try:
            pygame.mixer.music.stop()
            state.audio_playing = False
            print("[AUDIO STATE MACHINE] Deterrence audio STOPPED.")
        except Exception as e:
            print(f"[AUDIO ERROR] Failed to stop audio: {e}")

def open_webcam():
    """Helper to open webcam with DirectShow backend on Windows."""
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
    return cap

def vision_loop():
    cap = open_webcam()
    if not cap.isOpened():
        print("ERROR: Could not open laptop webcam (index 0).")
        return
        
    prev_frame_time = time.time()
    failed_frame_count = 0
    
    while state.is_running:
        ret, frame = cap.read()
        if not ret or frame is None:
            failed_frame_count += 1
            time.sleep(0.1)
            if failed_frame_count > 15:
                print("[VISION RECOVERY] Re-initializing webcam stream...")
                cap.release()
                time.sleep(0.5)
                cap = open_webcam()
                failed_frame_count = 0
            continue
            
        failed_frame_count = 0
        current_time = time.time()
        delta = current_time - prev_frame_time
        state.fps = (1.0 / delta) if delta > 0 else 0
        prev_frame_time = current_time
        
        highest_conf = 0.0
        best_bird = None
        
        # Perform Inference with Custom ScareX NCNN Model
        if state.ncnn_model:
            results = state.ncnn_model(frame, verbose=False, conf=state.conf_threshold)
            for result in results:
                for box in result.boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    class_name = state.class_names.get(cls, f"Species_{cls}")
                    
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    if conf >= state.conf_threshold:
                        if conf > highest_conf:
                            highest_conf = conf
                            best_bird = class_name
                            
                        # Draw bounding box
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        label = f"[NCNN] {class_name} {conf*100:.1f}%"
                        cv2.putText(frame, label, (x1, max(y1 - 10, 0)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # Handle Manual UI Override Trigger
        if state.manual_trigger:
            best_bird = "Simulated Bird (Manual)"
            highest_conf = 0.99

        # State Machine Logic with Consecutive-Frame Stability
        if best_bird:
            state.consecutive_detections += 1
            state.lost_frames = 0
            if state.consecutive_detections >= state.required_consecutive_detections:
                state.bird_detected = True
                state.latest_bird = best_bird
                state.latest_conf = highest_conf
                start_audio()
        else:
            state.consecutive_detections = 0
            if state.bird_detected:
                state.lost_frames += 1
                if state.lost_frames >= state.lost_detection_frames:
                    state.bird_detected = False
                    state.latest_bird = "None"
                    state.latest_conf = 0.0
                    stop_audio()
                    
        # Overlay Status Panel on Video Stream
        status_color = (0, 0, 255) if state.bird_detected else (0, 255, 0)
        status_text = f"BIRD DETECTED: {state.latest_bird}" if state.bird_detected else "NO BIRD"
        deterrence_text = "DETERRENCE: ON" if state.audio_playing else "DETERRENCE: OFF"
        
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (480, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        cv2.putText(frame, "ScareX NCNN Laptop Dashboard", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, status_text, (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        if state.bird_detected:
            cv2.putText(frame, f"Confidence: {state.latest_conf*100:.1f}%", (10, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
        cv2.putText(frame, deterrence_text, (10, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        cv2.putText(frame, f"FPS: {int(state.fps)}", (380, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Encode JPEG for web streaming
        ret, buffer = cv2.imencode('.jpg', frame)
        if ret:
            state.current_frame = buffer.tobytes()
            
        time.sleep(0.01)
        
    cap.release()

@app.route('/')
def index():
    return render_template('index.html')

def generate_video_stream():
    while True:
        if state.current_frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + state.current_frame + b'\r\n')
        time.sleep(0.05)

@app.route('/video_feed')
def video_feed():
    return Response(generate_video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/status')
def system_status():
    status_data = {
        "engine_running": True,
        "scare_active": state.audio_playing,
        "battery_level": "Laptop Power",
        "vision_bird": state.latest_bird,
        "vision_conf": round(float(state.latest_conf) * 100, 1),
        "audio_bird": "N/A",
        "audio_conf": 0.0,
        "distance_m": "N/A",
        "activations": 1 if state.audio_playing else 0,
        "last_deterrent": "Hawk/Eagle" if state.audio_playing else "None",
        "detection_source": "NCNN_CAMERA" if state.bird_detected else "None",
        "cooldown_remaining": 0
    }
    return jsonify(status_data)

@app.route('/api/trigger_scare', methods=['POST', 'GET'])
def trigger_scare():
    """Manual API endpoint to toggle audio deterrence test."""
    state.manual_trigger = not state.manual_trigger
    if not state.manual_trigger:
        stop_audio()
    return jsonify({"status": "ok", "manual_trigger": state.manual_trigger, "scare_active": state.audio_playing})

@app.route('/api/logs')
def get_logs():
    logs = []
    if state.bird_detected:
        logs.append({
            "id": 1,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": "SCARE_ACTIVATED",
            "species": state.latest_bird,
            "confidence": round(float(state.latest_conf) * 100, 1),
            "alarm_played": "hawk_eagle.mp3",
            "system_status": "SCARE",
            "detection_source": "NCNN_CAMERA"
        })
    return jsonify(logs)

if __name__ == '__main__':
    thread = threading.Thread(target=vision_loop, daemon=True)
    thread.start()
    
    print("\n" + "="*55)
    print("ScareX NCNN High-Sensitivity Dashboard is running!")
    print("Model: Custom ScareX NCNN Model (Crow, Common Myna, Parakeet, Peacock, Pigeon)")
    print("Open your browser and navigate to: http://localhost:5000")
    print("Manual Alarm Test Endpoint: http://localhost:5000/api/trigger_scare")
    print("="*55 + "\n")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        pass
    finally:
        state.is_running = False
        stop_audio()
        if state.audio_initialized:
            pygame.quit()
        cv2.destroyAllWindows()
        print("ScareX NCNN Dashboard shutdown complete.")

