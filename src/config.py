import os
from pathlib import Path
from dotenv import load_dotenv

_project_root = Path(__file__).parent.parent
load_dotenv(_project_root / ".env")

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
API_KEY = os.getenv("API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "1800"))


def validate():
    errors = []
    if not API_KEY:
        errors.append("API_KEY no está definida en el archivo .env")
    if not API_BASE_URL:
        errors.append("API_BASE_URL no está definida en el archivo .env")
    if errors:
        raise ValueError("\n".join(errors))


def to_dict():
    return {
        "API_BASE_URL": API_BASE_URL,
        "MODEL_NAME": MODEL_NAME,
        "TEMPERATURE": TEMPERATURE,
        "MAX_TOKENS": MAX_TOKENS,
        "BATCH_SIZE": BATCH_SIZE,
        "MAX_RETRIES": MAX_RETRIES,
        "REQUEST_TIMEOUT": REQUEST_TIMEOUT,
    }
