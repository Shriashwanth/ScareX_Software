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
    SQLite database manager for logging detection events, decision engine logs,
    prediction modes (Real Inference vs Demo / Synthetic), and deterrence histories.
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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detection_history (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    species TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    source TEXT NOT NULL,
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
            logger.info("[Database] Database schema initialized.")

    def log_event(self, species, display_name, confidence, source, prediction_mode,
                  media_path=None, bird_confirmed=False, deterrence_triggered=False,
                  motor_state=False, speaker_state=False, mock_mode=False,
                  manual_test_mode=False, emergency_stop=False, reason="", model_type="ncnn"):
        """Log a detection or decision event into SQLite database."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO detection_history (
                    timestamp, species, display_name, confidence, source, model_type,
                    prediction_mode, media_path, bird_confirmed, deterrence_triggered,
                    motor_state, speaker_state, mock_mode, manual_test_mode, emergency_stop, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                now_str, species, display_name, confidence, source, model_type,
                prediction_mode, media_path or "", 1 if bird_confirmed else 0,
                1 if deterrence_triggered else 0, 1 if motor_state else 0,
                1 if speaker_state else 0, 1 if mock_mode else 0,
                1 if manual_test_mode else 0, 1 if emergency_stop else 0, reason
            ))
            conn.commit()
            return cursor.lastrowid

    def log_manual_test(self, input_type, expected, actual, deterrence_st, motor_st, audio_st, status):
        """Log a manual test execution result."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO manual_test_logs (
                    timestamp, input_type, expected_result, actual_result,
                    deterrence_state, motor_state, audio_state, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (now_str, input_type, expected, actual, deterrence_st, motor_st, audio_st, status))
            conn.commit()
            return cursor.lastrowid

    def get_recent_history(self, limit=50):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM detection_history ORDER BY event_id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_manual_test_logs(self, limit=50):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM manual_test_logs ORDER BY test_id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_summary_stats(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total Detections
            cursor.execute("SELECT COUNT(*) as count FROM detection_history WHERE bird_confirmed=1")
            total_birds = cursor.fetchone()["count"]

            # Deterrence Triggers
            cursor.execute("SELECT COUNT(*) as count FROM detection_history WHERE deterrence_triggered=1")
            total_deterrence = cursor.fetchone()["count"]

            # Motorcycle Rejections
            cursor.execute("SELECT COUNT(*) as count FROM detection_history WHERE species='motorcycle_engine'")
            motorcycle_rejections = cursor.fetchone()["count"]

            # Species Breakdown
            cursor.execute("""
                SELECT species, display_name, COUNT(*) as count 
                FROM detection_history 
                WHERE bird_confirmed=1 
                GROUP BY species
            """)
            species_rows = cursor.fetchall()
            species_breakdown = {r["display_name"]: r["count"] for r in species_rows}

            return {
                "total_birds_confirmed": total_birds,
                "total_deterrence_triggers": total_deterrence,
                "motorcycle_rejections": motorcycle_rejections,
                "species_breakdown": species_breakdown
            }
