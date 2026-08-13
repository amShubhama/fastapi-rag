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
