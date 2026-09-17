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
    Unified PDF and CSV Report Generator supporting:
    - Bird Report (Module A)
    - Tomato Report (Module B)
    - Combined ScareX Report (Modules A & B)
    """
    def __init__(self, db_manager):
        self.db = db_manager
        self.reports_dir = Path(config.reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_all_reports(self, bird_stats=None, tomato_metrics=None, crop_state=None, rows_stats=None):
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_stats = self.db.get_summary_stats()
        history = self.db.get_recent_history(limit=30)
        crop_states = self.db.get_recent_crop_states(limit=5)

        csv_path = self.generate_csv(summary_stats, history, crop_states, tomato_metrics, rows_stats, timestamp_str)
        pdf_path = self.generate_pdf(summary_stats, history, crop_states, tomato_metrics, crop_state, rows_stats, timestamp_str)

        return {
            "timestamp": timestamp_str,
            "csv": str(csv_path),
            "pdf": str(pdf_path),
            "stats": summary_stats
        }

    def generate_csv(self, stats, history, crop_states, tomato_metrics, rows_stats, timestamp_str):
        latest_file = self.reports_dir / "latest_report.csv"
        dated_file = self.reports_dir / f"scarex_report_{timestamp_str}.csv"

        rows = [
            ["ScareX Combined Telemetry & Crop Protection Report"],
            ["Generated At", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            [],
            ["--- MODULE A: BIRD DETECTION & DETERRENCE ---"],
            ["Confirmed Bird Detections", stats.get("total_birds_confirmed", 0)],
            ["Total Deterrence Triggers", stats.get("total_deterrence_triggers", 0)],
            ["Motorcycle Noise Rejections", stats.get("motorcycle_rejections", 0)],
            [],
            ["Bird Species Breakdown"],
            ["Species Name", "Confirmed Count"]
        ]

        for sp, count in stats.get("species_breakdown", {}).items():
            rows.append([sp, count])

        rows.extend([
            [],
            ["--- MODULE B: TOMATO CROP MONITORING ---"],
            ["Total Tomatoes Counted", tomato_metrics.get("total_tomatoes", 0) if tomato_metrics else 0],
            ["Fully Ripened Count", tomato_metrics.get("fully_ripened_count", 0) if tomato_metrics else 0],
            ["Half Ripened Count", tomato_metrics.get("half_ripened_count", 0) if tomato_metrics else 0],
            ["Green Tomato Count", tomato_metrics.get("green_count", 0) if tomato_metrics else 0],
            ["Fully Ripened %", tomato_metrics.get("fully_ripened_pct", 0.0) if tomato_metrics else 0.0],
            ["Average Confidence", tomato_metrics.get("average_confidence", 0.0) if tomato_metrics else 0.0],
            [],
            ["Row-Wise Crop Priority Statistics"],
            ["Row ID", "Tomato Count", "Fully Ripened", "Half Ripened", "Green", "Priority Level", "Rationale"]
        ])

        if rows_stats:
            for r in rows_stats:
                rows.append([
                    r.get("row_id"), r.get("tomato_count"), r.get("fully_ripened_count"),
                    r.get("half_ripened_count"), r.get("green_count"), r.get("priority"), r.get("reason")
                ])

        for p in [latest_file, dated_file]:
            with open(p, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

        logger.info(f"[Reports] Generated CSV report: {latest_file}")
        return latest_file

    def generate_pdf(self, stats, history, crop_states, tomato_metrics, crop_state, rows_stats, timestamp_str):
        latest_file = self.reports_dir / "latest_report.pdf"
        dated_file = self.reports_dir / f"scarex_report_{timestamp_str}.pdf"

        try:
            from fpdf import FPDF

            class ScareXPDF(FPDF):
                def header(self):
                    self.set_font("Arial", "B", 15)
                    self.set_text_color(255, 94, 54)
                    self.cell(0, 10, "ScareX Crop Protection & Tomato Monitoring Report", 0, 1, "C")
                    self.set_font("Arial", "I", 9)
                    self.set_text_color(100, 100, 100)
                    self.cell(0, 5, "Raspberry Pi 5 Bird Deterrence & Crop Condition Analysis Platform", 0, 1, "C")
                    self.ln(5)

                def footer(self):
                    self.set_y(-15)
                    self.set_font("Arial", "I", 8)
                    self.cell(0, 10, f"ScareX System Report | Page {self.page_no()}", 0, 0, "C")

            pdf = ScareXPDF()
            pdf.add_page()

            # Executive Overview
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 7, "1. Executive Telemetry Overview", 0, 1, "L")
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 6, f"Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1)
            pdf.cell(0, 6, f"Confirmed Bird Intrusions: {stats.get('total_birds_confirmed', 0)}", 0, 1)
            pdf.cell(0, 6, f"Deterrence Audio & Motor Triggers: {stats.get('total_deterrence_triggers', 0)}", 0, 1)
            pdf.cell(0, 6, f"Motorcycle Engine Noise Rejections: {stats.get('motorcycle_rejections', 0)}", 0, 1)
            pdf.ln(4)

            # Module B Crop Condition
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 7, "2. Tomato Crop Condition State Analysis", 0, 1, "L")
            pdf.set_font("Arial", "", 10)
            if crop_state:
                pdf.cell(0, 6, f"Current Crop Condition: {crop_state.get('crop_state', 'N/A')}", 0, 1)
                pdf.cell(0, 6, f"Condition Rationale: {crop_state.get('reason', 'N/A')}", 0, 1)
                pdf.cell(0, 6, f"Recommendation: {crop_state.get('recommendation', 'N/A')}", 0, 1)
            if tomato_metrics:
                pdf.cell(0, 6, f"Maturity Breakdown: Fully Ripened: {tomato_metrics.get('fully_ripened_pct')}% | Half: {tomato_metrics.get('half_ripened_pct')}% | Green: {tomato_metrics.get('green_pct')}%", 0, 1)
            pdf.ln(4)

            # Row Priority Table
            if rows_stats:
                pdf.set_font("Arial", "B", 11)
                pdf.cell(0, 7, "3. Row-Wise Crop Priority Statistics", 0, 1, "L")
                pdf.set_font("Arial", "B", 9)
                pdf.set_fill_color(230, 230, 230)
                pdf.cell(20, 6, "Row ID", 1, 0, "C", True)
                pdf.cell(30, 6, "Tomatoes", 1, 0, "C", True)
                pdf.cell(30, 6, "Fully Ripened", 1, 0, "C", True)
                pdf.cell(30, 6, "Priority", 1, 0, "C", True)
                pdf.cell(70, 6, "Rationale", 1, 1, "L", True)

                pdf.set_font("Arial", "", 8)
                for r in rows_stats:
                    pdf.cell(20, 5, f"Row {r.get('row_id')}", 1, 0, "C")
                    pdf.cell(30, 5, str(r.get("tomato_count")), 1, 0, "C")
                    pdf.cell(30, 5, f"{r.get('fully_ripened_count')} ({r.get('fully_ripened_pct')}%)", 1, 0, "C")
                    pdf.cell(30, 5, str(r.get("priority")), 1, 0, "C")
                    pdf.cell(70, 5, str(r.get("reason"))[:45], 1, 1, "L")

            for p in [latest_file, dated_file]:
                pdf.output(str(p))

            logger.info(f"[Reports] Generated PDF report: {latest_file}")
            return latest_file

        except Exception as e:
            logger.warning(f"[Reports] FPDF error (text fallback used): {e}")
            txt_file = self.reports_dir / "latest_report.txt"
            with open(txt_file, "w") as f:
                f.write(f"ScareX Combined Telemetry Report\nBirds Confirmed: {stats.get('total_birds_confirmed')}\nCrop State: {crop_state.get('crop_state') if crop_state else 'N/A'}\n")
            return txt_file
