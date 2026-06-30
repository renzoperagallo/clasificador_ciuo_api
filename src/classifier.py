import json
import re
import sys
from src.api_client import chat_completion
from src.prompt_builder import build_system_message, build_user_message
from src.config import BATCH_SIZE, MODEL_NAME


def _extract_json(content):
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
    if match:
        content = match.group(1)

    start = content.find("[")
    end = content.rfind("]")
    if start != -1 and end != -1:
        content = content[start:end + 1]

    return json.loads(content)


def _fallback_result(item):
    return {
        "id": item["id"],
        "glosa": item["glosa"],
        "gran_grupo": "99",
        "subgrupo_principal": "99",
        "subgrupo": "99",
        "grupo_primario": "99",
    }


def _parse_batch_response(response_content, batch):
    classified = _extract_json(response_content)
    class_map = {item["id"]: item for item in classified}

    results = []
    for item in batch:
        if item["id"] in class_map:
            result = class_map[item["id"]]
            results.append({
                "id": item["id"],
                "glosa": item["glosa"],
                "gran_grupo": result.get("gran_grupo", "99"),
                "subgrupo_principal": result.get("subgrupo_principal", "99"),
                "subgrupo": result.get("subgrupo", "99"),
                "grupo_primario": result.get("grupo_primario", "99"),
            })
        else:
            results.append(_fallback_result(item))
    return results


def classify_csv(input_path, output_path, model=None, batch_size=None):
    model = model or MODEL_NAME
    batch_size = batch_size or BATCH_SIZE

    from src.csv_handler import read_input, write_output

    rows = read_input(input_path)
    if not rows:
        print("Error: El archivo CSV de entrada está vacío", file=sys.stderr)
        return

    system_message = build_system_message()

    batches = [rows[i:i + batch_size] for i in range(0, len(rows), batch_size)]
    all_results = []

    for batch_idx, batch in enumerate(batches):
        print(
            f"Procesando lote {batch_idx + 1}/{len(batches)} "
            f"({len(batch)} glosas)..."
        )

        user_message = build_user_message(batch)
        messages = [system_message, user_message]

        try:
            response = chat_completion(messages, model=model)
            batch_results = _parse_batch_response(response, batch)
            all_results.extend(batch_results)
        except Exception as e:
            print(
                f"Error en lote {batch_idx + 1}: {e}. "
                f"Clasificando como '99'...",
                file=sys.stderr,
            )
            for item in batch:
                all_results.append(_fallback_result(item))

    write_output(output_path, all_results)
    print(f"Clasificación completada. Resultados guardados en: {output_path}")
    print(f"Total de glosas procesadas: {len(all_results)}")
