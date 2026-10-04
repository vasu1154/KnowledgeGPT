# KnowledgeGPT — AI Knowledge Assistant

AI Knowledge Assistant is an AI-powered document question-answering platform that allows users to upload documents (PDF, DOCX, TXT) and interact with them using natural language powered by Retrieval-Augmented Generation (RAG).

## 🏗️ Architecture Stack

- **Backend:** FastAPI (Python 3.12, Async)
- **AI Framework:** LangChain & Google Gemini
- **Vector Database:** ChromaDB
- **Relational Database:** PostgreSQL (asyncpg, SQLAlchemy 2.0, Alembic)
- **Queue & Cache:** Redis + Celery
- **Frontend:** React + TypeScript + Tailwind CSS (Phase 10)
- **Deployment:** Docker & Docker Compose

## 🚀 Quick Start (Phase 1 — Project Foundation)

### 1. Prerequisites
- Python 3.12+
- Docker & Docker Compose

### 2. Start PostgreSQL & Redis
```bash
docker compose up -d
```

### 3. Setup Backend
```bash
cd backend
python -m venv .venv
# Activate virtual environment (Windows PowerShell)
.venv\Scripts\activate
# Or Windows Command Prompt:
# .venv\Scripts\activate.bat

pip install -r requirements.txt
cp .env.example .env
```

### 4. Run Migrations & Server
```bash
# Start FastAPI development server
uvicorn app.main:app --reload
```

- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)
- API v1: [http://localhost:8000/api/v1/](http://localhost:8000/api/v1/)
