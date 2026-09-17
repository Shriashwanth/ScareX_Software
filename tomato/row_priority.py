import logging
import numpy as np
try:
    from ScareX.config import config
except ImportError:
    from config import config

logger = logging.getLogger("ScareX.RowPriority")

class TomatoRowPriorityEngine:
    """
    Evaluates row-wise crop statistics and assigns monitoring priorities:
    Low, Medium, High, Critical with documented rationale strings.
    """
    def evaluate_rows(self, detections, total_rows=None):
        num_rows = total_rows or config.total_rows
        rows_stats = []

        for r in range(1, num_rows + 1):
            row_dets = [d for d in detections if d.get("row_id") == r]
            tot = len(row_dets)

            fully = sum(1 for d in row_dets if d.get("class_name") in ["b_fully_ripened", "fully_ripened"])
            half = sum(1 for d in row_dets if d.get("class_name") in ["b_half_ripened", "half_ripened"])
            green = sum(1 for d in row_dets if d.get("class_name") in ["b_green", "green"])

            confs = [d.get("confidence", 0.0) for d in row_dets]
            avg_conf = round(float(np.mean(confs)), 3) if tot > 0 else 0.0

            fully_pct = round((fully / tot) * 100.0, 1) if tot > 0 else 0.0
            half_pct = round((half / tot) * 100.0, 1) if tot > 0 else 0.0
            green_pct = round((green / tot) * 100.0, 1) if tot > 0 else 0.0

            # Rule-based priority evaluation
            if tot == 0:
                priority = "Low"
                color = "gray"
                reason = f"Row {r} — Low Priority Reason: No tomatoes detected in this crop row."
            elif fully_pct >= 50.0 or (tot >= 20 and fully >= 8):
                priority = "Critical"
                color = "red"
                reason = f"Row {r} — Critical Priority Reason: Over 50% fully-ripened tomatoes ({fully_pct}%); urgent harvest required."
            elif fully_pct >= 35.0 or half_pct >= 40.0:
                priority = "High"
                color = "orange"
                reason = f"Row {r} — High Priority Reason: High fully-ripened ({fully_pct}%) or half-ripened ({half_pct}%) percentage."
            elif half_pct >= 25.0 or tot >= 10:
                priority = "Medium"
                color = "yellow"
                reason = f"Row {r} — Medium Priority Reason: Mixed maturity distribution requiring regular monitoring."
            else:
                priority = "Low"
                color = "green"
                reason = f"Row {r} — Low Priority Reason: Mostly green tomatoes ({green_pct}%); early growth stage."

            rows_stats.append({
                "row_id": r,
                "tomato_count": tot,
                "fully_ripened_count": fully,
                "half_ripened_count": half,
                "green_count": green,
                "fully_ripened_pct": fully_pct,
                "half_ripened_pct": half_pct,
                "green_pct": green_pct,
                "average_confidence": avg_conf,
                "priority": priority,
                "color_code": color,
                "reason": reason
            })

        return rows_stats
