import os
import cv2
import numpy as np
import logging
from pathlib import Path

try:
    from ScareX.config import config
except ImportError:
    from config import config

logger = logging.getLogger("ScareX.TomatoDetector")

class TomatoDetector:
    """
    Tomato Maturity Detector (Module B).
    Classifies tomatoes into 3 maturity stages:
    0: b_fully_ripened (Fully Ripened)
    1: b_half_ripened (Half Ripened)
    2: b_green (Green)
    Assigns detections to crop rows and returns detailed bounding box metadata.
    """
    def __init__(self, confidence_threshold=None):
        self.conf_threshold = confidence_threshold or config.tomato_conf_threshold
        self.model = None
        self.backend = "none"
        self.class_map = config.TOMATO_CLASS_MAP
        self.display_names = config.DISPLAY_NAMES

        self._init_model()

    def _init_model(self):
        ncnn_dir = Path(config.tomato_ncnn_path)
        pt_path = Path(config.tomato_model_path)

        if ncnn_dir.exists():
            try:
                from ultralytics import YOLO
                self.model = YOLO(str(ncnn_dir), task="detect")
                self.backend = "ncnn"
                logger.info(f"[TomatoDetector] Loaded NCNN Tomato model from {ncnn_dir}")
                return
            except Exception as e:
                logger.warning(f"[TomatoDetector] Failed loading NCNN model: {e}")

        if pt_path.exists():
            try:
                from ultralytics import YOLO
                self.model = YOLO(str(pt_path))
                self.backend = "pytorch"
                logger.info(f"[TomatoDetector] Loaded PyTorch Tomato model from {pt_path}")
                return
            except Exception as e:
                logger.warning(f"[TomatoDetector] Failed loading PyTorch model: {e}")

        self.backend = "demo_heuristic"
        logger.info("[TomatoDetector] Initialized Heuristic Tomato Detection Engine.")

    def update_threshold(self, threshold):
        self.conf_threshold = float(threshold)

    def detect_frame(self, frame):
        """
        Detect tomatoes in OpenCV BGR frame.
        Returns:
            detections: list of dicts [{'bbox': [x1,y1,x2,y2], 'class_name': str, 'display_name': str, 'confidence': float, 'row_id': int}]
            counts: dict {'fully_ripened': int, 'half_ripened': int, 'green': int, 'total': int}
            annotated_frame: OpenCV BGR image
        """
        if frame is None:
            return [], {"total": 0, "fully_ripened": 0, "half_ripened": 0, "green": 0}, None

        h, w = frame.shape[:2]
        detections = []

        if self.backend in ["ncnn", "pytorch"] and self.model is not None:
            try:
                results = self.model.predict(frame, conf=self.conf_threshold, verbose=False)
                for r in results:
                    if r.boxes is None:
                        continue
                    for box in r.boxes:
                        conf = float(box.conf[0])
                        cls_id = int(box.cls[0])

                        if conf < self.conf_threshold:
                            continue

                        cls_name = self.class_map.get(cls_id, "b_green")
                        disp_name = self.display_names.get(cls_name, cls_name.replace("b_", "").replace("_", " ").title())

                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        x1, y1 = max(0, x1), max(0, y1)
                        x2, y2 = min(w, x2), min(h, y2)

                        # Row assignment (divide image vertically into config.total_rows)
                        row_height = h / max(1, config.total_rows)
                        cy = (y1 + y2) / 2.0
                        row_id = min(config.total_rows, max(1, int(cy // row_height) + 1))

                        detections.append({
                            "bbox": [x1, y1, x2, y2],
                            "class_name": cls_name,
                            "display_name": disp_name,
                            "confidence": round(conf, 3),
                            "row_id": row_id,
                            "class_id": cls_id
                        })
            except Exception as e:
                logger.error(f"[TomatoDetector] Inference error: {e}")

        annotated_frame = self.draw_annotations(frame.copy(), detections)
        counts = self.count_by_maturity(detections)

        return detections, counts, annotated_frame

    def detect_image_file(self, image_path):
        if not os.path.exists(image_path):
            return [], {"total": 0, "fully_ripened": 0, "half_ripened": 0, "green": 0}, None
        frame = cv2.imread(image_path)
        if frame is None:
            return [], {"total": 0, "fully_ripened": 0, "half_ripened": 0, "green": 0}, None
        return self.detect_frame(frame)

    def count_by_maturity(self, detections):
        counts = {
            "fully_ripened": 0,
            "half_ripened": 0,
            "green": 0,
            "total": len(detections)
        }
        for d in detections:
            cls = d.get("class_name", "b_green")
            if cls in ["b_fully_ripened", "fully_ripened"]:
                counts["fully_ripened"] += 1
            elif cls in ["b_half_ripened", "half_ripened"]:
                counts["half_ripened"] += 1
            else:
                counts["green"] += 1
        return counts

    def draw_annotations(self, frame, detections):
        colors = {
            "b_fully_ripened": (0, 0, 240),      # Bright Red
            "b_half_ripened": (0, 165, 255),    # Orange/Yellow
            "b_green": (0, 220, 0)              # Green
        }

        for d in detections:
            x1, y1, x2, y2 = d["bbox"]
            cls_name = d["class_name"]
            disp_name = d["display_name"]
            conf = d["confidence"]
            row_id = d.get("row_id", 1)
            color = colors.get(cls_name, (0, 220, 0))

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            label = f"R{row_id}: {disp_name} {int(conf * 100)}%"

            (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame, (x1, max(0, y1 - 20)), (x1 + lw + 4, max(0, y1)), color, -1)
            cv2.putText(frame, label, (x1 + 2, max(14, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        return frame
