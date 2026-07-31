import os
from pathlib import Path
from dotenv import load_dotenv

# Project Root Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load Environment Variables from .env file
load_dotenv(dotenv_path=BASE_DIR / ".env")

# API Keys & Tokens
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SANDBOX_GUILD_ID = os.getenv("SANDBOX_GUILD_ID", "")

# Discord Channel Topic Tags (Dynamic setup via Channel Topic)
KNOWLEDGE_TOPIC_TAG = "[KUDO-KNOWLEDGE]"
QA_TOPIC_TAG = "[KUDO-QA]"
CURATION_EMOJI = "✅"

# AI Model Configurations
LLM_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "gemini-embedding-2"
TOP_K_RESULTS = 5

# Database Configurations
MONGO_URI = os.getenv("MONGO_URI", "local")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "kudo_rag_db")

# ChromaDB Configurations (Client-Server Mode)
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
