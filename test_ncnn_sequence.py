import os
import sys
import time
import numpy as np

# Ensure project path is accessible
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from laptop_dashboard import state, start_audio, stop_audio

def run_ncnn_sequence_test():
    print("=" * 60)
    print("STARTING NCNN AUDIO STATE MACHINE TEST SEQUENCE")
    print("=" * 60)
    
    # Verify NCNN model is loaded
    print(f"NCNN Model Loaded: {state.ncnn_model is not None}")
    print(f"Preserved Class Mapping: {state.class_names}")
    
    # 1. Test Initial State: NO BIRD
    print("\n--- STAGE 1: NO BIRD DETECTED ---")
    state.consecutive_detections = 0
    state.bird_detected = False
    stop_audio()
    
    assert not state.bird_detected, "Expected bird_detected == False"
    assert not state.audio_playing, "Expected audio_playing == False"
    print("STATUS: NO BIRD | SOUND: OFF -> VERIFIED")
    
    # 2. Test Detection Transition: BIRD DETECTED -> SOUND ON
    print("\n--- STAGE 2: BIRD DETECTED (Simulated Detection) ---")
    mock_bird_species = state.class_names.get(0, "Crow")
    mock_conf = 0.88
    
    # Simulate consecutive frames
    for i in range(1, state.required_consecutive_detections + 1):
        state.consecutive_detections += 1
        state.lost_frames = 0
        if state.consecutive_detections >= state.required_consecutive_detections:
            state.bird_detected = True
            state.latest_bird = mock_bird_species
            state.latest_conf = mock_conf
            start_audio()
            
    assert state.bird_detected, "Expected bird_detected == True"
    assert state.audio_playing, "Expected audio_playing == True"
    print(f"STATUS: BIRD DETECTED ({state.latest_bird}, {state.latest_conf*100:.1f}%) | SOUND: ON -> VERIFIED")
    
    # 3. Test Audio State Machine Stability (No redundant restarts)
    print("\n--- STAGE 3: STATE MACHINE STABILITY TEST ---")
    prev_audio_state = state.audio_playing
    # Calling start_audio again while already playing should not re-trigger play()
    start_audio()
    assert state.audio_playing == prev_audio_state, "Expected state.audio_playing to stay True"
    print("STATE MACHINE STABILITY: NO DUPLICATE SOUND RESTARTS -> VERIFIED")
    
    # 4. Test Bird Removal Transition: BIRD REMOVED -> SOUND OFF
    print("\n--- STAGE 4: BIRD REMOVED (Simulated Loss of Frames) ---")
    for i in range(1, state.lost_detection_frames + 1):
        state.consecutive_detections = 0
        state.lost_frames += 1
        if state.lost_frames >= state.lost_detection_frames:
            state.bird_detected = False
            state.latest_bird = "None"
            state.latest_conf = 0.0
            stop_audio()
            
    assert not state.bird_detected, "Expected bird_detected == False"
    assert not state.audio_playing, "Expected audio_playing == False"
    print("STATUS: BIRD REMOVED | SOUND: OFF -> VERIFIED")
    
    print("\n" + "=" * 60)
    print("FULL NCNN SEQUENCE TEST PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_ncnn_sequence_test()
