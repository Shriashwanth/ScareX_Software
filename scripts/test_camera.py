#!/usr/bin/env python3
"""
ScareX USB Webcam Diagnostic Script.
Checks camera index opening, resolution capture, and frame reading.
"""
import cv2
import sys

def test_camera(cam_idx=0):
    print(f"Testing USB Webcam on index {cam_idx}...")
    cap = cv2.VideoCapture(cam_idx)

    if not cap.isOpened():
        print(f"FAILED: Could not open USB webcam at index {cam_idx}.")
        sys.exit(1)

    ret, frame = cap.read()
    if not ret or frame is None:
        print("FAILED: Opened camera but could not capture frame.")
        sys.exit(1)

    h, w = frame.shape[:2]
    print(f"SUCCESS: USB Webcam captured {w}x{h} frame successfully!")
    cap.release()

if __name__ == "__main__":
    test_camera(0)
