"""
AgentContext TypedDict — the shared state object passed through the pipeline.

Every agent accepts an AgentContext and returns an AgentContext.
Agents write to their own key(s) only; they never mutate other agents' keys.
"""
from typing import Any, TypedDict


class AgentContext(TypedDict, total=False):
    # ── Inputs set before pipeline starts ────────────────────────────────────
    session_id: str
    user_id: str
    interview_type: str          # "technical" | "hr" | "behavioral" | "mixed"
    job_role: str
    experience_level: str        # "fresher" | "junior" | "mid" | "senior"

    # ── Set by CandidateProfileAgent ─────────────────────────────────────────
    profile: dict[str, Any]

    # ── Set by ResumeAnalysisAgent ────────────────────────────────────────────
    resume_analysis: dict[str, Any]
    # Keys: skills, education, experience, projects, summary, identified_gaps

    # ── Set by InterviewPlanningAgent ─────────────────────────────────────────
    interview_plan: dict[str, Any]
    # Keys: categories, difficulties, question_count, sub_topics

    # ── Set by QuestionGenerationAgent ───────────────────────────────────────
    questions: list[dict[str, Any]]
    # Each: {question_text, question_type, difficulty, model_answer, rag_sources}

    # ── Set incrementally during the live session ─────────────────────────────
    answers: list[dict[str, Any]]
    # Each: {question_id, answer_text, quick_score}

    # ── Set by AnswerEvaluationAgent (full pipeline run) ─────────────────────
    evaluations: list[dict[str, Any]]
    # Each: {question_id, accuracy, relevance, clarity, completeness, total, feedback}

    # ── Set by FeedbackScoringAgent ───────────────────────────────────────────
    feedback: dict[str, Any]
    # Keys: per_question (list), skill_scores (dict), improvement_areas (list)

    # ── Set by PerformanceReportAgent ─────────────────────────────────────────
    report: dict[str, Any]
    # Keys: overall_score, radar_data, question_review, strengths, weaknesses, summary

    # ── Pipeline metadata ─────────────────────────────────────────────────────
    errors: list[str]            # Non-fatal errors collected during the run
