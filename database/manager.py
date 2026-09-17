import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime

try:
    from ScareX.config import config
except ImportError:
    from config import config

logger = logging.getLogger("ScareX.Database")

class ScareXDatabaseManager:
    """
    SQLite database manager for Module A (Bird Deterrence) & Module B (Tomato Crop Monitoring).
    Manages detection histories, tomato maturity logs, 6 crop condition states, and row priorities.
    """
    def __init__(self, db_path=None):
        self.db_path = Path(db_path or config.db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()

    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Module A — Bird Detection History
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detection_history (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    species TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    source TEXT NOT NULL,
                    module TEXT DEFAULT 'bird',
                    model_type TEXT DEFAULT 'ncnn',
                    prediction_mode TEXT NOT NULL,
                    media_path TEXT,
                    bird_confirmed INTEGER DEFAULT 0,
                    deterrence_triggered INTEGER DEFAULT 0,
                    motor_state INTEGER DEFAULT 0,
                    speaker_state INTEGER DEFAULT 0,
                    mock_mode INTEGER DEFAULT 0,
                    manual_test_mode INTEGER DEFAULT 0,
                    emergency_stop INTEGER DEFAULT 0,
                    reason TEXT
                )
            """)

            # Ensure columns exist on legacy databases
            try:
                cursor.execute("ALTER TABLE detection_history ADD COLUMN module TEXT DEFAULT 'bird'")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE detection_history ADD COLUMN model_type TEXT DEFAULT 'ncnn'")
            except sqlite3.OperationalError:
                pass

            # Module B — Tomato Detections
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tomato_detections (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    source TEXT NOT NULL,
                    module TEXT DEFAULT 'tomato',
                    image_path TEXT,
                    video_path TEXT,
                    class_name TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    bounding_box TEXT,
                    row_id INTEGER DEFAULT 1
                )
            """)

            # Module B — Crop Condition State Logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crop_state_logs (
                    state_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    crop_state TEXT NOT NULL,
                    total_tomatoes INTEGER DEFAULT 0,
                    fully_ripened_count INTEGER DEFAULT 0,
                    half_ripened_count INTEGER DEFAULT 0,
                    green_count INTEGER DEFAULT 0,
                    fully_ripened_percentage REAL DEFAULT 0.0,
                    half_ripened_percentage REAL DEFAULT 0.0,
                    green_percentage REAL DEFAULT 0.0,
                    average_confidence REAL DEFAULT 0.0,
                    overall_priority TEXT DEFAULT 'Low',
                    reason TEXT
                )
            """)

            # Module B — Row Statistics Logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS row_statistics_logs (
                    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    row_id INTEGER NOT NULL,
                    tomato_count INTEGER DEFAULT 0,
                    fully_ripened_count INTEGER DEFAULT 0,
                    half_ripened_count INTEGER DEFAULT 0,
                    green_count INTEGER DEFAULT 0,
                    average_confidence REAL DEFAULT 0.0,
                    priority TEXT NOT NULL,
                    priority_reason TEXT
                )
            """)

            # Manual Test Diagnostic Logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS manual_test_logs (
                    test_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    input_type TEXT NOT NULL,
                    expected_result TEXT NOT NULL,
                    actual_result TEXT NOT NULL,
                    deterrence_state TEXT NOT NULL,
                    motor_state TEXT NOT NULL,
                    audio_state TEXT NOT NULL,
                    status TEXT NOT NULL
                )
            """)

            conn.commit()
            logger.info("[Database] Integrated SQLite database schema initialized.")

    def log_event(self, species, display_name, confidence, source, prediction_mode,
                  media_path=None, bird_confirmed=False, deterrence_triggered=False,
                  motor_state=False, speaker_state=False, mock_mode=False,
                  manual_test_mode=False, emergency_stop=False, reason="", model_type="ncnn", module="bird"):
        """Log a Module A (Bird) event."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO detection_history (
                    timestamp, species, display_name, confidence, source, module, model_type,
                    prediction_mode, media_path, bird_confirmed, deterrence_triggered,
                    motor_state, speaker_state, mock_mode, manual_test_mode, emergency_stop, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                now_str, species, display_name, confidence, source, module, model_type,
                prediction_mode, media_path or "", 1 if bird_confirmed else 0,
                1 if deterrence_triggered else 0, 1 if motor_state else 0,
                1 if speaker_state else 0, 1 if mock_mode else 0,
                1 if manual_test_mode else 0, 1 if emergency_stop else 0, reason
            ))
            conn.commit()
            return cursor.lastrowid

    def log_tomato_event(self, source, class_name, display_name, confidence, bbox, row_id=1, image_path="", video_path=""):
        """Log a Module B (Tomato) detection."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tomato_detections (
                    timestamp, source, module, image_path, video_path,
                    class_name, display_name, confidence, bounding_box, row_id
                ) VALUES (?, ?, 'tomato', ?, ?, ?, ?, ?, ?, ?)
            """, (
                now_str, source, image_path, video_path,
                class_name, display_name, confidence, json.dumps(bbox), row_id
            ))
            conn.commit()
            return cursor.lastrowid

    def log_crop_state(self, state_info, metrics, overall_priority="Low"):
        """Log a Module B Crop Condition State snapshot."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO crop_state_logs (
                    timestamp, crop_state, total_tomatoes, fully_ripened_count,
                    half_ripened_count, green_count, fully_ripened_percentage,
                    half_ripened_percentage, green_percentage, average_confidence,
                    overall_priority, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                now_str, state_info.get("crop_state"), metrics.get("total_tomatoes", 0),
                metrics.get("fully_ripened_count", 0), metrics.get("half_ripened_count", 0),
                metrics.get("green_count", 0), metrics.get("fully_ripened_pct", 0.0),
                metrics.get("half_ripened_pct", 0.0), metrics.get("green_pct", 0.0),
                metrics.get("average_confidence", 0.0), overall_priority, state_info.get("reason", "")
            ))
            conn.commit()
            return cursor.lastrowid

    def log_row_stats(self, rows_stats):
        """Log Module B row-wise priority statistics."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for r in rows_stats:
                cursor.execute("""
                    INSERT INTO row_statistics_logs (
                        timestamp, row_id, tomato_count, fully_ripened_count,
                        half_ripened_count, green_count, average_confidence,
                        priority, priority_reason
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    now_str, r.get("row_id"), r.get("tomato_count", 0),
                    r.get("fully_ripened_count", 0), r.get("half_ripened_count", 0),
                    r.get("green_count", 0), r.get("average_confidence", 0.0),
                    r.get("priority"), r.get("reason")
                ))
            conn.commit()

    def log_manual_test(self, input_type, expected_result, actual_result, deterrence_state="OFF", motor_state="OFF", audio_state="OFF", status="PASS"):
        """Log a manual test execution result."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO manual_test_logs (
                    timestamp, input_type, expected_result, actual_result,
                    deterrence_state, motor_state, audio_state, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (now_str, input_type, expected_result, actual_result, deterrence_state, motor_state, audio_state, status))
            conn.commit()
            return cursor.lastrowid

    def get_recent_history(self, limit=50):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM detection_history ORDER BY event_id DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def get_recent_tomatoes(self, limit=50):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tomato_detections ORDER BY event_id DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def get_recent_crop_states(self, limit=10):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM crop_state_logs ORDER BY state_id DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def get_summary_stats(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Bird Detections
            cursor.execute("SELECT COUNT(*) as count FROM detection_history WHERE bird_confirmed=1")
            total_birds = cursor.fetchone()["count"]

            # Deterrence Triggers
            cursor.execute("SELECT COUNT(*) as count FROM detection_history WHERE deterrence_triggered=1")
            total_deterrence = cursor.fetchone()["count"]

            # Motorcycle Rejections
            cursor.execute("SELECT COUNT(*) as count FROM detection_history WHERE species='motorcycle_engine'")
            motorcycle_rejections = cursor.fetchone()["count"]

            # Bird Species Breakdown
            cursor.execute("""
                SELECT species, display_name, COUNT(*) as count 
                FROM detection_history 
                WHERE bird_confirmed=1 
                GROUP BY species
            """)
            species_breakdown = {r["display_name"]: r["count"] for r in cursor.fetchall()}

            # Tomato Detections Count
            cursor.execute("SELECT COUNT(*) as count FROM tomato_detections")
            total_tomatoes = cursor.fetchone()["count"]

            return {
                "total_birds_confirmed": total_birds,
                "total_deterrence_triggers": total_deterrence,
                "motorcycle_rejections": motorcycle_rejections,
                "species_breakdown": species_breakdown,
                "total_tomatoes_logged": total_tomatoes
            }
