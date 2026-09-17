import time
import sys
import argparse
from src.core.logger import logger
from src.vision.detector import BirdDetector
from src.audio.recognizer import AudioRecognizer
from src.fusion.fusion_engine import FusionEngine
from src.navigation.navigation import navigation_engine
from src.dashboard.app import start_flask_app

def main():
    parser = argparse.ArgumentParser(description="ScareX Real-Time Bird Detection System for Raspberry Pi 5")
    parser.add_argument('--test', action='store_true', help="Run the system in test mode")
    args = parser.parse_args()

    print("=" * 40)
    print("ScareX System Starting...")
    print("=" * 40)
    
    try:
        # Initialize Core Modules
        vision_module = BirdDetector()
        audio_module = AudioRecognizer()  # Retained for structure, but audio not used for deterrence
        
        # Initialize Decision Engine (combines Vision + Audio, controls Alarms)
        fusion_engine = FusionEngine(vision_module, audio_module)
        
        print(f"Model: {vision_module.model_path}")
        print(f"Camera: USB Camera (Index {vision_module.config.get('camera_index', 0)})")
        print(f"Audio: USB Speaker (Path: {vision_module.config.get('audio_path', 'assets/audio/hawk_eagle.mp3')})")
        print("Deterrence: OFF")
        print("System Ready")
        print("=" * 40)
        
        if args.test:
            logger.info("Running in TEST MODE. Validating components...")
            # We just let it run normally for test mode right now.
        
        # Start Dashboard in a background thread
        start_flask_app(fusion_engine, vision_module, audio_module)
        
        # Start AI modules
        vision_module.start()
        audio_module.start()
        
        # Start Engines
        fusion_engine.start()
        navigation_engine.start()
        
        logger.info("All systems started. Press Ctrl+C to stop.")
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n" + "=" * 40)
        print("Shutting down ScareX...")
        print("=" * 40)
    except Exception as e:
        logger.error(f"Critical error: {e}")
    finally:
        try:
            navigation_engine.stop()
            fusion_engine.stop()
            vision_module.stop()
            audio_module.stop()
        except:
            pass
        logger.info("Shutdown complete.")
        sys.exit(0)

if __name__ == "__main__":
    main()
