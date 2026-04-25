import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional


RETENTION_DAYS = 30


def _load_db(path: str) -> Dict:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"logs": [], "retention_days": RETENTION_DAYS, "last_cleanup": None}


def _save_db(path: str, db: Dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4)


def prune_old_logs(logs_path: str = "data/runtime_logs.json") -> int:
    db = _load_db(logs_path)
    retention_days = db.get("retention_days", RETENTION_DAYS)
    cutoff = (datetime.now() - timedelta(days=retention_days)).isoformat()
    
    original_count = len(db.get("logs", []))
    db["logs"] = [
        log for log in db.get("logs", [])
        if log.get("timestamp", "") > cutoff
    ]
    db["last_cleanup"] = datetime.now().isoformat()
    
    _save_db(logs_path, db)
    return original_count - len(db["logs"])


def add_log(
    message: str,
    level: str = "INFO",
    logs_path: str = "data/runtime_logs.json"
) -> None:
    db = _load_db(logs_path)
    db["logs"].append({
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": message
    })
    _save_db(logs_path, db)


def get_recent_logs(
    limit: int = 100,
    logs_path: str = "data/runtime_logs.json"
) -> List[Dict]:
    db = _load_db(logs_path)
    logs = db.get("logs", [])
    return logs[-limit:] if len(logs) > limit else logs


def clear_logs(logs_path: str = "data/runtime_logs.json") -> None:
    db = _load_db(logs_path)
    db["logs"] = []
    db["last_cleanup"] = datetime.now().isoformat()
    _save_db(logs_path, db)