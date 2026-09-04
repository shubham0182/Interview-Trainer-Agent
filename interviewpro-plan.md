# InterviewPro AI — Implementation Plan

AICTE 2026 PS22 Interview Trainer Agent  
Status: `[ ] pending`

---

## Key Decisions Confirmed

| Decision | Choice |
|---|---|
| Answer evaluation timing | Hybrid: quick score per answer immediately, deep evaluation at session end |
| Session length | Fixed 10 questions per session |
| Interview types | Technical / HR / Behavioral / Mixed (candidate picks before start) |
| Answer input | Text only (no voice in MVP) |
| LLM | IBM Granite via watsonx.ai exclusively |
| Vector store | pgvector inside PostgreSQL (no separate vector DB) |
| Long-running pipeline | Polling `/api/v1/sessions/{id}/status` — no WebSockets |
| Frontend ↔ backend coupling | `NEXT_PUBLIC_API_URL` only; all IBM credentials backend-only |

---

## Open Issues / Decisions to Resolve Before Coding

1. **Model answer display** — Should model answers be shown (a) immediately after the quick score, (b) only in the final report, or (c) optionally revealed by the candidate? Default assumed: shown only in the final report.
2. **Resume requirement** — Is resume upload mandatory to start a session, or optional (profile-only mode)? Default assumed: optional — if skipped, questions are generated from job-role + experience level alone.
3. **Session resumability** — If the candidate closes the browser mid-session, should the session be resumable? Default assumed: yes, partially answered sessions are stored and can be continued.
4. **Knowledge base seeding** — The RAG knowledge base must be populated before the app is usable. Plan assumes a set of seed documents are committed to `knowledge_base/` and ingested during setup.
5. **Scoring rubric** — Answer evaluation uses 4 dimensions: Accuracy, Relevance, Clarity, Completeness (each 0–25, total 0–100). This must be agreed upon before implementing the evaluation agent.

---

## System Architecture Overview

The platform has three runtime concerns:

1. **Frontend** (Next.js, port 3000) — user-facing SPA; communicates with backend via REST only
2. **Backend** (FastAPI, port 8000) — hosts all business logic, agent pipeline, RAG, and IBM Granite calls
3. **PostgreSQL + pgvector** (port 5432) — all persistence including embeddings

The agent pipeline runs entirely inside the backend. The frontend never calls watsonx.ai.

### Request Flow (Session)

```
Browser → Next.js → POST /api/v1/sessions (start)
                  ← session_id

Browser → POST /api/v1/sessions/{id}/answers (per answer)
                  ← quick_score (immediate Granite call)

Browser → POST /api/v1/sessions/{id}/complete
       Backend runs full 7-agent pipeline (async background task)
                  ← { status: "processing" }

Browser polls → GET /api/v1/sessions/{id}/status
             ← { status: "complete" | "processing" | "failed" }

Browser → GET /api/v1/sessions/{id}/report
        ← full performance report JSON
```

---

## A. Complete System Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (Next.js 14 App Router)                       │
│  Pages: Auth · Profile · Resume · Interview · Report    │
│  src/lib/api-client.ts — single fetch gateway           │
└───────────────┬─────────────────────────────────────────┘
                │ REST (JSON)  NEXT_PUBLIC_API_URL
┌───────────────▼─────────────────────────────────────────┐
│  Backend (FastAPI)                                      │
│  ┌───────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ API Layer │  │ Agent Pipeline│  │ Services        │  │
│  │ /api/v1/  │→ │ Orchestrator  │→ │ WatsonxService  │  │
│  │ routes    │  │ 7 Agents      │  │ RAGService      │  │
│  └───────────┘  └──────────────┘  │ ResumeService   │  │
│                                   │ AuthService     │  │
│                                   └────────┬────────┘  │
└────────────────────────────────────────────┼────────────┘
                                             │
              ┌──────────────────────────────┼──────────┐
              │                              │          │
   ┌──────────▼──────────┐       ┌───────────▼───────┐  │
   │  PostgreSQL + pgvector│      │  watsonx.ai       │  │
   │  - users             │      │  IBM Granite LLM  │  │
   │  - candidate_profiles│      │  IBM Granite Embed│  │
   │  - interview_sessions│      └───────────────────┘  │
   │  - questions         │                              │
   │  - answers           │                              │
   │  - document_embeddings│                             │
   └──────────────────────┘                              │
