from openai import OpenAI
from config import LLM_MODEL_NAME, LLM_BASE_URL, LLM_API_KEY, LLM_TEMPERATURE
import asyncio

class OpenAIClient:
    def __init__(self):
        self.model_name = LLM_MODEL_NAME
        self.temperature = LLM_TEMPERATURE
        self.client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)

    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        try:
            resp = await asyncio.to_thread(
                lambda: self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.temperature,
                )
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return f"ERROR_CALLING_LLM::{type(e).__name__}:{e}"