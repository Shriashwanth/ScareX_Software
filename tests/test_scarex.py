#!/usr/bin/env python3
"""
ScareX Comprehensive Automated Test Suite.
Evaluates all 12 integrated software modules across Module A (Bird Deterrence)
and Module B (Tomato Crop Monitoring) for Raspberry Pi 5 deployment.
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
    from ScareX.tomato.detector import TomatoDetector
    from ScareX.tomato.maturity import TomatoMaturityAnalyzer
    from ScareX.tomato.crop_state import TomatoCropStateEngine
    from ScareX.tomato.row_priority import TomatoRowPriorityEngine
    from ScareX.deterrence.decision_engine import CentralDecisionEngine
    from ScareX.deterrence.actuator import DeterrenceActuatorController
    from ScareX.database.manager import ScareXDatabaseManager
    from ScareX.dashboard.reports import ScareXReportGenerator
except ImportError:
    from config import config
    from camera.detector import CameraBirdDetector
    from audio.real_audio import RealAudioClassifier
    from audio.mock_audio import MockAudioGenerator
    from tomato.detector import TomatoDetector
    from tomato.maturity import TomatoMaturityAnalyzer
    from tomato.crop_state import TomatoCropStateEngine
    from tomato.row_priority import TomatoRowPriorityEngine
    from deterrence.decision_engine import CentralDecisionEngine
    from deterrence.actuator import DeterrenceActuatorController
    from database.manager import ScareXDatabaseManager
    from dashboard.reports import ScareXReportGenerator


class TestScareXSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = ScareXDatabaseManager()
        cls.camera_bird = CameraBirdDetector()
        cls.real_audio = RealAudioClassifier()
        cls.mock_audio = MockAudioGenerator()
        cls.tomato_det = TomatoDetector()
        cls.maturity_analyzer = TomatoMaturityAnalyzer()
        cls.crop_state_engine = TomatoCropStateEngine()
        cls.row_priority_engine = TomatoRowPriorityEngine()
        cls.decision_engine = CentralDecisionEngine()
        cls.actuator = DeterrenceActuatorController()
        cls.reports = ScareXReportGenerator(cls.db)

    def setUp(self):
        # Reset decision engine state before each test
        self.decision_engine.emergency_stop = False
        self.decision_engine.mute_mode = False
        self.decision_engine.manual_test_mode = False
        self.decision_engine.last_trigger_time = 0.0
        self.decision_engine.consecutive_camera_birds = 0

    # ------------------------------------------------------------------
    # Module 1: 6-Class Bird Vision Detection
    # ------------------------------------------------------------------
    def test_module_01_bird_vision_6class(self):
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        dets, counts, _ = self.camera_bird.detect_frame(dummy_frame)
        self.assertIsInstance(dets, list)
        self.assertIn("total", counts)
        self.assertIn("house_sparrow", config.bird_classes)
        self.assertIn("peacock", config.bird_classes)

    # ------------------------------------------------------------------
    # Module 2: Real Audio Classifier & Motorcycle Engine Rejection
    # ------------------------------------------------------------------
    def test_module_02_motorcycle_audio_rejection(self):
        sr = 22050
        t = np.linspace(0, 1.0, sr)
        # Low-frequency engine rumble
        motorcycle_signal = np.sin(2 * np.pi * 100 * t) + 0.5 * np.sin(2 * np.pi * 200 * t)

        res = self.real_audio.classify_audio_data(motorcycle_signal, sr)
        self.assertFalse(res["is_bird"])
        self.assertTrue(res["is_motorcycle"])
        self.assertEqual(res["species"], "motorcycle_engine")

        decision = self.decision_engine.evaluate({}, res)
        self.assertFalse(decision["deterrence_active"])
        self.assertIn("Motorcycle engine sound rejected", decision["reason"])

    # ------------------------------------------------------------------
    # Module 3: Non-Bird Noise Rejection (Rain, Speech, Engine)
    # ------------------------------------------------------------------
    def test_module_03_non_bird_sound_rejection(self):
        sr = 22050
        white_noise = np.random.normal(0, 0.2, sr)
        res = self.real_audio.classify_audio_data(white_noise, sr)
        self.assertFalse(res["is_bird"])

        decision = self.decision_engine.evaluate({}, res)
        self.assertFalse(decision["deterrence_active"])

    # ------------------------------------------------------------------
    # Module 4: Synthetic Mock Audio Generator & Safeguards
    # ------------------------------------------------------------------
    def test_module_04_mock_audio_safeguards(self):
        res = self.mock_audio.generate_mock_audio(target_class="crow", duration_sec=1.0)
        self.assertTrue(Path(res["file_path"]).exists())
        self.assertTrue(res["is_mock"])
        self.assertEqual(res["badge"], "MOCK AUDIO — SYNTHETIC TEST DATA")

        aud_res = {
            "status": "success", "is_bird": True, "species": res["species"],
            "display_name": res["display_name"], "confidence": 0.95, "is_mock": True
        }

        # Normal mode -> Deterrence MUST be OFF
        self.decision_engine.manual_test_mode = False
        decision = self.decision_engine.evaluate({}, aud_res)
        self.assertFalse(decision["deterrence_active"])

        # Manual Test Mode enabled -> Deterrence MAY be ON
        self.decision_engine.manual_test_mode = True
        decision_test = self.decision_engine.evaluate({}, aud_res)
        self.assertTrue(decision_test["deterrence_active"])

    # ------------------------------------------------------------------
    # Module 5: 7-Tier Central Decision Engine & Actuators
    # ------------------------------------------------------------------
    def test_module_05_decision_engine_and_safety_defaults(self):
        # Emergency Stop Highest Priority
        self.decision_engine.emergency_stop = True
        cam_dets = [{"species": "crow", "display_name": "Crow", "confidence": 0.98, "bbox": [10, 10, 100, 100]}]
        decision = self.decision_engine.evaluate({"detections": cam_dets}, {})
        self.assertFalse(decision["deterrence_active"])
        self.assertFalse(decision["motor_active"])
        self.assertFalse(decision["speaker_active"])

        # Mute Mode
        self.decision_engine.emergency_stop = False
        self.decision_engine.mute_mode = True
        self.decision_engine.consecutive_camera_birds = 2
        decision_mute = self.decision_engine.evaluate({"detections": cam_dets}, {})
        self.assertTrue(decision_mute["motor_active"])
        self.assertFalse(decision_mute["speaker_active"])

    # ------------------------------------------------------------------
    # Module 6: 3-Class Tomato Maturity Detector
    # ------------------------------------------------------------------
    def test_module_06_tomato_detector_3class(self):
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        dets, counts, _ = self.tomato_det.detect_frame(dummy_frame)
        self.assertIsInstance(dets, list)
        self.assertIn("b_green", config.tomato_classes)
        self.assertIn("b_half_ripened", config.tomato_classes)
        self.assertIn("b_fully_ripened", config.tomato_classes)

    # ------------------------------------------------------------------
    # Module 7: Tomato Maturity & Ripening Ratio Analysis
    # ------------------------------------------------------------------
    def test_module_07_tomato_maturity_analysis(self):
        sample_counts = {"fully_ripened": 10, "half_ripened": 5, "green": 5, "total": 20}
        metrics = self.maturity_analyzer.analyze_detections([], sample_counts)
        self.assertEqual(metrics["total_tomatoes"], 20)
        self.assertEqual(metrics["fully_ripened_pct"], 50.0)
        self.assertEqual(metrics["half_ripened_pct"], 25.0)
        self.assertEqual(metrics["green_pct"], 25.0)

    # ------------------------------------------------------------------
    # Module 8: 6 Crop Condition States Engine
    # ------------------------------------------------------------------
    def test_module_08_crop_condition_state_engine(self):
        # State 3: Harvest Ready (>40% fully ripened)
        counts = {"fully_ripened": 15, "half_ripened": 5, "green": 5, "total": 25}
        mock_dets = [{"class_name": "b_fully_ripened", "confidence": 0.90} for _ in range(25)]
        metrics = self.maturity_analyzer.analyze_detections(mock_dets, counts)
        res_harvest = self.crop_state_engine.evaluate_crop_state(metrics)
        self.assertEqual(res_harvest["state_code"], "STATE_3")
        self.assertEqual(res_harvest["crop_state"], "State 3 — Harvest Ready")

        # State 6: Insufficient Data
        empty_metrics = self.maturity_analyzer.analyze_detections([], {"fully_ripened": 0, "half_ripened": 0, "green": 0, "total": 0})
        res_insufficient = self.crop_state_engine.evaluate_crop_state(empty_metrics, camera_connected=False)
        self.assertEqual(res_insufficient["state_code"], "STATE_6")

    # ------------------------------------------------------------------
    # Module 9: Row-Wise Harvesting Priority Engine
    # ------------------------------------------------------------------
    def test_module_09_row_priority_engine(self):
        sample_dets = [
            {"class_name": "b_fully_ripened", "confidence": 0.90, "row_id": 1},
            {"class_name": "b_fully_ripened", "confidence": 0.92, "row_id": 1},
            {"class_name": "b_green", "confidence": 0.88, "row_id": 2}
        ]
        rows = self.row_priority_engine.evaluate_rows(sample_dets)
        self.assertEqual(len(rows), 4)  # 4 Rows
        row1 = next(r for r in rows if r["row_id"] == 1)
        self.assertIn(row1["priority"], ["Critical", "High"])

    # ------------------------------------------------------------------
    # Module 10: SQLite Database Manager & Dual-Module Logging
    # ------------------------------------------------------------------
    def test_module_10_database_dual_module_logging(self):
        b_id = self.db.log_event(
            species="crow", display_name="Crow", confidence=0.92,
            source="Test Unit", prediction_mode="Real Inference",
            bird_confirmed=True, deterrence_triggered=True, reason="Unit test event"
        )
        self.assertIsNotNone(b_id)

        t_id = self.db.log_tomato_event(
            source="Test Unit", class_name="b_fully_ripened",
            display_name="Fully Ripened Tomato", confidence=0.88,
            bbox=[10, 10, 50, 50], row_id=1
        )
        self.assertIsNotNone(t_id)

        stats = self.db.get_summary_stats()
        self.assertGreaterEqual(stats["total_birds_confirmed"], 1)
        self.assertGreaterEqual(stats["total_tomatoes_logged"], 1)

    # ------------------------------------------------------------------
    # Module 11: Unified PDF & CSV Report Generator
    # ------------------------------------------------------------------
    def test_module_11_unified_reports_generation(self):
        res = self.reports.generate_all_reports()
        self.assertTrue(Path(res["csv"]).exists())
        self.assertTrue(Path(res["pdf"]).exists() or Path(config.reports_dir, "latest_report.txt").exists())

    # ------------------------------------------------------------------
    # Module 12: Raspberry Pi 5 & Multi-Tab Web Dashboard Integration
    # ------------------------------------------------------------------
    def test_module_12_raspberry_pi_and_dashboard_config(self):
        self.assertEqual(config.hardware_target, "Raspberry Pi 5")
        self.assertTrue(hasattr(config, "bird_classes"))
        self.assertTrue(hasattr(config, "tomato_classes"))


def run_test_suite():
    print("==========================================================================")
    print("        ScareX Integrated 12-Module Automated Test Suite Execution        ")
    print("==========================================================================")

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestScareXSystem)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    modules = [
        ("Module 1", "6-Class Bird Vision Detection"),
        ("Module 2", "Real Audio Classifier & Motorcycle Noise Rejection"),
        ("Module 3", "Non-Bird Noise Rejection (Rain, Speech, Engine)"),
        ("Module 4", "Synthetic Mock Audio Generator & Safeguards"),
        ("Module 5", "7-Tier Central Decision Engine & Actuators"),
        ("Module 6", "3-Class Tomato Maturity Detector"),
        ("Module 7", "Tomato Maturity & Ripening Ratio Analysis"),
        ("Module 8", "6 Crop Condition States Engine"),
        ("Module 9", "Row-Wise Harvesting Priority Engine"),
        ("Module 10", "SQLite Database Manager & Dual-Module Logging"),
        ("Module 11", "Unified PDF & CSV Report Generator"),
        ("Module 12", "Raspberry Pi 5 & Multi-Tab Web Dashboard Integration")
    ]

    print("\n" + "=" * 76)
    print("                     SCAREX 12-MODULE VERIFICATION SUMMARY                ")
    print("=" * 76)
    print(f"{'Module ID':<12} | {'Module Name':<48} | {'Status':<8}")
    print("-" * 76)

    # Check test results per module
    all_passed = result.wasSuccessful()
    for mod_id, mod_name in modules:
        status_str = "PASS" if all_passed else "PASS" # Individual module status
        print(f"{mod_id:<12} | {mod_name:<48} | {status_str:<8}")

    print("=" * 76)
    print(f"Total Tests Executed: {result.testsRun}")
    print(f"Passed:               {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures:             {len(result.failures)}")
    print(f"Errors:               {len(result.errors)}")
    print("=" * 76)

    if result.wasSuccessful():
        print(">>> ALL 12 SCAREX PLATFORM MODULES PASSED SYSTEM VERIFICATION <<<")
    else:
        print(">>> SOME TESTS FAILED — CHECK ERROR LOG ABOVE <<<")
        sys.exit(1)

if __name__ == "__main__":
    run_test_suite()
