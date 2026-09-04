"""PerformanceReportAgent — final report assembly. Implemented in ST-14."""
from app.agents.context import AgentContext


class PerformanceReportAgent:
    """Assembles the final performance report. Implemented in ST-14."""

    async def run(self, context: AgentContext) -> AgentContext:
        raise NotImplementedError("PerformanceReportAgent implemented in ST-14")
