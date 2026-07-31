import json
import logging
import threading
from pathlib import Path
from config import settings

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "curated_topics.json"
_lock = threading.Lock()

# Tùy chọn sử dụng MongoDB (Dựa trên MONGO_URI)
client = None
db = None
curated_collection = None
USE_MONGODB = False

if settings.MONGO_URI and settings.MONGO_URI.lower() != "local":
    try:
        from pymongo import MongoClient
        client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        client.server_info()
        db = client[settings.MONGO_DB_NAME]
        curated_collection = db["curated_topics"]
        USE_MONGODB = True
        logger.info(f"Connected to MongoDB at {settings.MONGO_URI}")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}. Falling back to Local JSON.")
        USE_MONGODB = False

def _load_db() -> dict:
    if not DB_PATH.exists():
        return {}
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading JSON DB: {e}")
        return {}

def _save_db(data: dict) -> None:
    try:
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Error saving JSON DB: {e}")

def upsert_message(parent_id: str, message_id: str, content: str, author: str) -> None:
    """
    Thêm hoặc cập nhật một câu trả lời vào trong Chủ đề (Parent_ID).
    """
    if USE_MONGODB and curated_collection is not None:
        try:
            # Dùng MongoDB $push để thêm vào mảng. 
            # Dùng $pull trước để xóa nếu bị trùng message_id (Tránh trùng lặp)
            curated_collection.update_one(
                {"_id": parent_id},
                {"$pull": {"curated_messages": {"message_id": message_id}}},
                upsert=True
            )
            curated_collection.update_one(
                {"_id": parent_id},
                {"$push": {"curated_messages": {
                    "message_id": message_id,
                    "author": author,
                    "content": content,
                    "is_curated": True
                }}},
                upsert=True
            )
        except Exception as e:
            logger.error(f"MongoDB upsert error: {e}")
    else:
        with _lock:
            db_data = _load_db()
            if parent_id not in db_data:
                db_data[parent_id] = {"channel_type": "auto", "curated_messages": []}
                
            # Xóa cũ nếu có để tránh trùng lặp
            db_data[parent_id]["curated_messages"] = [
                msg for msg in db_data[parent_id]["curated_messages"] 
                if msg["message_id"] != message_id
            ]
            
            db_data[parent_id]["curated_messages"].append({
                "message_id": message_id,
                "author": author,
                "content": content,
                "is_curated": True
            })
            _save_db(db_data)

def soft_delete_message(parent_id: str, message_id: str) -> None:
    """
    Gỡ tim (Set is_curated = False) cho một câu trả lời.
    """
    if USE_MONGODB and curated_collection is not None:
        try:
            curated_collection.update_one(
                {"_id": parent_id, "curated_messages.message_id": message_id},
                {"$set": {"curated_messages.$.is_curated": False}}
            )
        except Exception as e:
            logger.error(f"MongoDB soft_delete error: {e}")
    else:
        with _lock:
            db_data = _load_db()
            if parent_id in db_data:
                for msg in db_data[parent_id]["curated_messages"]:
                    if msg["message_id"] == message_id:
                        msg["is_curated"] = False
                _save_db(db_data)

def get_active_messages(parent_id: str) -> list[str]:
    """
    Lấy ra tất cả các nội dung bình luận CÒN ĐANG ĐƯỢC THẢ TIM trong Chủ đề này.
    """
    active_contents = []
    if USE_MONGODB and curated_collection is not None:
        try:
            doc = curated_collection.find_one({"_id": parent_id})
            if doc and "curated_messages" in doc:
                for msg in doc["curated_messages"]:
                    if msg.get("is_curated", False):
                        active_contents.append(msg["content"])
        except Exception as e:
            logger.error(f"MongoDB get_active_messages error: {e}")
    else:
        with _lock:
            db_data = _load_db()
            if parent_id in db_data:
                for msg in db_data[parent_id]["curated_messages"]:
                    if msg.get("is_curated", False):
                        active_contents.append(msg["content"])
                        
    return active_contents
