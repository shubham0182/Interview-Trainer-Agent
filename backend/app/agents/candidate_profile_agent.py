"""CandidateProfileAgent — loads candidate profile. Implemented in ST-09."""
from app.agents.context import AgentContext


class CandidateProfileAgent:
    """Loads the candidate's profile from DB into AgentContext. Implemented in ST-09."""

    async def run(self, context: AgentContext) -> AgentContext:
        raise NotImplementedError("CandidateProfileAgent implemented in ST-09")
