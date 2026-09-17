import logging
try:
    from ScareX.config import config
except ImportError:
    from config import config

logger = logging.getLogger("ScareX.CropState")

class TomatoCropStateEngine:
    """
    Evaluates Tomato Crop Condition States:
    State 1 — Healthy / Normal
    State 2 — Ripening Stage
    State 3 — Harvest Ready
    State 4 — Early Growth / Mostly Green
    State 5 — Crop Monitoring Required
    State 6 — Insufficient Data
    """
    def evaluate_crop_state(self, metrics, camera_connected=True, model_available=True):
        if not camera_connected or not model_available:
            return {
                "state_id": 6,
                "state_code": "STATE_6",
                "crop_state": "State 6 — Insufficient Data",
                "color_code": "gray",
                "badge": "INSUFFICIENT DATA",
                "recommendation": "Camera disconnected or tomato model unavailable.",
                "reason": "Hardware disconnect or inference model failure."
            }

        total = metrics.get("total_tomatoes", 0)
        if total == 0:
            return {
                "state_id": 6,
                "state_code": "STATE_6",
                "crop_state": "State 6 — Insufficient Data",
                "color_code": "gray",
                "badge": "NO TOMATOES DETECTED",
                "recommendation": "Adjust camera positioning or verify crop in frame.",
                "reason": "Zero tomatoes detected in field frame."
            }

        avg_conf = metrics.get("average_confidence", 0.0)
        fully_pct = metrics.get("fully_ripened_pct", 0.0)
        half_pct = metrics.get("half_ripened_pct", 0.0)
        green_pct = metrics.get("green_pct", 0.0)

        if avg_conf < config.low_conf_warning_threshold or metrics.get("detection_density") == "Sparse / None":
            return {
                "state_id": 5,
                "state_code": "STATE_5",
                "crop_state": "State 5 — Crop Monitoring Required",
                "color_code": "yellow",
                "badge": "MONITORING REQUIRED",
                "recommendation": "Inspect camera lens and field lighting; low average detection confidence.",
                "reason": f"Low average confidence ({int(avg_conf*100)}%) or irregular crop distribution."
            }
        elif (fully_pct / 100.0) >= config.harvest_ready_threshold:
            return {
                "state_id": 3,
                "state_code": "STATE_3",
                "crop_state": "State 3 — Harvest Ready",
                "color_code": "orange",
                "badge": "HARVEST READY",
                "recommendation": "Schedule harvesting operations immediately; high percentage of fully ripened yield.",
                "reason": f"Fully ripened tomatoes reached {fully_pct}% (crosses harvest threshold {int(config.harvest_ready_threshold*100)}%)."
            }
        elif (half_pct / 100.0) >= config.ripening_stage_threshold:
            return {
                "state_id": 2,
                "state_code": "STATE_2",
                "crop_state": "State 2 — Ripening Stage",
                "color_code": "yellow",
                "badge": "RIPENING STAGE",
                "recommendation": "Monitor crop daily; large portion of tomatoes entering half-ripened phase.",
                "reason": f"Half-ripened tomatoes reached {half_pct}% (crosses ripening threshold {int(config.ripening_stage_threshold*100)}%)."
            }
        elif (green_pct / 100.0) >= config.early_growth_threshold:
            return {
                "state_id": 4,
                "state_code": "STATE_4",
                "crop_state": "State 4 — Early Growth / Mostly Green",
                "color_code": "green",
                "badge": "EARLY GROWTH",
                "recommendation": "Maintain regular irrigation and fertilizer schedule; crop mostly in early green stage.",
                "reason": f"Green tomatoes reached {green_pct}% (crosses early growth threshold {int(config.early_growth_threshold*100)}%)."
            }
        else:
            return {
                "state_id": 1,
                "state_code": "STATE_1",
                "crop_state": "State 1 — Healthy / Normal",
                "color_code": "green",
                "badge": "HEALTHY / NORMAL",
                "recommendation": "Standard crop monitoring schedule active; balanced maturity distribution.",
                "reason": "Balanced tomato maturity distribution across green, half-ripened, and fully-ripened stages."
            }
