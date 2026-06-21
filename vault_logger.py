import os
import json
from datetime import datetime
from config import BASE_DIR

LOG_FILE = os.path.join(BASE_DIR, "vault_logs.json")


def _read_logs():
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def _write_logs(logs):
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)


def log_event(event_type: str, detail: str = ""):
    logs = _read_logs()
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event": event_type,
        "detail": detail,
    }
    logs.append(entry)
    # Keep last 500 entries max
    if len(logs) > 500:
        logs = logs[-500:]
    _write_logs(logs)


def get_logs():
    return _read_logs()
