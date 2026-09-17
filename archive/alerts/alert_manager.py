import os
import pygame
from src.core.logger import logger
from src.core.config_manager import ConfigManager

class AlertManager:
    def __init__(self):
        self.config = ConfigManager()
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        audio_path_config = self.config.get('audio_path', 'assets/audio/hawk_eagle.mp3')
        
        # Resolve absolute path for audio
        if os.path.isabs(audio_path_config):
            self.audio_path = audio_path_config
        else:
            self.audio_path = os.path.join(self.base_dir, audio_path_config)
            
        try:
            pygame.mixer.init()
            self.set_volume(self.config.get('speaker_volume', 1.0))
            self.initialized = True
            logger.info(f"[ALERT] AlertManager initialized. Audio path: {self.audio_path}")
        except Exception as e:
            logger.error(f"[ALERT] Failed to initialize pygame mixer: {e}")
            self.initialized = False

    def set_volume(self, volume):
        if self.initialized:
            pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))

    def play_continuous(self):
        """Starts playing the deterrence sound continuously if not already playing."""
        if not self.initialized:
            return False
            
        if not os.path.exists(self.audio_path):
            logger.error(f"[ALERT] Deterrence audio file not found: {self.audio_path}")
            return False

        if not pygame.mixer.music.get_busy():
            try:
                pygame.mixer.music.load(self.audio_path)
                # Play indefinitely (-1 loop)
                pygame.mixer.music.play(-1)
                logger.info(f"[ALERT] Playing deterrence sound continuously.")
                return True
            except Exception as e:
                logger.error(f"[ALERT] Error playing audio: {e}")
                return False
        return True # already playing

    def stop(self):
        """Stops the continuous deterrence sound immediately."""
        if not self.initialized:
            return
            
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            logger.info("[ALERT] Stopped deterrence sound.")

alert_manager = AlertManager()