```

---

## B. Frontend Architecture

### Pages (App Router)

| Route | Page | Auth Required |
|---|---|---|
| `/` | Landing / marketing | No |
| `/auth/login` | Login form | No |
| `/auth/register` | Registration form | No |
| `/dashboard` | Session history + start new | Yes |
| `/profile` | Candidate profile + resume upload | Yes |
| `/interview/setup` | Choose type + job role | Yes |
| `/interview/[sessionId]` | Live interview (Q&A loop) | Yes |
| `/report/[sessionId]` | Final performance report | Yes |

### Component Tree (key components)

```
src/
├── app/
│   ├── layout.tsx                  # Root layout + auth provider
│   ├── (auth)/login/page.tsx
│   ├── (auth)/register/page.tsx
│   ├── dashboard/page.tsx
│   ├── profile/page.tsx
│   ├── interview/
│   │   ├── setup/page.tsx
│   │   └── [sessionId]/page.tsx    # "use client" — polling loop
│   └── report/[sessionId]/page.tsx
├── components/
│   ├── ui/                         # Reusable Tailwind primitives
│   ├── interview/
│   │   ├── QuestionCard.tsx
│   │   ├── AnswerInput.tsx
│   │   ├── QuickScoreBadge.tsx     # Shows per-answer immediate score
│   │   └── ProgressBar.tsx
│   ├── report/
│   │   ├── ScoreChart.tsx          # Radar chart: 4 dimensions
│   │   ├── QuestionReview.tsx
│   │   └── ImprovementTips.tsx
│   └── profile/
│       ├── ResumeUpload.tsx
│       └── ProfileForm.tsx
├── lib/
│   ├── api-client.ts               # All fetch calls live here
│   ├── auth.ts                     # JWT cookie helpers
│   └── types.ts                    # Mirrors Pydantic schemas exactly
└── hooks/
    ├── useSession.ts               # Session state + polling
    └── useAuth.ts
```

### State Management

- No external state library (Zustand/Redux) — React context for auth, `useState`/`useReducer` for interview state
- Interview page polls `GET /api/v1/sessions/{id}/status` every 3 seconds while `status === "processing"`
- JWT stored in httpOnly cookie set by the backend; Next.js middleware guards protected routes

---

## C. FastAPI Backend Architecture

### Module Layering (strict, no cross-layer imports)

```
api/          ← HTTP in/out only; calls services or orchestrator
agents/       ← business pipeline; calls services only
services/     ← data access, LLM, RAG, resume; calls models
models/       ← SQLAlchemy ORM definitions only
schemas/      ← Pydantic v2 I/O shapes; no logic
core/         ← config, security, db session; no domain logic
```

### File Layout

```
backend/
├── app/
│   ├── main.py                     # App factory, CORS, router registration
│   ├── core/
│   │   ├── config.py               # Settings (pydantic-settings BaseSettings)
│   │   ├── db.py                   # AsyncSession factory, get_db dependency
│   │   └── security.py             # JWT create/verify, password hash/verify
│   ├── models/
│   │   ├── user.py
│   │   ├── candidate_profile.py
│   │   ├── interview_session.py
│   │   ├── question.py
│   │   ├── answer.py
│   │   └── document_embedding.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── profile.py
│   │   ├── session.py
│   │   ├── question.py
│   │   ├── answer.py
│   │   └── report.py
│   ├── agents/
│   │   ├── context.py              # AgentContext TypedDict definition
│   │   ├── orchestrator.py         # Chains all 7 agents
│   │   ├── candidate_profile_agent.py
│   │   ├── resume_analysis_agent.py
│   │   ├── interview_planning_agent.py
│   │   ├── question_generation_agent.py
│   │   ├── answer_evaluation_agent.py
│   │   ├── feedback_scoring_agent.py
│   │   └── performance_report_agent.py
│   ├── services/
│   │   ├── watsonx_service.py      # IBM Granite wrapper
│   │   ├── rag_service.py          # pgvector similarity search
│   │   ├── rag_ingest.py           # One-time ingestion script
│   │   ├── resume_service.py       # PDF/DOCX → structured text
│   │   └── session_service.py      # CRUD for sessions, questions, answers
│   └── api/
│       └── v1/
│           ├── auth.py
│           ├── profiles.py
│           ├── sessions.py
│           ├── answers.py
│           └── reports.py
├── alembic/                        # Migration files
├── tests/
│   ├── conftest.py                 # Fixtures: test DB, mock_watsonx
│   ├── test_agents/
│   ├── test_api/
│   └── test_services/
├── requirements.txt
└── .env.example
```

---

## D. PostgreSQL + pgvector Database Design

### Schema Overview

#### `users`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| email | VARCHAR UNIQUE NOT NULL | |
| hashed_password | VARCHAR NOT NULL | bcrypt |
| full_name | VARCHAR | |
| created_at | TIMESTAMPTZ | |

#### `candidate_profiles`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK → users.id UNIQUE | one per user |
| job_role | VARCHAR | e.g. "Software Engineer" |
| experience_level | VARCHAR | "fresher" / "junior" / "mid" / "senior" |
| skills | JSONB | list of strings from resume/manual |
| education | JSONB | degrees, institutions |
| experience | JSONB | work history |
| projects | JSONB | projects from resume |
| resume_text | TEXT | raw extracted text |
| resume_filename | VARCHAR | original upload name |
| resume_parsed | BOOLEAN DEFAULT false | flag: parsing complete |
| updated_at | TIMESTAMPTZ | |

#### `interview_sessions`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK → users.id | |
| interview_type | VARCHAR | "technical" / "hr" / "behavioral" / "mixed" |
| job_role | VARCHAR | copied from profile at start |
| experience_level | VARCHAR | copied from profile at start |
| status | VARCHAR | "active" / "processing" / "complete" / "failed" |
| total_score | FLOAT NULLABLE | set after full evaluation |
| question_count | INT DEFAULT 10 | |
| current_question_index | INT DEFAULT 0 | for resumability |
| pipeline_context | JSONB NULLABLE | serialized AgentContext for resume |
| started_at | TIMESTAMPTZ | |
| completed_at | TIMESTAMPTZ NULLABLE | |

#### `questions`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| session_id | UUID FK → interview_sessions.id | |
| sequence_number | INT | 1–10 |
| question_text | TEXT | |
| question_type | VARCHAR | "technical" / "hr" / "behavioral" |
| difficulty | VARCHAR | "easy" / "medium" / "hard" |
| model_answer | TEXT | Granite-generated ideal answer |
| rag_sources | JSONB | chunk IDs used in generation |
| created_at | TIMESTAMPTZ | |

#### `answers`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| question_id | UUID FK → questions.id | |
| session_id | UUID FK → interview_sessions.id | |
| answer_text | TEXT | |
| quick_score | FLOAT NULLABLE | 0–100, immediate evaluation |
| accuracy_score | FLOAT NULLABLE | 0–25 |
| relevance_score | FLOAT NULLABLE | 0–25 |
| clarity_score | FLOAT NULLABLE | 0–25 |
| completeness_score | FLOAT NULLABLE | 0–25 |
| total_score | FLOAT NULLABLE | sum of 4 dimensions |
| feedback_text | TEXT NULLABLE | detailed per-answer feedback |
| improvement_tip | TEXT NULLABLE | specific tip for this answer |
| submitted_at | TIMESTAMPTZ | |

#### `document_embeddings`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| source_file | VARCHAR | e.g. "software_engineer_questions.md" |
| chunk_index | INT | position in source doc |
| chunk_text | TEXT | raw text chunk |
| embedding | vector(1536) | from IBM slate embedding model |
| metadata | JSONB | role, type, difficulty tags |
| created_at | TIMESTAMPTZ | |

### Indexes
- `document_embeddings.embedding` — IVFFlat or HNSW index for ANN search
- `interview_sessions.user_id` — for dashboard queries
- `answers.session_id` — for report aggregation

---

## E. RAG Architecture and Ingestion Process

### Knowledge Base Structure (`knowledge_base/`)

```
knowledge_base/
├── technical/
│   ├── software_engineer.md
│   ├── data_scientist.md
│   ├── devops_engineer.md
│   └── frontend_developer.md
├── behavioral/
│   ├── star_method_scenarios.md
│   └── common_behavioral_questions.md
├── hr/
│   ├── hr_interview_guidelines.md
│   └── salary_negotiation.md
└── industry/
    ├── expectations_fresher.md
    └── expectations_senior.md
