import logging
try:
    from ScareX.config import config
except ImportError:
    from config import config

logger = logging.getLogger("ScareX.TomatoMaturity")

class TomatoMaturityAnalyzer:
    """
    Analyzes tomato maturity metrics, percentages, average confidence, and detection density.
    """
    def analyze_detections(self, detections, counts):
        total = counts.get("total", len(detections))

        if total == 0:
            return {
                "total_tomatoes": 0,
                "fully_ripened_count": 0,
                "half_ripened_count": 0,
                "green_count": 0,
                "fully_ripened_pct": 0.0,
                "half_ripened_pct": 0.0,
                "green_pct": 0.0,
                "average_confidence": 0.0,
                "detection_density": "Sparse / None"
            }

        fully_cnt = counts.get("fully_ripened", 0)
        half_cnt = counts.get("half_ripened", 0)
        green_cnt = counts.get("green", 0)

        fully_pct = round((fully_cnt / total) * 100.0, 1)
        half_pct = round((half_cnt / total) * 100.0, 1)
        green_pct = round((green_cnt / total) * 100.0, 1)

        confs = [d.get("confidence", 0.0) for d in detections if "confidence" in d]
        avg_conf = round(float(np.mean(confs)), 3) if len(confs) > 0 else 0.0

        if total >= 25:
            density = "High Density"
        elif total >= 10:
            density = "Moderate Density"
        else:
            density = "Low Density"

        return {
            "total_tomatoes": total,
            "fully_ripened_count": fully_cnt,
            "half_ripened_count": half_cnt,
            "green_count": green_cnt,
            "fully_ripened_pct": fully_pct,
            "half_ripened_pct": half_pct,
            "green_pct": green_pct,
            "average_confidence": avg_conf,
            "detection_density": density
        }

import numpy as np
