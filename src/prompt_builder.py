from pathlib import Path
from src.excel_reader import read_manual

_PROJECT_ROOT = Path(__file__).parent.parent
_PROMPT_PATH = _PROJECT_ROOT / "prompt.txt"


def load_system_prompt():
    if not _PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró {_PROMPT_PATH.name} en la raíz del proyecto"
        )
    return _PROMPT_PATH.read_text(encoding="utf-8")


def build_system_message():
    base_prompt = load_system_prompt()

    try:
        manual_text = read_manual()
        system_content = (
            f"{base_prompt}\n\n"
            f"--- MANUAL DE CLASIFICACIÓN CIUO.08CL ---\n\n"
            f"{manual_text}"
        )
    except FileNotFoundError:
        system_content = base_prompt

    return {"role": "system", "content": system_content}


def build_user_message(batch):
    items = "\n".join(
        [f"ID: {item['id']}\nGlosa: {item['glosa']}" for item in batch]
    )
    user_content = (
        "Clasifica las siguientes descripciones ocupacionales según CIUO.08CL.\n\n"
        f"{items}\n\n"
        "Responde ÚNICAMENTE con un array JSON en este formato exacto:\n"
        '[\n'
        '  {"id": "<id>", "gran_grupo": "<1 dígito>",'
        ' "subgrupo_principal": "<2 dígitos>",'
        ' "subgrupo": "<3 dígitos>",'
        ' "grupo_primario": "<4 dígitos>"}\n'
        ']\n\n'
        'Usa "99" para cualquier nivel donde no tengas suficiente información.'
    )
    return {"role": "user", "content": user_content}
