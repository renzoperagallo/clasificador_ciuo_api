import json
import re
import sys
import time
from src.api_client import chat_completion
from src.prompt_builder import build_system_message, build_user_message
from src.config import BATCH_SIZE, MAX_RETRIES, MODEL_NAME
from src.checkpoint import save as save_checkpoint
from src.checkpoint import load as load_checkpoint
from src.checkpoint import clear as clear_checkpoint


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


def _fmt_time(seconds):
    if seconds < 60:
        return f"{seconds:.0f}s"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def _fmt_tokens(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def classify_csv(input_path, output_path, model=None, batch_size=None,
                 resume=False):
    model = model or MODEL_NAME
    batch_size = batch_size or BATCH_SIZE

    from src.csv_handler import read_input, read_output, write_output

    print(f"Leyendo {input_path}...")
    rows = read_input(input_path)
    total = len(rows)
    print(f"  {total} glosas cargadas.")
    if not rows:
        print("Error: El archivo CSV de entrada está vacío", file=sys.stderr)
        return

    all_results = []
    stats = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "batches_ok": 0,
        "batches_fallback_99": 0,
    }
    start_time = time.time()

    if resume:
        cp = load_checkpoint()
        if cp and cp.get("input_file") == input_path:
            try:
                all_results = read_output(output_path)
                expected = cp["processed"]
                if len(all_results) >= expected:
                    all_results = all_results[:expected]
                stats = cp.get("stats", stats)
                start_time -= cp.get("elapsed", 0)
                elapsed_str = _fmt_time(cp.get("elapsed", 0))
                print(f"Reanudando: {len(all_results)}/{total} glosas ya "
                      f"clasificadas ({len(all_results)/total*100:.1f}%) | "
                      f"Tiempo previo: {elapsed_str}")
            except FileNotFoundError:
                clear_checkpoint()
                print("Checkpoint inconsistente, iniciando desde cero.",
                      file=sys.stderr)
        else:
            print("No se encontró checkpoint válido. Iniciando desde cero.",
                  file=sys.stderr)

    processed_before = len(all_results)
    if processed_before >= total:
        print("Todas las glosas ya están clasificadas.")
        clear_checkpoint()
        return

    remaining = rows[processed_before:]
    batches = [remaining[i:i + batch_size]
               for i in range(0, len(remaining), batch_size)]

    system_message = build_system_message()
    total_batches = (total + batch_size - 1) // batch_size

    for batch_idx, batch in enumerate(batches):
        batch_num = (processed_before // batch_size) + batch_idx + 1
        batch_start = time.time()

        user_message = build_user_message(batch)
        messages = [system_message, user_message]

        api_response = None
        retry_wait = 2
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                api_response = chat_completion(messages, model=model)
                break
            except Exception as e:
                if attempt < MAX_RETRIES:
                    print(f"  Reintento {attempt}/{MAX_RETRIES} en "
                          f"{retry_wait}s: {type(e).__name__}", flush=True)
                    time.sleep(retry_wait)
                    retry_wait *= 2
                else:
                    print(f"  ERROR tras {MAX_RETRIES} intentos: "
                          f"{type(e).__name__}", file=sys.stderr)

        if api_response is not None:
            try:
                batch_results = _parse_batch_response(
                    api_response["content"], batch
                )
                all_results.extend(batch_results)
                stats["batches_ok"] += 1
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"  Error parseando JSON: {e}. Marcando como '99'...",
                      file=sys.stderr)
                for item in batch:
                    all_results.append(_fallback_result(item))
                stats["batches_fallback_99"] += 1

            usage = api_response.get("usage", {})
            stats["prompt_tokens"] += usage.get("prompt_tokens", 0)
            stats["completion_tokens"] += usage.get("completion_tokens", 0)
            stats["total_tokens"] += usage.get("total_tokens", 0)
        else:
            elapsed_total = time.time() - start_time
            write_output(output_path, all_results)
            save_checkpoint(
                processed=len(all_results),
                total=total,
                input_file=input_path,
                output_file=output_path,
                batch_size=batch_size,
                elapsed=elapsed_total,
                stats=stats,
            )
            print(
                f"\nERROR: API no respondió tras {MAX_RETRIES} intentos "
                f"en lote {batch_num}/{total_batches}.",
                file=sys.stderr,
            )
            print(
                f"Progreso guardado: {len(all_results)}/{total} glosas "
                f"({len(all_results)/total*100:.1f}%).",
                file=sys.stderr,
            )
            print(
                "Ejecuta nuevamente con --resume para continuar.",
                file=sys.stderr,
            )
            return

        progress = len(all_results)

        elapsed_total = time.time() - start_time
        write_output(output_path, all_results)
        save_checkpoint(
            processed=progress,
            total=total,
            input_file=input_path,
            output_file=output_path,
            batch_size=batch_size,
            elapsed=elapsed_total,
            stats=stats,
        )

        batch_time = time.time() - batch_start
        tok_count = _fmt_tokens(
            api_response.get("usage", {}).get("total_tokens", 0)
        ) if api_response else "N/A"

        eta_str = ""
        if progress > 0 and progress < total:
            rate_ips = progress / elapsed_total if elapsed_total > 0 else 0
            eta_s = (total - progress) / rate_ips if rate_ips > 0 else 0
            eta_str = f" | ETA {_fmt_time(eta_s)}"

        print(
            f"  Lote {batch_num}/{total_batches} "
            f"({progress}/{total})  "
            f"[{_fmt_time(batch_time)}"
            f"{' | ' + tok_count + ' tok' if api_response else ''}"
            f"{eta_str}]",
            flush=True,
        )

    # Final summary
    elapsed_total = time.time() - start_time
    clear_checkpoint()
    write_output(output_path, all_results)

    print()
    print("=" * 52)
    print(f"Clasificación completada: {len(all_results)}/{total} glosas")
    print(f"Tiempo total: {_fmt_time(elapsed_total)}")
    print(f"Tokens: {stats['total_tokens']:,} "
          f"(prompt: {_fmt_tokens(stats['prompt_tokens'])}"
          f" | completion: {_fmt_tokens(stats['completion_tokens'])})")
    print(f"Lotes OK: {stats['batches_ok']}"
          f"  |  →99: {stats['batches_fallback_99']}")
    print(f"Resultado: {output_path}")
    print("=" * 52)