```

Each file uses consistent front-matter tags:
```
---
role: software_engineer
type: technical
difficulty: medium
---
```

### Ingestion Pipeline (`rag_ingest.py`)

1. Walk `knowledge_base/` recursively, read each `.md` file
2. Parse YAML front-matter → metadata dict
3. Chunk text: 512-token sliding window, 64-token overlap
4. For each chunk: call `WatsonxService.embed(text)` → 1536-dim vector
5. Bulk-insert into `document_embeddings` (truncate-then-insert on re-run)
6. Build IVFFlat index on `document_embeddings.embedding` column

### Retrieval (`rag_service.py`)

- Input: `query_text`, `top_k=5`, optional `metadata_filter` (role, type)
- Embed query with same model → ANN search via pgvector `<->` operator
- Return list of `{chunk_text, source_file, metadata, similarity_score}`
- Always filter by `metadata.role` when role is known (improves relevance)

---

## F. IBM Granite / watsonx.ai Integration Architecture

### `WatsonxService` (`services/watsonx_service.py`)

Wraps the `ibm_watsonx_ai` SDK. Exposes two methods:

**`generate(prompt: str, params: GenerateParams) -> str`**
- Calls `ModelInference` with `GRANITE_MODEL_ID`
- `GenerateParams` includes: `max_new_tokens`, `temperature`, `stop_sequences`
- Returns the generated text string only (strips metadata)
- Retries up to 3 times on rate-limit (429) with exponential back-off

**`embed(text: str) -> list[float]`**
- Calls the embeddings endpoint with `GRANITE_EMBEDDING_MODEL`
- Returns a 1536-dimensional float list

### Prompt Patterns

Each agent that calls Granite constructs prompts using module-level string templates (never inline):

```python
# example in question_generation_agent.py
QUESTION_GENERATION_PROMPT = """
You are an expert technical interviewer.
Role: {job_role}
Experience Level: {experience_level}
Candidate Skills: {skills}

Relevant Interview Context (from knowledge base):
{rag_context}

Generate {count} {interview_type} interview questions.
Format as JSON array: [{{"question": "...", "difficulty": "...", "model_answer": "..."}}]
"""
```

Rules:
- All prompts request structured JSON output from Granite
- Each agent owns its own prompt templates
- `WatsonxService` does not know about prompt content

### Config (environment-driven)

| Env Var | Purpose |
|---|---|
| `WATSONX_API_KEY` | IBM Cloud API key |
| `WATSONX_PROJECT_ID` | watsonx.ai project ID |
| `WATSONX_URL` | Regional endpoint |
| `GRANITE_MODEL_ID` | Default: `ibm/granite-13b-instruct-v2` |
| `GRANITE_EMBEDDING_MODEL` | Default: `ibm/slate-125m-english-rtrvr` |

---

## G. Resume Parsing Workflow

### Flow

```
POST /api/v1/profiles/resume  (multipart/form-data)
  → validate file type (PDF or DOCX) and size (max 5MB)
  → save to temp storage
  → ResumeService.parse(file_path, mime_type)
      PDF  → pdfplumber.extract_text()
      DOCX → python-docx Document.paragraphs
  → raw_text cleaned (remove noise, page numbers)
  → WatsonxService.generate(EXTRACTION_PROMPT + raw_text)
      Granite extracts: skills[], education[], experience[], projects[]
      Returns structured JSON
  → store on CandidateProfile: resume_text, skills, education, experience, projects
  → set resume_parsed = True
  ← 200 { profile: CandidateProfile }
