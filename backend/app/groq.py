import base64

import httpx

from .config import settings


GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


async def chat_completion(messages: list[dict], model: str | None = None) -> str:
    if not settings.groq_api_key:
        return "GROQ_API_KEY is not set. Add it to backend/.env or docker-compose.yml."

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json={
                "model": model or settings.groq_model,
                "messages": messages,
                "temperature": 0.4,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def analyze_image(image_bytes: bytes, mime_type: str, prompt: str) -> str:
    encoded = base64.b64encode(image_bytes).decode()
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{encoded}"},
                },
            ],
        }
    ]
    return await chat_completion(messages, model=settings.groq_vision_model)

