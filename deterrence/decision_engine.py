import time
import logging
try:
    from ScareX.config import config
except ImportError:
    from config import config

logger = logging.getLogger("ScareX.DecisionEngine")

class CentralDecisionEngine:
    """
    Central Multimodal Decision Engine enforcing strict 7-tier safety priority order:
    1. Emergency Stop (Highest Priority)
    2. Mute State
    3. Manual Test Mode
    4. Real Camera Bird Detection
    5. Real Audio Bird Detection
    6. Mock Audio Test Detection
    7. Default / Non-bird Sound / Error (Deterrence OFF)
    """
    def __init__(self):
        self.emergency_stop = config.emergency_stop
        self.mute_mode = config.mute_mode
        self.manual_test_mode = config.manual_test_mode

        self.consecutive_camera_birds = 0
        self.last_trigger_time = 0.0
        self.cooldown_sec = config.cooldown_sec
        self.min_consecutive_frames = config.min_consecutive_detections

        self.display_names = config.DISPLAY_NAMES

    def evaluate(self, camera_result, audio_result):
        """
        Evaluate camera and audio predictions against priority rules.
        Returns:
            dict: {
                'deterrence_active': bool,
                'motor_active': bool,
                'speaker_active': bool,
                'bird_confirmed': bool,
                'multimodal_status': 'Consistent'|'Uncertain'|'No Evidence',
                'primary_species': str,
                'display_name': str,
                'reason': str,
                'emergency_stop': bool,
                'mute_mode': bool,
                'manual_test_mode': bool
            }
        """
        now = time.time()
        cooldown_remaining = max(0.0, self.cooldown_sec - (now - self.last_trigger_time)) if self.last_trigger_time > 0 else 0.0
        in_cooldown = cooldown_remaining > 0

        # Extract camera info
        cam_dets = camera_result.get("detections", []) if isinstance(camera_result, dict) else []
        valid_cam_birds = [d for d in cam_dets if d.get("species") in config.BIRD_SPECIES_MAP.values()]
        has_cam_bird = len(valid_cam_birds) > 0

        # Extract audio info
        aud_info = audio_result if isinstance(audio_result, dict) else {}
        has_aud_bird = aud_info.get("is_bird", False) and aud_info.get("species") in config.BIRD_SPECIES_MAP.values()
        is_motorcycle = aud_info.get("is_motorcycle", False) or aud_info.get("species") == "motorcycle_engine"
        is_mock_audio = aud_info.get("is_mock", False)

        # ----------------------------------------------------
        # Priority Tier 1: Emergency Stop
        # ----------------------------------------------------
        if self.emergency_stop:
            return self._build_decision(
                deterrence=False, motor=False, speaker=False, confirmed=False,
                status="No Evidence", species="none", name="Emergency Stop Active",
                reason="Emergency Stop activated — all actuators disabled immediately."
            )

        # ----------------------------------------------------
        # Priority Tier 2: Mute Mode
        # ----------------------------------------------------
        # (Handled during output: speaker_active = False while motor follows safe policy)

        # ----------------------------------------------------
        # Priority Tier 3 & 6: Mock Audio Handling
        # ----------------------------------------------------
        if is_mock_audio and not self.manual_test_mode:
            return self._build_decision(
                deterrence=False, motor=False, speaker=False, confirmed=False,
                status="No Evidence", species=aud_info.get("species", "mock_audio"),
                name="Mock Audio Active",
                reason="Mock audio prediction ignored in normal operation (Manual Test Mode disabled)."
            )

        # ----------------------------------------------------
        # Priority Tier 4: Real Camera Bird Detection
        # ----------------------------------------------------
        if has_cam_bird:
            self.consecutive_camera_birds += 1
            best_cam = max(valid_cam_birds, key=lambda x: x.get("confidence", 0.0))
            sp = best_cam["species"]
            disp = best_cam["display_name"]
            conf = best_cam["confidence"]

            if self.consecutive_camera_birds >= self.min_consecutive_frames:
                if not in_cooldown:
                    self.last_trigger_time = now
                    speaker_on = not self.mute_mode

                    status_str = "Consistent" if (has_aud_bird and aud_info.get("species") == sp) else "Uncertain" if has_aud_bird else "Consistent"

                    return self._build_decision(
                        deterrence=True, motor=True, speaker=speaker_on, confirmed=True,
                        status=status_str, species=sp, name=disp,
                        reason=f"Supported {disp} detected by camera (Conf: {int(conf*100)}%, Consecutive: {self.consecutive_camera_birds})."
                    )
                else:
                    return self._build_decision(
                        deterrence=False, motor=False, speaker=False, confirmed=True,
                        status="Consistent", species=sp, name=disp,
                        reason=f"Supported {disp} detected by camera, but deterrence is in cooldown ({round(cooldown_remaining, 1)}s remaining)."
                    )
        else:
            self.consecutive_camera_birds = 0

        # ----------------------------------------------------
        # Priority Tier 5: Real Audio Bird Detection
        # ----------------------------------------------------
        if has_aud_bird and (not is_mock_audio or self.manual_test_mode):
            sp = aud_info.get("species")
            disp = aud_info.get("display_name", sp.replace("_", " ").title())
            conf = aud_info.get("confidence", 0.0)

            if not in_cooldown:
                self.last_trigger_time = now
                speaker_on = not self.mute_mode

                return self._build_decision(
                    deterrence=True, motor=True, speaker=speaker_on, confirmed=True,
                    status="Consistent", species=sp, name=disp,
                    reason=f"Supported {disp} sound recognized by audio model (Conf: {int(conf*100)}%)."
                )
            else:
                return self._build_decision(
                    deterrence=False, motor=False, speaker=False, confirmed=True,
                    status="Consistent", species=sp, name=disp,
                    reason=f"Supported {disp} sound recognized, but deterrence is in cooldown ({round(cooldown_remaining, 1)}s remaining)."
                )

        # ----------------------------------------------------
        # Non-Bird Sound Rejection (Motorcycle, Speech, Weather, Silence)
        # ----------------------------------------------------
        if is_motorcycle:
            return self._build_decision(
                deterrence=False, motor=False, speaker=False, confirmed=False,
                status="No Evidence", species="motorcycle_engine", name="Motorcycle Sound",
                reason="Motorcycle engine sound rejected as non-bird sound — Deterrence OFF."
            )

        if aud_info.get("species") in config.NON_BIRD_SOUND_CLASSES:
            aud_sp = aud_info.get("species")
            disp = aud_info.get("display_name", "Non-bird Sound")
            return self._build_decision(
                deterrence=False, motor=False, speaker=False, confirmed=False,
                status="No Evidence", species=aud_sp, name=disp,
                reason=f"Non-bird sound ({disp}) rejected — Deterrence OFF."
            )

        # ----------------------------------------------------
        # Priority Tier 7: Default / No Detection / Unknown
        # ----------------------------------------------------
        return self._build_decision(
            deterrence=False, motor=False, speaker=False, confirmed=False,
            status="No Evidence", species="none", name="No Bird Detected",
            reason="No valid bird evidence detected — Deterrence OFF."
        )

    def _build_decision(self, deterrence, motor, speaker, confirmed, status, species, name, reason):
        return {
            "deterrence_active": deterrence,
            "motor_active": motor,
            "speaker_active": speaker,
            "bird_confirmed": confirmed,
            "multimodal_status": status,
            "primary_species": species,
            "display_name": name,
            "reason": reason,
            "emergency_stop": self.emergency_stop,
            "mute_mode": self.mute_mode,
            "manual_test_mode": self.manual_test_mode
        }