```

### Extraction Prompt

Granite is given the raw resume text and asked to return structured JSON with exactly: `skills`, `education`, `experience`, `projects`. The schema is explicit in the prompt to ensure parseable output.

### Error handling

- If Granite returns malformed JSON → log warning, store `resume_text` only, set `resume_parsed = False`
- Candidate can still proceed with manual profile (job_role + experience_level)

---

## H. Authentication Workflow

### Registration

```
POST /api/v1/auth/register { email, password, full_name }
  → validate email uniqueness
  → bcrypt hash password (rounds=12)
  → insert user row
  ← 201 { access_token, token_type: "bearer" }
```

### Login

```
POST /api/v1/auth/login { email, password }
  → lookup user by email
  → bcrypt verify
  → create JWT { sub: user_id, exp: now + 24h }
  ← 200 { access_token, token_type: "bearer" }
```

### Token Delivery

- Backend returns token in JSON response body
- Frontend stores token in httpOnly cookie via `Set-Cookie` header (not localStorage)
- Next.js middleware reads cookie and redirects unauthenticated users to `/auth/login`

### Protected Routes

FastAPI dependency `get_current_user` in `core/security.py`:
- Reads `Authorization: Bearer <token>` header
- Decodes JWT with `SECRET_KEY`
- Fetches user from DB, returns `User` model
- All protected route handlers accept `current_user: User = Depends(get_current_user)`

---

## I. API Endpoint List

Base URL: `http://localhost:8000/api/v1`

### Auth
| Method | Path | Body | Response | Auth |
|---|---|---|---|---|
| POST | `/auth/register` | `{email, password, full_name}` | `{access_token}` | No |
| POST | `/auth/login` | `{email, password}` | `{access_token}` | No |
| POST | `/auth/logout` | — | `204` | Yes |

### Profile
| Method | Path | Body | Response | Auth |
|---|---|---|---|---|
| GET | `/profiles/me` | — | `CandidateProfile` | Yes |
| PUT | `/profiles/me` | `{job_role, experience_level, skills}` | `CandidateProfile` | Yes |
| POST | `/profiles/resume` | `multipart: file` | `CandidateProfile` | Yes |

### Sessions
| Method | Path | Body | Response | Auth |
|---|---|---|---|---|
| POST | `/sessions` | `{interview_type, job_role}` | `{session_id, first_question}` | Yes |
| GET | `/sessions` | — | `[SessionSummary]` | Yes |
| GET | `/sessions/{id}` | — | `SessionDetail` | Yes |
| GET | `/sessions/{id}/status` | — | `{status}` | Yes |
| POST | `/sessions/{id}/complete` | — | `{status: "processing"}` | Yes |

### Answers
| Method | Path | Body | Response | Auth |
|---|---|---|---|---|
| POST | `/sessions/{id}/answers` | `{question_id, answer_text}` | `{quick_score, next_question}` | Yes |

### Reports
| Method | Path | Body | Response | Auth |
|---|---|---|---|---|
| GET | `/reports/{session_id}` | — | `PerformanceReport` | Yes |

