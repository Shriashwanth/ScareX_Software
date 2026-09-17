import os
import cv2
import threading
import time
from ultralytics import YOLO
from src.core.logger import logger
from src.core.config_manager import ConfigManager

class BirdDetector:
    def __init__(self):
        self.config = ConfigManager()
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # Load from config, default to yolo11n.pt
        model_path_config = self.config.get('model_path', 'yolo11n.pt')
        if os.path.isabs(model_path_config):
            self.model_path = model_path_config
        else:
            self.model_path = os.path.join(self.base_dir, model_path_config)
        
        self.model = None
        self.cap = None
        self.is_running = False
        self.thread = None
        
        self.current_frame = None
        self.last_detected_bird = "No Bird Detected"
        self.last_confidence = 0.0
        
        # This will be updated based on model classes
        self.target_birds = [
            "crow", "common myna", "rose ringed parakeet", "peacock", "pigeon", "parrot",
            "hen", "sparrow", "dove", "koel", "duck", "goose", "turkey", "bird"
        ]

        # Used to indicate if the deterrence system is currently active (set by fusion)
        self.deterrence_active = False

        self.load_model()

    def set_deterrence_state(self, active):
        self.deterrence_active = active

    def load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model = YOLO(self.model_path)
                logger.info(f"YOLO model loaded successfully from: {self.model_path}")
            except Exception as e:
                logger.error(f"Failed to load YOLO model: {e}")
        else:
            logger.error(f"Custom YOLO model not found: {self.model_path}")

    def _vision_loop(self):
        camera_index = self.config.get('camera_index', 0)
        resolution = self.config.get('camera_resolution', [640, 480])
        display_enabled = self.config.get('display_enabled', True)
        
        self.cap = cv2.VideoCapture(camera_index)
            
        if not self.cap.isOpened():
            logger.error(f"USB camera could not be opened. Check camera_index: {camera_index}")
            self.is_running = False
            return

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

        logger.info(f"Vision detection started on camera {camera_index}.")
        conf_threshold = self.config.get('camera_confidence', 0.5)

        # OpenCV window setup
        window_name = "ScareX Real-Time Bird Detection"
        if display_enabled:
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                logger.error("Failed to grab frame from USB Camera.")
                time.sleep(1.0)
                continue

            highest_conf = 0.0
            best_bird = "No Bird Detected"

            if self.model is not None:
                results = self.model(frame, verbose=False)
                for result in results:
                    boxes = result.boxes
                    for box in boxes:
                        conf = float(box.conf[0])
                        cls = int(box.cls[0])
                        class_name = self.model.names[cls]

                        # Check if it's one of our target birds
                        if (class_name.lower() in [t.lower() for t in self.target_birds]) and conf >= conf_threshold:
                            # Draw Bounding Box
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                            
                            display_name = class_name
                            label = f"{display_name} {conf*100:.1f}%"
                            cv2.putText(frame, label, (x1, max(y1 - 10, 0)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                            
                            if conf > highest_conf:
                                highest_conf = conf
                                best_bird = display_name
            
            self.last_detected_bird = best_bird
            self.last_confidence = highest_conf
            
            # Display status overlay
            if best_bird != "No Bird Detected":
                cv2.putText(frame, f"BIRD DETECTED: {best_bird}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.putText(frame, f"Confidence: {highest_conf:.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                cv2.putText(frame, "NO BIRD DETECTED", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
            deterrence_color = (0, 0, 255) if self.deterrence_active else (0, 255, 0)
            deterrence_text = "ON" if self.deterrence_active else "OFF"
            cv2.putText(frame, f"DETERRENCE: {deterrence_text}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, deterrence_color, 2)
            
            # Convert frame for GUI display (BGR to RGB)
            self.current_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            if display_enabled:
                cv2.imshow(window_name, frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logger.info("OpenCV window closed via 'q'.")
                    break
                    
            # Basic rate limiting
            time.sleep(0.01)

        if self.cap:
            self.cap.release()
        if display_enabled:
            cv2.destroyAllWindows()

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._vision_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        if self.cap:
            self.cap.release()
        self.current_frame = None
        cv2.destroyAllWindows()
        logger.info("Vision detection stopped.")

    def get_latest_detection(self):
        return self.last_detected_bird, self.last_confidence

    def get_current_frame(self):
        return self.current_frame

