# InterviewPro AI

**AI-powered interview preparation platform — AICTE 2026 PS22 Interview Trainer Agent**

Users practice mock interviews with personalized AI feedback, role-specific questions, and
detailed performance reports — powered by a 7-agent pipeline running IBM Granite via watsonx.ai.

---

## Architecture

```
Frontend (Next.js 14)  →  Backend (FastAPI)  →  PostgreSQL + pgvector
                                ↓
                        7-Agent Pipeline
                        (IBM Granite via watsonx.ai)
```

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 App Router · TypeScript · Tailwind CSS |
| Backend | Python 3.11+ · FastAPI · Pydantic v2 |
| LLM | IBM Granite via watsonx.ai (no OpenAI) |
| Database | PostgreSQL 15 + pgvector |
| Auth | JWT + bcrypt |

---

## Local Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker (for PostgreSQL with pgvector)
- IBM Cloud API key with watsonx.ai access

### 1. Start PostgreSQL with pgvector

```bash
docker run -d \
  --name interviewpro-db \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=interviewpro \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

### 2. Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env          # Edit: add IBM credentials + DB URL

alembic upgrade head          # Create tables
python -m app.services.rag_ingest   # Seed knowledge base (run once)

uvicorn app.main:app --reload  # http://localhost:8000
# API docs: http://localhost:8000/docs
```

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local    # Edit if backend runs on a different port

npm run dev                   # http://localhost:3000
```

---

## Agent Pipeline

A session passes through 7 sequential agents, each writing to a shared `AgentContext`:

1. **CandidateProfileAgent** — loads candidate profile from DB
2. **ResumeAnalysisAgent** — extracts skills/experience summary via Granite
3. **InterviewPlanningAgent** — decides question mix and difficulty distribution
4. **QuestionGenerationAgent** — RAG retrieval → Granite question + model-answer generation
5. **AnswerEvaluationAgent** — scores answers on Accuracy / Relevance / Clarity / Completeness
6. **FeedbackScoringAgent** — per-answer tips + skill-area scores
7. **PerformanceReportAgent** — final report with radar chart data + executive summary

---

## Key Commands

### Backend

```bash
cd backend && source venv/bin/activate   # or venv\Scripts\activate on Windows

pytest                                    # all tests
pytest tests/test_agents.py::test_name   # single test
pytest -k "keyword"                       # by keyword

alembic revision --autogenerate -m "description"   # new migration
alembic upgrade head                               # apply migrations
```

### Frontend

```bash
cd frontend
npm run dev      # development server
npm run build    # production build
npm run lint     # ESLint
npx jest --testPathPattern=ComponentName   # single test
```

---

## Environment Variables

See [`backend/.env.example`](backend/.env.example) and [`frontend/.env.example`](frontend/.env.example).

**IBM credentials must never be committed or exposed to the frontend.**

---

## Project Structure

```
InterviewPro-AI/
├── knowledge_base/        # RAG source documents (Markdown)
├── backend/               # FastAPI application
│   ├── app/
│   │   ├── agents/        # 7-agent pipeline
│   │   ├── api/v1/        # REST route handlers
│   │   ├── core/          # Config, DB, security
│   │   ├── models/        # SQLAlchemy ORM
│   │   ├── schemas/       # Pydantic v2 I/O
│   │   └── services/      # WatsonX, RAG, Resume, Session
│   └── tests/
└── frontend/              # Next.js 14 application
    └── src/
        ├── app/           # App Router pages
        ├── components/    # UI components
        ├── hooks/         # Custom React hooks
        └── lib/           # api-client, auth, types
```

---

## AICTE PS22 Requirements Coverage

| Requirement | Implementation |
|---|---|
| Candidate profile | CandidateProfileAgent + `/api/v1/profiles` |
| Resume analysis | ResumeAnalysisAgent + pdfplumber/python-docx + Granite |
| Personalization | InterviewPlanningAgent (role + experience + resume) |
| Technical/HR/Behavioral/Mixed questions | QuestionGenerationAgent + RAG by category |
| Industry expectations | `knowledge_base/industry/` RAG documents |
| Model answers | Granite-generated, shown in final report |
| Interactive mock interview | 10-question session with per-answer quick score |
| 4-dimension evaluation | Accuracy · Relevance · Clarity · Completeness |
| Improvement tips | FeedbackScoringAgent — per-answer + top-3 areas |
| Performance report | PerformanceReportAgent + radar chart + executive summary |
| IBM Granite / watsonx.ai | Mandatory — used by 5 of 7 agents |
| Multi-agent workflow | 7-agent sequential pipeline via AgentContext |
