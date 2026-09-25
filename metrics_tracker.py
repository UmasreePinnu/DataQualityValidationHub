import json
import os
from datetime import datetime

STATS_FILE = os.path.join(os.path.dirname(__file__), "app_statistics.json")

def _load_stats() -> list:
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def log_event(feature: str, duration_sec: float, details: dict):
    stats = _load_stats()
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "feature": feature,
        "duration_sec": round(duration_sec, 2),
        "details": details,
    }
    stats.append(entry)
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)

def get_stats() -> list:
    return _load_stats()

def clear_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "w") as f:
            json.dump([], f)