import json
import os
from typing import Dict, Any

SAVE_FILE = "equestrian_progress.json"

def cargar_progreso() -> Dict[str, Any]:
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def guardar_progreso(data: Dict[str, Any]) -> None:
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Error guardando progreso:", e)
