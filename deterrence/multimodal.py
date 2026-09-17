import logging
try:
    from ScareX.config import config
except ImportError:
    from config import config

logger = logging.getLogger("ScareX.Multimodal")

class MultimodalFusionEngine:
    """
    Multimodal Fusion Engine combining Camera, Image, Video, Real Audio, and Mock Audio predictions.
    Generates unified telemetry and consistency checks.
    """
    def __init__(self):
        self.display_names = config.DISPLAY_NAMES

    def fuse_predictions(self, camera_dets, audio_res, source="Camera"):
        """
        Combine camera vision detections and audio classification results.
        Returns:
            dict: {
                'source': str,
                'camera_prediction': str,
                'camera_confidence': float,
                'audio_prediction': str,
                'audio_confidence': float,
                'multimodal_result': 'Consistent'|'Uncertain'|'No Evidence',
                'bird_evidence': 'Confirmed'|'Not confirmed',
                'is_mock': bool,
                'is_motorcycle': bool
            }
        """
        # Highest confidence camera detection
        if camera_dets and len(camera_dets) > 0:
            best_cam = max(camera_dets, key=lambda x: x.get("confidence", 0.0))
            cam_species = best_cam.get("species", "none")
            cam_conf = best_cam.get("confidence", 0.0)
            cam_disp = best_cam.get("display_name", "No bird")
        else:
            cam_species = "none"
            cam_conf = 0.0
            cam_disp = "No bird"

        # Audio classification info
        aud_info = audio_res if isinstance(audio_res, dict) else {}
        aud_species = aud_info.get("species", "none")
        aud_conf = aud_info.get("confidence", 0.0)
        aud_disp = aud_info.get("display_name", "No sound")
        is_mock = aud_info.get("is_mock", False)
        is_motorcycle = aud_info.get("is_motorcycle", False)

        has_cam_bird = cam_species in config.BIRD_SPECIES_MAP.values()
        has_aud_bird = aud_species in config.BIRD_SPECIES_MAP.values()

        # Multimodal Consistency Check
        if has_cam_bird and has_aud_bird:
            if cam_species == aud_species:
                multimodal_result = "Consistent"
                bird_evidence = "Confirmed"
            else:
                multimodal_result = "Uncertain"
                bird_evidence = "Not confirmed"
        elif has_cam_bird or (has_aud_bird and (not is_mock or config.manual_test_mode)):
            multimodal_result = "Consistent"
            bird_evidence = "Confirmed"
        else:
            multimodal_result = "No Evidence"
            bird_evidence = "Not confirmed"

        return {
            "source": source,
            "camera_prediction": f"{cam_disp} — {int(cam_conf * 100)}%" if has_cam_bird else "No bird",
            "camera_confidence": cam_conf,
            "audio_prediction": f"{aud_disp} — {int(aud_conf * 100)}%" if has_aud_bird or is_motorcycle else aud_disp,
            "audio_confidence": aud_conf,
            "multimodal_result": multimodal_result,
            "bird_evidence": bird_evidence,
            "is_mock": is_mock,
            "is_motorcycle": is_motorcycle
        }
