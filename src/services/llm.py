import httpx


class LLMService:

    def __init__(self, ollama_url: str, model: str):
        self.ollama_url = ollama_url
        self.model = model

    async def generate(
        self,
        messages: list[dict],
        model: str = None,
    ) -> str:

        payload = {
            "model": model or self.model,
            "messages": messages,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.post(
                f"{self.ollama_url}/api/chat",
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

            return data["message"]["content"]

    async def generateTitle(self, query: str):
        query = query[:500]

        prompt = f"""
        Generate a concise, meaningful title for this conversation.

        User's message:
        {query}

        The title should represent the broader topic, theme, or intent of the conversation,
        not simply repeat or paraphrase the user's question.

        Think of the title as a name for the conversation that would still make sense
        if the user continues discussing related ideas, questions, and topics later.

        Rules:
        - Must be in English
        - 2 to 5 words
        - Maximum 40 characters
        - Capture the broader topic or theme
        - Make it natural and human-friendly
        - Prefer a conceptual topic over a specific question
        - Do not copy or paraphrase the user's query
        - Avoid generic titles like "New Conversation", "Chat", or "Question"
        - Return only the title
        """

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0,
                "num_predict": 10,
            },
        }

        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.post(
                f"{self.ollama_url}/api/chat",
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

            return data["message"]["content"].strip()
