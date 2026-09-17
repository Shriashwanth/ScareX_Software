#!/usr/bin/env python3
"""
ScareX 6-Class Bird Species Vision Model Training Script.
Trains YOLO / NCNN model on datasets/bird_species/data.yaml.
"""
import os
import sys
from pathlib import Path

def train_vision_model(data_yaml=None, epochs=50, imgsz=640, batch=16):
    data_yaml = data_yaml or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datasets", "bird_species", "data.yaml")
    
    print("============================================================")
    print("      ScareX 6-Class Bird Species Vision Training           ")
    print("============================================================")
    print(f"Data config: {data_yaml}")
    print(f"Epochs: {epochs}, Image Size: {imgsz}, Batch Size: {batch}")

    try:
        from ultralytics import YOLO
        model = YOLO("yolov8n.pt")
        results = model.train(
            data=data_yaml,
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            name="scarex_6class_bird_model"
        )
        print("[TrainVision] Training completed successfully.")
        return results
    except Exception as e:
        print(f"[TrainVision] Error during training: {e}")
        return None

if __name__ == "__main__":
    train_vision_model()
