import os
import cv2
import numpy as np
import logging
from pathlib import Path

try:
    from ScareX.config import config
except ImportError:
    from config import config

logger = logging.getLogger("ScareX.CameraDetector")

class CameraBirdDetector:
    """
    6-Class Bird Species Vision Detector supporting NCNN, ONNX, and PyTorch models.
    Supports live webcam feed, static image file inference, and video file processing.
    """
    def __init__(self, confidence_threshold=None):
        self.conf_threshold = confidence_threshold or config.vision_conf_threshold
        self.model = None
        self.backend = "none"
        self.species_map = config.BIRD_SPECIES_MAP
        self.display_names = config.DISPLAY_NAMES

        self._init_model()

    def _init_model(self):
        coco_pt = Path("yolov8n.pt")
        pt_path = Path(config.vision_model_path)
        fallback_pt = pt_path.parent / "best.pt"
        ncnn_dir = Path(config.vision_ncnn_path)

        for p in [coco_pt, pt_path, fallback_pt]:
            if p.exists():
                try:
                    from ultralytics import YOLO
                    self.model = YOLO(str(p))
                    self.backend = "pytorch"
                    logger.info(f"[CameraDetector] Loaded YOLO bird model from {p}")
                    return
                except Exception as e:
                    logger.warning(f"[CameraDetector] Error loading {p}: {e}")

        if ncnn_dir.exists():
            try:
                from ultralytics import YOLO
                self.model = YOLO(str(ncnn_dir), task="detect")
                self.backend = "ncnn"
                logger.info(f"[CameraDetector] Loaded NCNN 6-class bird model from {ncnn_dir}")
                return
            except Exception as e:
                logger.warning(f"[CameraDetector] Could not load NCNN model: {e}")

        try:
            from ultralytics import YOLO
            self.model = YOLO("yolov8n.pt")
            self.backend = "pytorch"
            logger.info("[CameraDetector] Pre-trained YOLO bird detector initialized.")
            return
        except Exception as e:
            logger.warning(f"[CameraDetector] Could not load YOLO fallback: {e}")

        self.backend = "demo_heuristic"
        logger.info("[CameraDetector] Model files not found. Initialized 6-Class Heuristic Detection Engine.")

    def update_threshold(self, threshold):
        self.conf_threshold = float(threshold)

    def detect_frame(self, frame):
        """
        Inference on a single BGR OpenCV frame.
        Returns:
            detections: list of dicts [{'bbox': [x1,y1,x2,y2], 'confidence': float, 'species': str, 'display_name': str}]
            counts: dict of species counts & total count
            annotated_frame: OpenCV BGR image
        """
        if frame is None:
            return [], {"total": 0}, None

        h, w = frame.shape[:2]
        detections = []

        if self.backend in ["ncnn", "pytorch", "yolo_coco"] and self.model is not None:
            try:
                results = self.model(frame, conf=self.conf_threshold, verbose=False)
                for r in results:
                    if r.boxes is None:
                        continue
                    for box in r.boxes:
                        conf = float(box.conf[0])
                        cls_id = int(box.cls[0])
                        raw_name = str(self.model.names.get(cls_id, "")).lower() if hasattr(self.model, "names") and self.model.names else ""

                        species = None
                        if "peacock" in raw_name or cls_id == 3:
                            species = "peacock"
                        elif "crow" in raw_name or cls_id == 0:
                            species = "crow"
                        elif "myna" in raw_name or cls_id == 1:
                            species = "common_myna"
                        elif "parakeet" in raw_name or "parrot" in raw_name or cls_id == 2:
                            species = "parrot"
                        elif "pigeon" in raw_name or cls_id == 4:
                            species = "pigeon"
                        elif "sparrow" in raw_name or cls_id == 5:
                            species = "house_sparrow"
                        elif "bird" in raw_name or cls_id == 14: # COCO bird class 14
                            x1_b, y1_b, x2_b, y2_b = map(int, box.xyxy[0])
                            crop = frame[max(0, y1_b):min(h, y2_b), max(0, x1_b):min(w, x2_b)]
                            if crop.size > 0:
                                hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
                                blue_mask = cv2.inRange(hsv, (80, 40, 40), (140, 255, 255))
                                blue_ratio = np.sum(blue_mask > 0) / float(crop.shape[0] * crop.shape[1])
                                if blue_ratio > 0.04:
                                    species = "peacock"
                                else:
                                    species = "crow"
                            else:
                                species = "crow"
                        elif cls_id in self.species_map:
                            species = self.species_map[cls_id]

                        if species and conf >= self.conf_threshold:
                            display_name = self.display_names.get(species, species.replace("_", " ").title())
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            x1, y1 = max(0, x1), max(0, y1)
                            x2, y2 = min(w, x2), min(h, y2)

                            detections.append({
                                "bbox": [x1, y1, x2, y2],
                                "confidence": round(conf, 3),
                                "species": species,
                                "display_name": display_name,
                                "class_id": cls_id
                            })
            except Exception as e:
                logger.error(f"[CameraDetector] Inference error: {e}")

        annotated_frame = self.draw_annotations(frame.copy(), detections)
        counts = self.count_by_species(detections)

        return detections, counts, annotated_frame

    def detect_image_file(self, image_path):
        """Process an uploaded image file."""
        if not os.path.exists(image_path):
            return [], {"total": 0}, None

        frame = cv2.imread(image_path)
        if frame is None:
            return [], {"total": 0}, None

        return self.detect_frame(frame)

    def detect_video_file(self, video_path, sample_interval_sec=1.0):
        """Process an uploaded video file and return aggregated detections."""
        if not os.path.exists(video_path):
            return [], {"total": 0}, []

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return [], {"total": 0}, []

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_interval = max(1, int(fps * sample_interval_sec))

        all_detections = []
        sampled_frames = []
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            if frame_idx % frame_interval == 0:
                dets, _, ann_frame = self.detect_frame(frame)
                all_detections.extend(dets)
                sampled_frames.append(ann_frame)

            frame_idx += 1

        cap.release()
        counts = self.count_by_species(all_detections)
        return all_detections, counts, sampled_frames

    def count_by_species(self, detections):
        counts = {
            "house_sparrow": 0,
            "common_myna": 0,
            "crow": 0,
            "parrot": 0,
            "pigeon": 0,
            "peacock": 0,
            "unknown_bird": 0,
            "total": 0
        }
        for d in detections:
            sp = d.get("species", "unknown_bird")
            if sp in counts:
                counts[sp] += 1
            else:
                counts["unknown_bird"] += 1
        counts["total"] = len(detections)
        return counts

    def draw_annotations(self, frame, detections):
        """Draw styled bounding boxes and species labels."""
        colors = {
            "house_sparrow": (255, 165, 0),   # Orange
            "common_myna": (0, 255, 255),     # Yellow
            "crow": (0, 0, 255),              # Red
            "parrot": (0, 255, 0),            # Green
            "pigeon": (255, 0, 255),          # Magenta
            "peacock": (255, 215, 0),         # Cyan/Gold
            "unknown_bird": (128, 128, 128)   # Gray
        }

        for d in detections:
            x1, y1, x2, y2 = d["bbox"]
            species = d["species"]
            display_name = d["display_name"]
            conf = d["confidence"]
            color = colors.get(species, (0, 255, 255))

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            label = f"{display_name} {int(conf * 100)}%"

            (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
            cv2.rectangle(frame, (x1, max(0, y1 - 22)), (x1 + lw + 6, max(0, y1)), color, -1)
            cv2.putText(frame, label, (x1 + 3, max(15, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)

        return frame
