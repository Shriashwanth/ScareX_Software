import threading
import time
from src.core.logger import logger
from src.logging.db_logger import db_logger
from src.core.config_manager import ConfigManager
from src.hardware.hardware import hardware_controller
from src.alerts.alert_manager import alert_manager

class FusionEngine:
    def __init__(self, vision_module, audio_module=None):
        self.vision = vision_module
        # We retain audio_module reference but ignore it for deterrence per the prompt
        self.audio = audio_module
        self.config = ConfigManager()
        
        self.is_running = False
        self.thread = None
        self.consecutive_detections = 0
        self.lost_frames = 0
        self.scare_active = False

    def _engine_loop(self):
        logger.info("Decision engine started. Enforcing NO BIRD = NO SOUND.")
        
        # Read from config
        required_consecutive = self.config.get('required_consecutive_detections', 3)
        max_lost_frames = self.config.get('lost_detection_frames', 5)
        
        while self.is_running:
            v_bird, v_conf = self.vision.get_latest_detection()
            conf_threshold = self.config.get('camera_confidence', 0.5)
            
            # Check if camera currently sees a bird
            bird_detected = (v_bird != "No Bird Detected" and v_conf >= conf_threshold)

            if bird_detected:
                self.consecutive_detections += 1
                self.lost_frames = 0
                
                # Turn ON deterrence if required threshold met
                if self.consecutive_detections >= required_consecutive:
                    if not self.scare_active:
                        self.scare_active = True
                        self.vision.set_deterrence_state(True)
                        logger.info(f"Bird confirmed visually ({v_bird}). Starting deterrence.")
                        db_logger.log_event("SCARE_ACTIVATED", species=v_bird, confidence=v_conf, alarm_played="continuous", system_status="SCARE", detection_source="CAMERA")
                    
                    # Ensure sound keeps playing
                    alert_manager.play_continuous()
            else:
                self.consecutive_detections = 0
                
                # If a bird was previously detected, wait for lost_frames before stopping
                if self.scare_active:
                    self.lost_frames += 1
                    if self.lost_frames >= max_lost_frames:
                        logger.info("Bird lost. Stopping deterrence immediately.")
                        self.scare_active = False
                        self.vision.set_deterrence_state(False)
                        alert_manager.stop()
                        db_logger.log_event("SCARE_DEACTIVATED", species="None", confidence=0.0, alarm_played="none", system_status="MONITORING", detection_source="CAMERA")
            
            time.sleep(1.0 / self.config.get('fps', 15))

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._engine_loop, daemon=True)
            self.thread.start()
            db_logger.log_event("SYSTEM_START", system_status="RUNNING")
            logger.info("Decision engine started.")

    def stop(self):
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.scare_active = False
        if self.vision:
            self.vision.set_deterrence_state(False)
        alert_manager.stop()
        logger.info("Decision engine stopped.")
        db_logger.log_event("SYSTEM_STOP", system_status="STOPPED")
