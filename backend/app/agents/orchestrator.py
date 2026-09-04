"""
Agent pipeline orchestrator.

Chains the 7 agents sequentially, passing AgentContext through each.
If a non-critical agent fails, the error is recorded and the pipeline continues.
If a critical agent fails, the session is marked failed and the pipeline stops.

CRITICAL agents: QuestionGenerationAgent, AnswerEvaluationAgent, PerformanceReportAgent
NON-CRITICAL agents: ResumeAnalysisAgent, InterviewPlanningAgent, FeedbackScoringAgent
"""
import logging

from app.agents.context import AgentContext

logger = logging.getLogger(__name__)

# ── Agent imports (uncommented as each agent is implemented) ──────────────────
# from app.agents.candidate_profile_agent import CandidateProfileAgent
# from app.agents.resume_analysis_agent import ResumeAnalysisAgent
# from app.agents.interview_planning_agent import InterviewPlanningAgent
# from app.agents.question_generation_agent import QuestionGenerationAgent
# from app.agents.answer_evaluation_agent import AnswerEvaluationAgent
# from app.agents.feedback_scoring_agent import FeedbackScoringAgent
# from app.agents.performance_report_agent import PerformanceReportAgent

CRITICAL_AGENTS = {
    "QuestionGenerationAgent",
    "AnswerEvaluationAgent",
    "PerformanceReportAgent",
}


async def run_pipeline(context: AgentContext) -> AgentContext:
    """
    Run the full 7-agent pipeline.

    Agents are added here as they are implemented in later sub-tasks.
    Returns the final AgentContext with all agent outputs populated.
    """
    if "errors" not in context:
        context["errors"] = []

    # Pipeline registration — uncomment as each agent is implemented
    agents: list = [
        # CandidateProfileAgent(),
        # ResumeAnalysisAgent(),
        # InterviewPlanningAgent(),
        # QuestionGenerationAgent(),
        # AnswerEvaluationAgent(),
        # FeedbackScoringAgent(),
        # PerformanceReportAgent(),
    ]

    for agent in agents:
        agent_name = type(agent).__name__
        try:
            logger.info("Running agent: %s", agent_name)
            context = await agent.run(context)
            logger.info("Agent %s completed successfully", agent_name)
        except Exception as exc:
            logger.exception("Agent %s raised an exception: %s", agent_name, exc)
            context["errors"].append(f"{agent_name}: {exc!s}")
            if agent_name in CRITICAL_AGENTS:
                raise RuntimeError(
                    f"Critical agent {agent_name} failed: {exc}"
                ) from exc

    return context
