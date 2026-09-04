"""AnswerEvaluationAgent — 4-dimension scoring. Implemented in ST-14."""
from app.agents.context import AgentContext


class AnswerEvaluationAgent:
    """Scores answers on Accuracy/Relevance/Clarity/Completeness. Implemented in ST-14."""

    async def run(self, context: AgentContext) -> AgentContext:
        raise NotImplementedError("AnswerEvaluationAgent implemented in ST-14")
