# kudo-rag-service

Real-Time Discord RAG (Retrieval-Augmented Generation) Assistant for AI Course Community (AI20K).

## Overview
`kudo-rag-service` is an automated assistant integrated into Discord:
- **Knowledge Ingestion**: Automatically monitors knowledge channels (`#thông-báo`, `#tài-nguyên`, `#bài-học`, `#lý-thuyết`), attaches rich metadata (channel name, author, timestamp, jump URL), and upserts text embeddings into ChromaDB.
- **RAG QA Assistance**: Answers questions posted in QA channels (`#hỏi-đáp`, `#gõ-command`, `#chung`) or direct `@mentions` using ChromaDB retrieved context and Google Gemini (`gemini-2.5-flash`) with source citations.

## Quick Start

### 1. Requirements & Setup
Ensure Python 3.10+ is installed.

```bash
# Create virtual environment
python -m venv .venv

# Activate environment (Windows PowerShell)
.venv\Scripts\Activate.ps1
# On Linux/macOS: source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Configuration variables:
- `DISCORD_TOKEN`: Your Discord Bot token.
- `GEMINI_API_KEY`: Google Gemini API key.
- `SANDBOX_GUILD_ID`: Sandbox Discord server ID for testing.
- `CHROMA_HOST` & `CHROMA_PORT`: ChromaDB Server configuration.

### 3. How to Run (Development)
Since this project uses a Client-Server architecture for the Vector Database, you need to run two separate processes locally.

**Terminal 1: Start ChromaDB Server**
```bash
# Keep this running to serve the vector database on port 8000
chroma run --path ./chroma_db
```

**Terminal 2: Start Discord Bot (Client)**
```bash
python main.py
```

### 4. Production Deployment (Docker)
For enterprise/production deployment, use Docker Compose. This ensures the bot and database run continuously in isolated containers.

```bash
# Run the entire stack in the background
docker-compose up -d

# View logs
docker-compose logs -f kudo_bot
```

### 5. Folder Structure
```
kudo-rag-service/
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── spec.md
├── config/
│   ├── __init__.py
│   └── settings.py
├── core/
│   └── __init__.py
├── interfaces/
│   └── discord_bot/
│       └── __init__.py
├── eval/
└── validation/
```
