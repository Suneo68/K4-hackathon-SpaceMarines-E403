import json
import os
import threading
from typing import Dict, List

DB_FILE = "experts_db.json"
_lock = threading.Lock()

def _load_db() -> Dict[str, List[str]]:
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_db(data: Dict[str, List[str]]):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def add_expert(tag: str, user_id: str) -> None:
    with _lock:
        db = _load_db()
        tag = tag.strip().lower()
        if tag not in db:
            db[tag] = []
        if user_id not in db[tag]:
            db[tag].append(user_id)
        _save_db(db)

def remove_expert(tag: str, user_id: str) -> bool:
    with _lock:
        db = _load_db()
        tag = tag.strip().lower()
        if tag in db and user_id in db[tag]:
            db[tag].remove(user_id)
            if not db[tag]:
                del db[tag]
            _save_db(db)
            return True
        return False

def get_all_tags() -> List[str]:
    with _lock:
        return list(_load_db().keys())

def get_experts_by_tag(tag: str) -> List[str]:
    with _lock:
        db = _load_db()
        return db.get(tag.strip().lower(), [])

def get_full_db() -> Dict[str, List[str]]:
    with _lock:
        return _load_db()
