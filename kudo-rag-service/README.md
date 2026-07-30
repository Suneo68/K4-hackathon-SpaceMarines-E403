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

### 3. Folder Structure
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
