import time
from openai import OpenAI
from src.config import (
    API_BASE_URL,
    API_KEY,
    MODEL_NAME,
    TEMPERATURE,
    MAX_TOKENS,
    MAX_RETRIES,
    REQUEST_TIMEOUT,
)


def _create_client():
    return OpenAI(
        base_url=API_BASE_URL,
        api_key=API_KEY,
        timeout=REQUEST_TIMEOUT,
        max_retries=0,
    )


def chat_completion(messages, model=None, temperature=None, max_tokens=None):
    client = _create_client()
    model = model or MODEL_NAME
    temperature = temperature if temperature is not None else TEMPERATURE
    max_tokens = max_tokens or MAX_TOKENS

    last_exception = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            usage = response.usage
            return {
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens if usage else 0,
                    "completion_tokens": usage.completion_tokens if usage else 0,
                    "total_tokens": usage.total_tokens if usage else 0,
                },
            }
        except Exception as e:
            last_exception = e
            if attempt < MAX_RETRIES:
                wait = 2 ** attempt
                time.sleep(wait)

    raise last_exception
