# AGENTS.md

This file provides guidance to agents when working with code in this repository.

---

## Project Overview

**InterviewPro AI** — An AI-powered interview preparation platform (AICTE 2026 PS22).  
Users practice mock interviews with real AI feedback, powered by IBM Granite via watsonx.ai.  
This is a genuine multi-agent pipeline, not a chatbot.

---

## Stack

| Layer       | Technology |
|-------------|-----------|
| Frontend    | Next.js 16.3.4 (App Router), TypeScript, Tailwind CSS |
| Backend     | Python 3.11+, FastAPI, Pydantic v2 |
| LLM         | IBM Granite (via watsonx.ai SDK) — **no OpenAI** |
| Database    | PostgreSQL 15 + pgvector |
| Auth        | JWT (python-jose) + bcrypt password hashing |
| Embeddings  | IBM Granite embeddings → pgvector |

---

## Directory Structure

```
InterviewPro-AI/
├── frontend/          # Next.js App Router project (npm)
│   ├── src/app/       # App Router pages & layouts
│   ├── src/components/
│   ├── src/lib/       # API client, auth helpers, types
│   └── src/hooks/
├── backend/           # FastAPI project (pip / venv)
│   ├── app/
│   │   ├── api/       # Route handlers (versioned under /api/v1/)
│   │   ├── agents/    # One file per agent (see Agent Pipeline below)
│   │   ├── models/    # SQLAlchemy ORM models
│   │   ├── schemas/   # Pydantic v2 request/response schemas
│   │   ├── services/  # Business logic (db, rag, resume, watsonx)
│   │   ├── core/      # Config (settings.py), security, db session
│   │   └── main.py    # FastAPI app entry point
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── knowledge_base/    # RAG source documents (markdown / JSON)
├── AGENTS.md
└── README.md
```

---

## Commands

### Backend
```bash
cd backend
python -m venv venv && venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload                  # dev server: http://localhost:8000
pytest                                         # all tests
pytest tests/test_agents.py::test_answer_eval  # single test
pytest -k "answer_eval"                        # by keyword
```

### Frontend
```bash
cd frontend
npm install
npm run dev        # dev server: http://localhost:3000
npm run build
npm run lint
npx jest --testPathPattern=<file>   # single test file
```

### Database
```bash
# Apply migrations
cd backend && alembic upgrade head
# Create new migration
alembic revision --autogenerate -m "description"
```

---

## Agent Pipeline

Sequential agents in `backend/app/agents/`. Each agent is a class with a `run(context: AgentContext) -> AgentContext` method. The orchestrator (`backend/app/agents/orchestrator.py`) chains them:

1. `candidate_profile_agent.py` — loads/creates candidate profile
2. `resume_analysis_agent.py` — extracts skills, experience, education from resume
3. `interview_planning_agent.py` — selects question categories & difficulty
4. `question_generation_agent.py` — generates questions using RAG + Granite
5. `answer_evaluation_agent.py` — scores candidate answers with rubric
6. `feedback_scoring_agent.py` — constructs per-question feedback
7. `performance_report_agent.py` — produces final session report

**`AgentContext`** (defined in `backend/app/agents/context.py`) is the shared state dict passed through the pipeline — never bypass it to pass data between agents.

---

## IBM Granite / watsonx.ai Integration

- All LLM calls go through `backend/app/services/watsonx_service.py`
- Never call `ibm_watsonx_ai` SDK directly from agents — always use the service wrapper
- Required env vars: `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, `WATSONX_URL`
- Default model ID: `ibm/granite-13b-instruct-v2` (configurable via `GRANITE_MODEL_ID`)
- Embeddings: `ibm/slate-125m-english-rtrvr` (configurable via `GRANITE_EMBEDDING_MODEL`)

---

## RAG

- Knowledge base docs live in `knowledge_base/` as Markdown files
- Ingestion script: `backend/app/services/rag_ingest.py` — run once after adding docs
- Vector store: pgvector table `document_embeddings` in PostgreSQL
- Retrieval: `backend/app/services/rag_service.py` — always inject retrieved context into Granite prompts

---

## Environment Variables

Both services use `.env` files (never committed). See `.env.example` in each directory.  
Critical backend vars: `DATABASE_URL`, `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, `WATSONX_URL`, `SECRET_KEY`  
Frontend: `NEXT_PUBLIC_API_URL` points to the FastAPI backend.

---

## Code Style Rules

### Python (Backend)
- Pydantic v2 models only (`model_config = ConfigDict(...)`, not `class Config:`)
- All route handlers are `async def`; database calls use `AsyncSession`
- Import order: stdlib → third-party → local app (`from app.xxx import ...`)
- Agents never import from `api/` layer; services never import from `agents/`

### TypeScript (Frontend)
- Strict TypeScript (`"strict": true` in tsconfig)
- Fetch calls to backend through `src/lib/api-client.ts` only — never raw `fetch` in components
- Server Components by default; add `"use client"` only when hooks/events are needed
- Tailwind only — no external CSS-in-JS libraries

---

## Testing

- Backend: `pytest` + `httpx` for API integration tests; mock watsonx calls with `pytest-mock`
- Frontend: Jest + React Testing Library
- Do not write tests that make real watsonx.ai API calls; use fixtures/mocks
