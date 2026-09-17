#!/usr/bin/env python3
"""
ScareX NCNN Export Utility Script.
Converts PyTorch model weights to NCNN optimized format for Raspberry Pi 5.
"""
import os
import sys

def export_to_ncnn(model_path=None):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = model_path or os.path.join(base_dir, "..", "models", "bird_species_model.pt")

    print("============================================================")
    print("      ScareX NCNN Model Export for Raspberry Pi 5           ")
    print("============================================================")

    if not os.path.exists(model_path):
        print(f"[ExportNCNN] Model weights not found at {model_path}. Exiting.")
        return False

    try:
        from ultralytics import YOLO
        model = YOLO(model_path)
        out_dir = model.export(format="ncnn", imgsz=640)
        print(f"[ExportNCNN] Successfully exported model to NCNN format: {out_dir}")
        return True
    except Exception as e:
        print(f"[ExportNCNN] Export failed: {e}")
        return False

if __name__ == "__main__":
    export_to_ncnn()
