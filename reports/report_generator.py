import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "health.db"
ALERT_LOG_PATH = Path(__file__).resolve().parent.parent / "alerts" / "failures.log"
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


def fetch_health_logs():
    if not DB_PATH.exists():
        return []

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT name, status_code, latency_ms, is_up, timestamp
        FROM health_logs
        ORDER BY timestamp ASC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def summarize(rows):
    if not rows:
        return {
            "total_checks": 0,
            "avg_latency": None,
            "failure_count": 0,
            "uptime_by_api": {},
        }

    total_checks = len(rows)
    latency_values = [r[2] for r in rows if r[2] is not None]
    avg_latency = sum(latency_values) / len(latency_values) if latency_values else None
    failure_count = sum(1 for r in rows if r[1] != 200 or int(r[3]) != 1)

    per_api_total = defaultdict(int)
    per_api_up = defaultdict(int)
    for name, status_code, latency_ms, is_up, ts in rows:
        per_api_total[name] += 1
        per_api_up[name] += int(is_up)

    uptime_by_api = {
        name: (per_api_up[name] / per_api_total[name]) * 100
        for name in per_api_total
    }

    return {
        "total_checks": total_checks,
        "avg_latency": avg_latency,
        "failure_count": failure_count,
        "uptime_by_api": uptime_by_api,
    }


def build_latency_series(rows):
    per_api = defaultdict(lambda: {"x": [], "y": []})
    for name, status_code, latency_ms, is_up, ts in rows:
        if latency_ms is None:
            continue
        try:
            dt = datetime.fromisoformat(ts)
        except ValueError:
            continue
        per_api[name]["x"].append(dt)
        per_api[name]["y"].append(latency_ms)
    return per_api


def read_recent_failures(limit=20):
    if not ALERT_LOG_PATH.exists():
        return []

    lines = ALERT_LOG_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()
    return lines[-limit:]


def create_pdf_report(output_path=None):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    if output_path is None:
        output_path = REPORTS_DIR / f"api_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    else:
        output_path = Path(output_path)

    rows = fetch_health_logs()
    summary = summarize(rows)
    latency_series = build_latency_series(rows)
    recent_failures = read_recent_failures(limit=20)

    with PdfPages(output_path) as pdf:
        # Page 1: Summary
        fig = plt.figure(figsize=(11.69, 8.27))  # A4 landscape
        fig.suptitle("API Health Monitoring Report", fontsize=18, fontweight="bold")

        text_lines = [
            f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total checks: {summary['total_checks']}",
            f"Average latency: {summary['avg_latency']:.2f} ms" if summary["avg_latency"] is not None else "Average latency: N/A",
            f"Failure count: {summary['failure_count']}",
            "",
            "Uptime by API:",
        ]
        for api_name, uptime in sorted(summary["uptime_by_api"].items()):
            text_lines.append(f"  - {api_name}: {uptime:.2f}%")

        fig.text(0.05, 0.90, "\n".join(text_lines), fontsize=12, va="top", family="monospace")
        plt.axis("off")
        pdf.savefig(fig)
        plt.close(fig)

        # Page 2: Latency trend
        fig, ax = plt.subplots(figsize=(11.69, 8.27))
        ax.set_title("Latency Over Time")
        ax.set_xlabel("Time")
        ax.set_ylabel("Latency (ms)")
        for api_name, series in latency_series.items():
            if series["x"]:
                ax.plot(series["x"], series["y"], marker="o", linewidth=1.5, label=api_name)
        ax.legend(loc="upper left", fontsize=8)
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()
        pdf.savefig(fig)
        plt.close(fig)

        # Page 3: Uptime bar chart
        fig, ax = plt.subplots(figsize=(11.69, 8.27))
        names = list(summary["uptime_by_api"].keys())
        values = [summary["uptime_by_api"][n] for n in names]
        ax.bar(names, values)
        ax.set_title("Uptime Percentage by API")
        ax.set_ylabel("Uptime (%)")
        ax.set_ylim(0, 100)
        ax.grid(axis="y", alpha=0.3)
        plt.xticks(rotation=25, ha="right")
        pdf.savefig(fig)
        plt.close(fig)

        # Page 4: Recent failures (text)
        fig = plt.figure(figsize=(11.69, 8.27))
        fig.suptitle("Recent Failure Log Entries", fontsize=16, fontweight="bold")
        if not recent_failures:
            fig.text(0.05, 0.90, "No failure log entries found.", fontsize=12, va="top")
        else:
            block = "\n".join(recent_failures)
            fig.text(0.05, 0.95, block, fontsize=9, va="top", family="monospace")
        plt.axis("off")
        pdf.savefig(fig)
        plt.close(fig)

    return output_path