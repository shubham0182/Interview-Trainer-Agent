"""
WatsonxService — IBM Granite wrapper.

All LLM calls in the application go through this service.
Agents NEVER import ibm_watsonx_ai directly.
Implemented fully in ST-07.
"""


class WatsonxService:
    """
    Wraps ibm_watsonx_ai SDK.

    Methods:
        generate(prompt, params) -> str
        embed(text) -> list[float]

    Implemented in ST-07.
    """

    async def generate(self, prompt: str, **kwargs: object) -> str:
        raise NotImplementedError("WatsonxService implemented in ST-07")

    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError("WatsonxService implemented in ST-07")
