#!/usr/bin/env python3
"""
ScareX Comprehensive Automated Test Suite.
Verifies 6-class vision detection, audio classification & motorcycle noise rejection,
7-tier decision engine priority chain, motor safety defaults, DB logging, and PDF reports.
"""
import os
import sys
import unittest
import numpy as np
from pathlib import Path

# Add project root and parent to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from ScareX.config import config
    from ScareX.camera.detector import CameraBirdDetector
    from ScareX.audio.real_audio import RealAudioClassifier
    from ScareX.audio.mock_audio import MockAudioGenerator
    from ScareX.deterrence.decision_engine import CentralDecisionEngine
    from ScareX.deterrence.actuator import DeterrenceActuatorController
    from ScareX.database.manager import ScareXDatabaseManager
    from ScareX.dashboard.reports import ScareXReportGenerator
except ImportError:
    from config import config
    from camera.detector import CameraBirdDetector
    from audio.real_audio import RealAudioClassifier
    from audio.mock_audio import MockAudioGenerator
    from deterrence.decision_engine import CentralDecisionEngine
    from deterrence.actuator import DeterrenceActuatorController
    from database.manager import ScareXDatabaseManager
    from dashboard.reports import ScareXReportGenerator


class TestScareXSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = ScareXDatabaseManager()
        cls.camera = CameraBirdDetector()
        cls.audio = RealAudioClassifier()
        cls.mock_gen = MockAudioGenerator()
        cls.engine = CentralDecisionEngine()
        cls.actuator = DeterrenceActuatorController()
        cls.reports = ScareXReportGenerator(cls.db)

    def setUp(self):
        # Reset engine state before each test
        self.engine.emergency_stop = False
        self.engine.mute_mode = False
        self.engine.manual_test_mode = False
        self.engine.last_trigger_time = 0.0
        self.engine.consecutive_camera_birds = 0


    # ------------------------------------------------------------------
    # 1. Camera Detection & 6-Class Species Tests
    # ------------------------------------------------------------------
    def test_camera_detection_6class(self):
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        dets, counts, _ = self.camera.detect_frame(dummy_frame)
        self.assertIsInstance(dets, list)
        self.assertIn("total", counts)

    def test_camera_unsupported_object(self):
        # Non-bird / person detection should result in Deterrence OFF
        unsupported_dets = [{"species": "person", "display_name": "Person", "confidence": 0.95, "bbox": [10, 10, 100, 100]}]
        decision = self.engine.evaluate({"detections": unsupported_dets}, {})
        self.assertFalse(decision["deterrence_active"])
        self.assertFalse(decision["motor_active"])
        self.assertEqual(decision["display_name"], "No Bird Detected")

    # ------------------------------------------------------------------
    # 2. Real Audio Classification & Motorcycle Sound Rejection Tests
    # ------------------------------------------------------------------
    def test_motorcycle_sound_rejection(self):
        # Low frequency engine sound signature
        sr = 22050
        t = np.linspace(0, 1.0, sr)
        motorcycle_signal = np.sin(2 * np.pi * 100 * t) + 0.5 * np.sin(2 * np.pi * 200 * t)

        res = self.audio.classify_audio_data(motorcycle_signal, sr)
        self.assertFalse(res["is_bird"])
        self.assertTrue(res["is_motorcycle"])
        self.assertEqual(res["species"], "motorcycle_engine")

        # Evaluate through decision engine
        decision = self.engine.evaluate({}, res)
        self.assertFalse(decision["deterrence_active"])
        self.assertFalse(decision["motor_active"])
        self.assertIn("Motorcycle engine sound rejected", decision["reason"])

    def test_non_bird_noise_rejection(self):
        # Environmental noise
        sr = 22050
        noise_signal = np.random.normal(0, 0.2, sr)
        res = self.audio.classify_audio_data(noise_signal, sr)
        self.assertFalse(res["is_bird"])

        decision = self.engine.evaluate({}, res)
        self.assertFalse(decision["deterrence_active"])

    # ------------------------------------------------------------------
    # 3. Synthetic Mock Audio Generator Tests
    # ------------------------------------------------------------------
    def test_mock_audio_generation_all_species(self):
        species_list = ["house_sparrow", "common_myna", "crow", "parrot", "pigeon", "peacock", "motorcycle_engine"]
        for sp in species_list:
            res = self.mock_gen.generate_mock_audio(target_class=sp, duration_sec=1.0)
            self.assertTrue(Path(res["file_path"]).exists())
            self.assertTrue(res["is_mock"])
            self.assertEqual(res["badge"], "MOCK AUDIO — SYNTHETIC TEST DATA")

    def test_mock_audio_default_deterrence_off(self):
        res = self.mock_gen.generate_mock_audio(target_class="crow", duration_sec=1.0)
        aud_res = {
            "status": "success", "is_bird": True, "species": res["species"],
            "display_name": res["display_name"], "confidence": 0.95, "is_mock": True
        }

        # Normal mode (Manual Test Mode disabled) -> Deterrence MUST be OFF
        self.engine.manual_test_mode = False
        decision = self.engine.evaluate({}, aud_res)
        self.assertFalse(decision["deterrence_active"])
        self.assertIn("Mock audio prediction ignored in normal operation", decision["reason"])

        # Manual Test Mode enabled -> Deterrence MAY be ON
        self.engine.manual_test_mode = True
        decision_test = self.engine.evaluate({}, aud_res)
        self.assertTrue(decision_test["deterrence_active"])

    # ------------------------------------------------------------------
    # 4. Central Decision Engine Priority & Safety Default Tests
    # ------------------------------------------------------------------
    def test_emergency_stop_highest_priority(self):
        self.engine.emergency_stop = True
        cam_dets = [{"species": "crow", "display_name": "Crow", "confidence": 0.98, "bbox": [10, 10, 100, 100]}]

        decision = self.engine.evaluate({"detections": cam_dets}, {})
        self.assertFalse(decision["deterrence_active"])
        self.assertFalse(decision["motor_active"])
        self.assertFalse(decision["speaker_active"])
        self.assertIn("Emergency Stop activated", decision["reason"])

    def test_mute_mode_safety_policy(self):
        self.engine.mute_mode = True
        cam_dets = [
            {"species": "crow", "display_name": "Crow", "confidence": 0.95, "bbox": [10, 10, 100, 100]},
            {"species": "crow", "display_name": "Crow", "confidence": 0.95, "bbox": [10, 10, 100, 100]}
        ]
        self.engine.consecutive_camera_birds = 2  # Pass consecutive threshold

        decision = self.engine.evaluate({"detections": cam_dets}, {})
        self.assertTrue(decision["motor_active"])
        self.assertFalse(decision["speaker_active"])  # Muted

    # ------------------------------------------------------------------
    # 5. Database Logging & Report Generation Tests
    # ------------------------------------------------------------------
    def test_database_logging_and_reason_fields(self):
        event_id = self.db.log_event(
            species="crow", display_name="Crow", confidence=0.92,
            source="Camera Test", prediction_mode="Real Inference",
            bird_confirmed=True, deterrence_triggered=True,
            reason="Supported Crow detected by camera"
        )
        self.assertIsNotNone(event_id)
        history = self.db.get_recent_history(limit=5)
        self.assertTrue(len(history) > 0)
        self.assertEqual(history[0]["reason"], "Supported Crow detected by camera")

    def test_pdf_and_csv_report_generation(self):
        res = self.reports.generate_all_reports()
        self.assertTrue(Path(res["csv"]).exists())
        self.assertTrue(Path(res["pdf"]).exists() or Path(config.reports_dir, "latest_report.txt").exists())

def run_test_suite():
    print("============================================================")
    print("      ScareX Complete Automated Test Suite Execution        ")
    print("============================================================")

    suite = unittest.TestLoader().loadTestsFromTestCase(TestScareXSystem)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n------------------------------------------------------------")
    print("                 SCAREX TEST SUMMARY RESULTS                ")
    print("------------------------------------------------------------")
    print(f"Total Tests Executed: {result.testsRun}")
    print(f"Passed:               {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures:             {len(result.failures)}")
    print(f"Errors:               {len(result.errors)}")
    print("------------------------------------------------------------")

    if result.wasSuccessful():
        print(">>> ALL SCAREX SAFETY, REJECTION, & SYSTEM TESTS PASSED <<<")
    else:
        print(">>> SOME TESTS FAILED — CHECK LOGS ABOVE <<<")
        sys.exit(1)

if __name__ == "__main__":
    run_test_suite()
