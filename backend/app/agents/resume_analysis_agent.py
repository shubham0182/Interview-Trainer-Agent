"""ResumeAnalysisAgent — Granite resume summary. Implemented in ST-09."""
from app.agents.context import AgentContext


class ResumeAnalysisAgent:
    """Generates a candidate summary from parsed resume. Implemented in ST-09."""

    async def run(self, context: AgentContext) -> AgentContext:
        raise NotImplementedError("ResumeAnalysisAgent implemented in ST-09")
