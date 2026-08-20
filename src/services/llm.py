import httpx
from src.static.prompts import TITLE_SYSTEM_PROMPT


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
            "keep_alive": "10m",
        }

        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.post(
                f"{self.ollama_url}/api/chat",
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

            return data["message"]["content"]

    async def generateTitle(
        self,
        query: str,
    ) -> str:

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": TITLE_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": query,
                },
            ],
            "stream": False,
            "think": False,
            "keep_alive": "10m",
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
