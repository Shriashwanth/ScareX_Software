import os
import csv
import json
import logging
from pathlib import Path
from datetime import datetime

try:
    from ScareX.config import config
except ImportError:
    from config import config

logger = logging.getLogger("ScareX.Reports")

class ScareXReportGenerator:
    """
    Generates PDF and CSV reports for ScareX 6-class bird detection,
    sound rejection stats (motorcycle/vehicle noise filtering), manual test results, and deterrence history.
    """
    def __init__(self, db_manager):
        self.db = db_manager
        self.reports_dir = Path(config.reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_all_reports(self):
        stats = self.db.get_summary_stats()
        history = self.db.get_recent_history(limit=50)
        test_logs = self.db.get_manual_test_logs(limit=50)
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

        csv_path = self.generate_csv(stats, history, test_logs, timestamp_str)
        pdf_path = self.generate_pdf(stats, history, test_logs, timestamp_str)

        return {
            "timestamp": timestamp_str,
            "csv": str(csv_path),
            "pdf": str(pdf_path),
            "stats": stats
        }

    def generate_csv(self, stats, history, test_logs, timestamp_str):
        latest_file = self.reports_dir / "latest_report.csv"
        dated_file = self.reports_dir / f"scarex_report_{timestamp_str}.csv"

        rows = [
            ["ScareX System Telemetry & Sound Rejection Summary"],
            ["Generated At", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["Confirmed Bird Detections", stats.get("total_birds_confirmed", 0)],
            ["Total Deterrence Triggers", stats.get("total_deterrence_triggers", 0)],
            ["Motorcycle Engine Sound Rejections", stats.get("motorcycle_rejections", 0)],
            [],
            ["Species Breakdown"],
            ["Species Name", "Confirmed Count"]
        ]

        for sp, count in stats.get("species_breakdown", {}).items():
            rows.append([sp, count])

        rows.extend([
            [],
            ["Recent Detection & Decision Logs"],
            ["Event ID", "Timestamp", "Species", "Source", "Confidence", "Deterrence", "Motor", "Reason"]
        ])

        for h in history:
            rows.append([
                h.get("event_id"), h.get("timestamp"), h.get("display_name"),
                h.get("source"), f"{int(h.get('confidence',0)*100)}%",
                "ON" if h.get("deterrence_triggered") else "OFF",
                "ON" if h.get("motor_state") else "OFF",
                h.get("reason")
            ])

        for p in [latest_file, dated_file]:
            with open(p, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

        logger.info(f"[Reports] Generated CSV report: {latest_file}")
        return latest_file

    def generate_pdf(self, stats, history, test_logs, timestamp_str):
        latest_file = self.reports_dir / "latest_report.pdf"
        dated_file = self.reports_dir / f"scarex_report_{timestamp_str}.pdf"

        try:
            from fpdf import FPDF

            class ScareXPDF(FPDF):
                def header(self):
                    self.set_font("Arial", "B", 15)
                    self.set_text_color(255, 94, 54)
                    self.cell(0, 10, "ScareX Autonomous Bird Deterrence & Sound Filtering Report", 0, 1, "C")
                    self.set_font("Arial", "I", 9)
                    self.set_text_color(100, 100, 100)
                    self.cell(0, 5, "Raspberry Pi 5 6-Class Bird Recognition & Sound Rejection System", 0, 1, "C")
                    self.ln(5)

                def footer(self):
                    self.set_y(-15)
                    self.set_font("Arial", "I", 8)
                    self.cell(0, 10, f"ScareX System Report | Page {self.page_no()}", 0, 0, "C")

            pdf = ScareXPDF()
            pdf.add_page()
            pdf.set_font("Arial", "", 10)

            # Executive Summary
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 7, "1. Executive Telemetry & Sound Filtering Summary", 0, 1, "L")
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 6, f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1)
            pdf.cell(0, 6, f"Total Confirmed Bird Intrusions: {stats.get('total_birds_confirmed', 0)}", 0, 1)
            pdf.cell(0, 6, f"Total Deterrence Audio & Motor Triggers: {stats.get('total_deterrence_triggers', 0)}", 0, 1)
            pdf.cell(0, 6, f"Motorcycle Engine Noise Rejections: {stats.get('motorcycle_rejections', 0)}", 0, 1)
            pdf.ln(4)

            # Species Breakdown Table
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 7, "2. 6-Class Bird Species Detection Breakdown", 0, 1, "L")
            pdf.set_font("Arial", "B", 9)
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(100, 6, "Bird Species", 1, 0, "L", True)
            pdf.cell(80, 6, "Confirmed Count", 1, 1, "C", True)

            pdf.set_font("Arial", "", 9)
            for sp_name in ["House Sparrow", "Common Myna", "Crow", "Parrot", "Pigeon", "Peacock"]:
                count = stats.get("species_breakdown", {}).get(sp_name, 0)
                pdf.cell(100, 6, f"  {sp_name}", 1, 0, "L")
                pdf.cell(80, 6, str(count), 1, 1, "C")

            pdf.ln(5)

            # Decision History Log Table
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 7, "3. Decision Engine Priority & Reason Logs", 0, 1, "L")
            pdf.set_font("Arial", "B", 8)
            pdf.cell(20, 6, "Event ID", 1, 0, "C", True)
            pdf.cell(30, 6, "Source", 1, 0, "C", True)
            pdf.cell(40, 6, "Species", 1, 0, "C", True)
            pdf.cell(20, 6, "Deterrence", 1, 0, "C", True)
            pdf.cell(70, 6, "Reason / Decision", 1, 1, "L", True)

            pdf.set_font("Arial", "", 8)
            for h in history[:10]:
                pdf.cell(20, 5, str(h.get("event_id")), 1, 0, "C")
                pdf.cell(30, 5, str(h.get("source")), 1, 0, "C")
                pdf.cell(40, 5, str(h.get("display_name"))[:20], 1, 0, "C")
                pdf.cell(20, 5, "ON" if h.get("deterrence_triggered") else "OFF", 1, 0, "C")
                pdf.cell(70, 5, str(h.get("reason"))[:45], 1, 1, "L")

            for p in [latest_file, dated_file]:
                pdf.output(str(p))

            logger.info(f"[Reports] Generated PDF report: {latest_file}")
            return latest_file

        except Exception as e:
            logger.warning(f"[Reports] FPDF generation error (text fallback used): {e}")
            txt_file = self.reports_dir / "latest_report.txt"
            with open(txt_file, "w") as f:
                f.write(f"ScareX Telemetry Report\nConfirmed Birds: {stats.get('total_birds_confirmed')}\nMotorcycle Rejections: {stats.get('motorcycle_rejections')}\n")
            return txt_file