---

## J. Agent Pipeline — Detailed Design

### `AgentContext` (TypedDict in `context.py`)

```python
class AgentContext(TypedDict, total=False):
    # Inputs set before pipeline starts
    session_id: str
    user_id: str
    interview_type: str          # "technical" | "hr" | "behavioral" | "mixed"
    job_role: str
    experience_level: str

    # Set by CandidateProfileAgent
    profile: dict                # serialized CandidateProfile

    # Set by ResumeAnalysisAgent
    resume_analysis: dict        # {skills, education, experience, projects, summary}

    # Set by InterviewPlanningAgent
    interview_plan: dict         # {categories: [], difficulties: [], question_count: 10}

    # Set by QuestionGenerationAgent
    questions: list[dict]        # [{question_text, question_type, difficulty, model_answer, rag_sources}]

    # Set incrementally during live session
    answers: list[dict]          # [{question_id, answer_text, quick_score}]

    # Set by AnswerEvaluationAgent (full run)
    evaluations: list[dict]      # [{accuracy, relevance, clarity, completeness, total, feedback}]

    # Set by FeedbackScoringAgent
    feedback: dict               # {per_question: [], skill_scores: {}, improvement_areas: []}

    # Set by PerformanceReportAgent
    report: dict                 # final report structure

    # Pipeline metadata
    errors: list[str]            # non-fatal errors collected during run
```

### Agent 1 — `CandidateProfileAgent`

- **Purpose**: Load candidate's profile from DB into context
- **Inputs**: `session_id`, `user_id`
- **Outputs**: `context["profile"]`
- **Granite used**: No
- **RAG used**: No
- **Responsibilities**: Fetch `CandidateProfile` row, serialize to dict, handle missing profile gracefully (use job_role from session)

### Agent 2 — `ResumeAnalysisAgent`

- **Purpose**: Summarize parsed resume into interview-relevant insights
- **Inputs**: `context["profile"]`
- **Outputs**: `context["resume_analysis"]`
- **Granite used**: Yes — generate a concise summary of strengths and gaps from resume fields
- **RAG used**: No
- **Responsibilities**: If `resume_parsed` is False, produce a minimal analysis from `job_role` + `experience_level` only. If parsed, use skills/experience/projects to generate a candidate summary and identify likely question areas.

### Agent 3 — `InterviewPlanningAgent`

- **Purpose**: Decide the question mix for this session
- **Inputs**: `context["resume_analysis"]`, `interview_type`, `experience_level`
- **Outputs**: `context["interview_plan"]`
- **Granite used**: Yes — determine question difficulty distribution and sub-categories
- **RAG used**: No
- **Responsibilities**: For a 10-question session, produce a plan: question types, difficulty levels (e.g. 3 easy, 5 medium, 2 hard), and sub-topic areas to cover (derived from resume gaps + interview_type).

### Agent 4 — `QuestionGenerationAgent`

- **Purpose**: Generate the 10 interview questions with model answers
- **Inputs**: `context["interview_plan"]`, `context["resume_analysis"]`, `job_role`
- **Outputs**: `context["questions"]` (list of 10 question dicts)
- **Granite used**: Yes — generate questions + model answers
- **RAG used**: Yes — retrieve role-specific knowledge BEFORE calling Granite
- **Responsibilities**:
  1. For each planned question slot, call `RAGService.retrieve(query, metadata_filter={role, type})`
  2. Inject retrieved chunks into Granite prompt
  3. Parse Granite JSON output into question dicts
  4. Persist all 10 `Question` rows to DB immediately
  5. Store `rag_sources` (chunk IDs) on each question for auditability

### Agent 5 — `AnswerEvaluationAgent`

- **Purpose**: Score all candidate answers on the 4-dimension rubric
- **Inputs**: `context["questions"]`, `context["answers"]`
- **Outputs**: `context["evaluations"]`
- **Granite used**: Yes — one Granite call per answer with scoring rubric
- **RAG used**: Optional — retrieve model answer context for borderline cases
- **Responsibilities**: For each answer, produce scores for Accuracy (0–25), Relevance (0–25), Clarity (0–25), Completeness (0–25). Total = sum. Update `Answer` rows in DB with dimension scores.
- **Note**: `quick_score` was already set during the live session; this agent adds the 4 detailed dimension scores.

### Agent 6 — `FeedbackScoringAgent`

- **Purpose**: Synthesize per-answer feedback and skill-level assessment
- **Inputs**: `context["evaluations"]`, `context["resume_analysis"]`, `context["questions"]`
- **Outputs**: `context["feedback"]`
- **Granite used**: Yes — generate per-answer improvement tips and skill area summaries
- **RAG used**: No
- **Responsibilities**:
  - Per answer: generate one specific improvement tip (written directly to candidate)
  - Aggregate: compute skill-area scores (Technical Knowledge, Communication, Problem Solving, Domain Knowledge)
  - Identify top 3 improvement areas with actionable advice
  - Update `Answer` rows with `feedback_text` and `improvement_tip`

