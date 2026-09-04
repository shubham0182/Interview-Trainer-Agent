"""QuestionGenerationAgent — RAG + Granite question generation. Implemented in ST-10."""
from app.agents.context import AgentContext


class QuestionGenerationAgent:
    """Generates 10 interview questions using RAG retrieval + IBM Granite. Implemented in ST-10."""

    async def run(self, context: AgentContext) -> AgentContext:
        raise NotImplementedError("QuestionGenerationAgent implemented in ST-10")
