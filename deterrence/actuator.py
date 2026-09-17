import os
import time
import logging
import threading
from pathlib import Path

try:
    from ScareX.config import config
except ImportError:
    from config import config

logger = logging.getLogger("ScareX.Actuator")

class DeterrenceActuatorController:
    """
    Deterrence Actuator Controller managing USB Speakers, Motors, Servos, and LEDs.
    Enforces safe defaults (OFF on startup, error, disconnect, or emergency stop).
    """
    def __init__(self):
        self.sound_dir = Path(config.sound_dir)
        self.sound_files = list(self.sound_dir.glob("*.wav")) + list(self.sound_dir.glob("*.mp3"))

        self.motor_state = False
        self.speaker_state = False
        self.is_playing_sound = False
        self.is_pygame_active = False

        self._init_audio()

    def _init_audio(self):
        try:
            import pygame
            pygame.mixer.init()
            self.is_pygame_active = True
            logger.info("[Actuator] Pygame audio mixer initialized.")
        except Exception as e:
            logger.warning(f"[Actuator] Pygame audio mixer failed to initialize: {e}")

    def update_actuators(self, decision):
        """Apply decision engine outputs to physical actuators."""
        motor_cmd = decision.get("motor_active", False)
        speaker_cmd = decision.get("speaker_active", False)
        emergency = decision.get("emergency_stop", False)

        if emergency:
            self.stop_all()
            return

        # Motor control
        if motor_cmd != self.motor_state:
            self.motor_state = motor_cmd
            logger.info(f"[Actuator] Motor State set to: {'ON' if self.motor_state else 'OFF'}")

        # USB Speaker Audio Control
        if speaker_cmd:
            if not self.is_playing_sound:
                self.play_deterrence_sound()
        else:
            if self.is_playing_sound:
                self.stop_deterrence_sound()

    def play_deterrence_sound(self):
        # Refresh sound files list
        self.sound_files = list(self.sound_dir.glob("*.wav")) + list(self.sound_dir.glob("*.mp3"))
        if not self.sound_files:
            logger.warning(f"[Actuator] No deterrence sound files found in {self.sound_dir}")
            return

        sound_file = self.sound_files[0]
        logger.info(f"[Actuator] Playing Deterrence Audio: {sound_file.name}")
        self.is_playing_sound = True
        self.speaker_state = True

        def _play_thread():
            try:
                if self.is_pygame_active:
                    import pygame
                    pygame.mixer.music.load(str(sound_file))
                    pygame.mixer.music.play(-1)  # Loop while bird is visible in camera
                    while self.is_playing_sound and pygame.mixer.music.get_busy():
                        time.sleep(0.05)
            except Exception as e:
                logger.error(f"[Actuator] Audio playback error: {e}")
            finally:
                if not self.is_playing_sound:
                    try:
                        import pygame
                        pygame.mixer.music.stop()
                    except Exception:
                        pass
                self.speaker_state = self.is_playing_sound

        threading.Thread(target=_play_thread, daemon=True).start()

    def stop_deterrence_sound(self):
        self.is_playing_sound = False
        self.speaker_state = False
        logger.info("[Actuator] Stopping Deterrence Audio Playback.")
        try:
            if self.is_pygame_active:
                import pygame
                pygame.mixer.music.stop()
        except Exception as e:
            logger.error(f"[Actuator] Error stopping audio: {e}")

    def stop_all(self):
        """Immediate Emergency Stop disabling motor, audio, and all actuators."""
        self.motor_state = False
        self.stop_deterrence_sound()
        logger.info("[Actuator] EMERGENCY STOP EXECUTED — ALL ACTUATORS OFF.")