### Agent 7 — `PerformanceReportAgent`

- **Purpose**: Assemble the final report data structure
- **Inputs**: All prior context keys
- **Outputs**: `context["report"]`
- **Granite used**: Yes — generate executive summary paragraph (3–5 sentences)
- **RAG used**: No
- **Responsibilities**:
  - Calculate overall score (average of all `answer.total_score`)
  - Compose radar chart data (4 dimensions aggregated)
  - List question-by-question review (question, answer, score, model_answer, tip)
  - Generate strengths (top 2 performing areas) and weaknesses (bottom 2)
  - Write executive summary via Granite
  - Serialize full report to `interview_sessions.pipeline_context` and `status = "complete"`

---

## K. Complete Folder Structure

```
InterviewPro-AI/
├── AGENTS.md
├── interviewpro-plan.md
├── README.md
├── .gitignore
│
├── knowledge_base/
│   ├── technical/
│   │   ├── software_engineer.md
│   │   ├── data_scientist.md
│   │   ├── devops_engineer.md
│   │   └── frontend_developer.md
│   ├── behavioral/
│   │   ├── star_method_scenarios.md
│   │   └── common_behavioral_questions.md
│   ├── hr/
│   │   ├── hr_interview_guidelines.md
│   │   └── salary_negotiation.md
│   └── industry/
│       ├── expectations_fresher.md
│       └── expectations_senior.md
│
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── db.py
│   │   │   └── security.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── candidate_profile.py
│   │   │   ├── interview_session.py
│   │   │   ├── question.py
│   │   │   ├── answer.py
│   │   │   └── document_embedding.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── profile.py
│   │   │   ├── session.py
│   │   │   ├── question.py
│   │   │   ├── answer.py
│   │   │   └── report.py
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── context.py
│   │   │   ├── orchestrator.py
│   │   │   ├── candidate_profile_agent.py
│   │   │   ├── resume_analysis_agent.py
│   │   │   ├── interview_planning_agent.py
│   │   │   ├── question_generation_agent.py
│   │   │   ├── answer_evaluation_agent.py
│   │   │   ├── feedback_scoring_agent.py
│   │   │   └── performance_report_agent.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── watsonx_service.py
│   │   │   ├── rag_service.py
│   │   │   ├── rag_ingest.py
│   │   │   ├── resume_service.py
│   │   │   └── session_service.py
│   │   └── api/
│   │       └── v1/
│   │           ├── __init__.py
│   │           ├── auth.py
│   │           ├── profiles.py
│   │           ├── sessions.py
│   │           ├── answers.py
│   │           └── reports.py
│   └── tests/
│       ├── conftest.py
│       ├── test_agents/
│       │   ├── test_candidate_profile_agent.py
│       │   ├── test_resume_analysis_agent.py
│       │   ├── test_question_generation_agent.py
│       │   ├── test_answer_evaluation_agent.py
│       │   └── test_performance_report_agent.py
│       ├── test_api/
│       │   ├── test_auth.py
│       │   ├── test_sessions.py
│       │   └── test_reports.py
│       └── test_services/
│           ├── test_rag_service.py
│           └── test_resume_service.py
│
└── frontend/
    ├── .env.example
    ├── .env.local              # gitignored
    ├── package.json
    ├── tsconfig.json
    ├── tailwind.config.ts
    ├── next.config.ts
    ├── middleware.ts            # Auth guard
    └── src/
        ├── app/
        │   ├── layout.tsx
        │   ├── page.tsx         # Landing
        │   ├── (auth)/
        │   │   ├── login/page.tsx
        │   │   └── register/page.tsx
        │   ├── dashboard/page.tsx
        │   ├── profile/page.tsx
        │   ├── interview/
        │   │   ├── setup/page.tsx
        │   │   └── [sessionId]/page.tsx
        │   └── report/
        │       └── [sessionId]/page.tsx
        ├── components/
        │   ├── ui/
        │   ├── interview/
        │   ├── report/
        │   └── profile/
        ├── lib/
        │   ├── api-client.ts
        │   ├── auth.ts
        │   └── types.ts
        └── hooks/
            ├── useSession.ts
            └── useAuth.ts
```

---

## L. Environment Variables

### `backend/.env.example`

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/interviewpro

# JWT
SECRET_KEY=change-this-to-a-random-256-bit-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# IBM Granite / watsonx.ai
WATSONX_API_KEY=your-ibm-cloud-api-key
WATSONX_PROJECT_ID=your-watsonx-project-id
WATSONX_URL=https://us-south.ml.cloud.ibm.com

# Granite model IDs (defaults shown)
GRANITE_MODEL_ID=ibm/granite-13b-instruct-v2
GRANITE_EMBEDDING_MODEL=ibm/slate-125m-english-rtrvr

