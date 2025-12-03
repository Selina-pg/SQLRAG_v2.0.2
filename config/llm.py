import os

LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "Qwen/Qwen2.5-VL-32B-Instruct")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://10.13.18.40:2266/v1")
# LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "openai/gpt-oss-20b")
# LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://10.13.18.40:8964/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "none")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))