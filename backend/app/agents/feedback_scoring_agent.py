"""FeedbackScoringAgent — per-answer tips and skill scores. Implemented in ST-14."""
from app.agents.context import AgentContext


class FeedbackScoringAgent:
    """Generates per-answer improvement tips and skill-area scores. Implemented in ST-14."""

    async def run(self, context: AgentContext) -> AgentContext:
        raise NotImplementedError("FeedbackScoringAgent implemented in ST-14")
