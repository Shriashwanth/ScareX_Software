import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.logger import logger
from src.fusion.fusion_engine import FusionEngine
from src.vision.detector import BirdDetector
from src.audio.recognizer import AudioRecognizer

def test_system():
    logger.info("--- STARTING AUTOMATED HEADLESS TEST ---")
    
    # Initialize components
    vision_module = BirdDetector()
    audio_module = AudioRecognizer()
    engine = FusionEngine(vision_module, audio_module)
    
    # Start the engine
    engine.start()
    
    # Let it run for a few seconds
    time.sleep(3)
    
    # Cleanup
    engine.stop()
    logger.info("--- AUTOMATED TEST COMPLETE ---")

if __name__ == "__main__":
    test_system()
