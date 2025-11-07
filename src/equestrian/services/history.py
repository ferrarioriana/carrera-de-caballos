import json
import os
import time
from typing import Dict, Any, List

HISTORY_FILE = "equestrian_history.json"

def load_history() -> List[Dict[str, Any]]:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def append_history(entry: Dict[str, Any]) -> None:
    history = load_history()
    entry = dict(entry)
    if "timestamp" not in entry:
        entry["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    history.append(entry)
    if len(history) > 500:
        history = history[-500:]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