# CORS
FRONTEND_URL=http://localhost:3000

# App
DEBUG=true
LOG_LEVEL=INFO

# Test DB (used only in pytest)
TEST_DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/interviewpro_test
```

### `frontend/.env.example`

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## M. Error Handling

### Backend

- All FastAPI route handlers are wrapped in try/except; return structured `{"detail": "..."}` errors
- `WatsonxService.generate()` retries 3× on 429; raises `WatsonxUnavailableError` after exhausted retries
- `WatsonxService.generate()` validates JSON output; raises `WatsonxParseError` on malformed response
- Agent pipeline: individual agent failures are caught by orchestrator, stored in `context["errors"]`, and the pipeline continues with degraded output where possible
- Session status is set to `"failed"` only if a critical agent (QuestionGeneration, AnswerEvaluation, PerformanceReport) fails unrecoverably
- Resume parsing failure: non-fatal — sets `resume_parsed = False`, profile continues without extracted data

### Frontend

- API errors: `api-client.ts` throws typed `ApiError` objects with `status` and `message`
- Interview page: if polling returns `status === "failed"`, display error state with retry option
- Form validation: client-side only for UX; server-side Pydantic validation is the source of truth

---

## N. Security Considerations

- IBM credentials (`WATSONX_API_KEY`, `WATSONX_PROJECT_ID`) live in backend `.env` only — never in frontend env or version control
- Passwords: bcrypt with 12 rounds minimum
- JWT: `SECRET_KEY` minimum 256 bits random; store in env only; never log
- JWT tokens: httpOnly cookie prevents XSS access; `SameSite=Lax` prevents CSRF
- File uploads: validate MIME type server-side (not just extension); enforce 5MB size limit; store in temp dir, delete after parsing
- CORS: only `FRONTEND_URL` is allowed origin in `main.py`; no wildcard `*` in production
- SQL injection: SQLAlchemy ORM only — no raw string interpolation in queries
- Rate limiting: apply to `/auth/login` and `/auth/register` endpoints (use `slowapi`)
- Input sanitization: all text inputs passed to Granite are length-limited before prompt construction

---

## O. Testing Strategy

### Backend

| Test Type | Tool | Scope |
|---|---|---|
| Unit — agents | pytest + pytest-mock | Each agent in isolation; Granite mocked |
| Unit — services | pytest | RAGService, ResumeService (no live DB needed) |
| Integration — API | pytest + httpx AsyncClient | Full request/response; test DB |
| Integration — pipeline | pytest + pytest-mock | Full orchestrator run; Granite mocked |

**Key fixture** (`conftest.py`):
- `mock_watsonx` — patches `WatsonxService.generate` and `WatsonxService.embed` with deterministic return values
- `test_db` — uses `TEST_DATABASE_URL`; creates/drops schema per test session
- `auth_headers` — creates a test user and returns `Authorization: Bearer <token>`

### Frontend

- Jest + React Testing Library
- Test: form submission, error states, polling behavior (`useSession` hook)
- No tests make real API calls — use `msw` (Mock Service Worker) to intercept fetch

---

## P. Local Development Setup

```bash
# 1. Clone and enter project
cd InterviewPro-AI

# 2. Start PostgreSQL with pgvector
docker run -d \
  --name interviewpro-db \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=interviewpro \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# 3. Backend setup
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env           # Fill in IBM credentials
alembic upgrade head           # Create tables

# 4. Seed RAG knowledge base (required before first use)
python -m app.services.rag_ingest

# 5. Run backend
uvicorn app.main:app --reload

# 6. Frontend setup (new terminal)
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

---

## Q. Deployment Strategy

### Independent deployments

| Service | Target |
|---|---|
| Frontend | Vercel (recommended) or any static host supporting Next.js |
| Backend | Railway, Render, or any container host |
| Database | Supabase (PostgreSQL + pgvector built-in) or Railway PostgreSQL |

### Environment separation

- Frontend: only `NEXT_PUBLIC_API_URL` changes between dev and prod
- Backend: all env vars change; IBM credentials stay backend-only always
- Database: production DB URL in backend env only; run `alembic upgrade head` before each deploy

### Containerization (optional for demo)

A single `docker-compose.yml` at project root can start all three services for local demo:
- `db`: pgvector/pgvector:pg16
- `backend`: Dockerfile in `backend/`
- `frontend`: Dockerfile in `frontend/`

---

## R. Demo Workflow for an Evaluator

1. **Register** — Create account at `/auth/register`
2. **Build Profile** — Enter job role (e.g. "Software Engineer"), experience level (e.g. "fresher")
3. **Upload Resume** — Upload a PDF/DOCX; wait for "Profile updated with resume data" confirmation
4. **Start Interview** — Go to `/interview/setup`, select "Technical", click Start
5. **Answer Questions** — Answer 10 questions (text input); quick score badge appears after each
6. **Complete Session** — Click "Finish Interview"; status shows "Processing your results..."
7. **View Report** — System polls and redirects to `/report/{id}` showing:
   - Overall score (0–100)
   - Radar chart (Accuracy / Relevance / Clarity / Completeness)
   - Per-question review with model answer and improvement tip
   - Top 3 improvement areas
   - Executive summary paragraph
8. **Show Pipeline** — Evaluator can inspect FastAPI `/docs` (Swagger UI) to see all 7 agent steps logged

---

## S. AICTE PS22 Requirement-to-Feature Mapping

| PS22 Requirement | Feature in InterviewPro AI |
|---|---|
| Candidate profile creation | `CandidateProfileAgent` + `/profiles/me` endpoint |
| Resume analysis | `ResumeAnalysisAgent` + `ResumeService` (PDF/DOCX → Granite extraction) |
| Job role + experience personalization | `InterviewPlanningAgent` uses role + level to plan question mix |
| Technical, HR, Behavioral, Role-specific questions | `QuestionGenerationAgent` + RAG by category + interview_type selection |
| Industry expectations | `knowledge_base/industry/` RAG docs injected at question generation |
| Model answers | Granite generates model answer for each question; shown in final report |
| Interactive mock interview | 10-question session with text input loop on `/interview/[sessionId]` |
| Answer evaluation | `AnswerEvaluationAgent` — 4-dimension rubric (Accuracy, Relevance, Clarity, Completeness) |
| Technical skill assessment | Technical score aggregated from technical-type questions |
| Soft-skill assessment | Communication + behavioral dimension scores |
| Personalized improvement tips | `FeedbackScoringAgent` — per-answer tips + top 3 improvement areas |
| Final interview performance report | `PerformanceReportAgent` + `/reports/{session_id}` + radar chart |
| RAG-based knowledge retrieval | `RAGService` (pgvector ANN search) before every question generation |
| IBM Granite via watsonx.ai | `WatsonxService` used by 5 of 7 agents; mandatory, no fallback to other LLMs |
| Multi-agent workflow | 7-agent sequential pipeline via `Orchestrator` + `AgentContext` |

---

## Implementation Sub-Tasks

Each sub-task is designed to be implemented independently and sequentially.

### Phase 1 — Foundation

- [x] **ST-01** Project scaffolding: directory structure, `.gitignore`, `README.md`, `requirements.txt`, `package.json`
- [x] **ST-02** Backend core: `config.py`, `db.py`, `security.py`, SQLAlchemy models, Alembic setup + initial migration
- [x] **ST-03** Authentication API: register/login/logout endpoints + JWT + bcrypt
- [ ] **ST-04** Frontend foundation: Next.js init, Tailwind config, `api-client.ts`, `types.ts`, auth pages + middleware

### Phase 2 — Data Layer

- [ ] **ST-05** Candidate profile API: GET/PUT profile endpoint + resume upload endpoint + `ResumeService`
- [x] **ST-06** Knowledge base seed documents: 10 Markdown files committed across all categories (done in ST-01)
- [ ] **ST-07** RAG infrastructure: `WatsonxService` (embed method), `rag_ingest.py`, `rag_service.py`, pgvector index

### Phase 3 — Agent Pipeline

- [ ] **ST-08** `AgentContext` TypedDict + `Orchestrator` skeleton (empty pipeline)
- [ ] **ST-09** `CandidateProfileAgent` + `ResumeAnalysisAgent` (Granite summary)
- [ ] **ST-10** `InterviewPlanningAgent` (Granite question mix) + `QuestionGenerationAgent` (RAG + Granite)
- [ ] **ST-11** Session API: `POST /sessions` (runs agents 1–4, returns first question) + `GET /sessions/{id}/status`
- [ ] **ST-12** Quick answer evaluation: `POST /sessions/{id}/answers` → immediate Granite scoring → returns quick_score + next question
- [ ] **ST-13** Full pipeline: `POST /sessions/{id}/complete` → background task running agents 5–7 → updates session status

### Phase 4 — Report & Frontend

- [ ] **ST-14** `AnswerEvaluationAgent` + `FeedbackScoringAgent` + `PerformanceReportAgent`
- [ ] **ST-15** Report API: `GET /reports/{session_id}` → serialized report JSON
- [ ] **ST-16** Frontend: profile page + resume upload UI
- [ ] **ST-17** Frontend: interview setup + live interview page (Q&A loop + polling + quick score display)
- [ ] **ST-18** Frontend: performance report page (radar chart + question review + tips)

### Phase 5 — Quality

- [ ] **ST-19** Backend tests: agent unit tests with mocked Granite, API integration tests
- [ ] **ST-20** Frontend tests: key component and hook tests with MSW
- [ ] **ST-21** `docker-compose.yml` for local demo + `README.md` setup instructions
