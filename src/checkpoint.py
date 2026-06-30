import json
from pathlib import Path

_CHECKPOINT_DIR = Path(__file__).parent.parent / "build"
_CHECKPOINT_FILE = _CHECKPOINT_DIR / ".checkpoint.json"


def save(processed, total, input_file, output_file, batch_size, elapsed, stats):
    _CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "input_file": str(input_file),
        "output_file": str(output_file),
        "processed": processed,
        "total": total,
        "batch_size": batch_size,
        "elapsed": elapsed,
        "stats": stats,
    }
    with open(_CHECKPOINT_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load():
    if not _CHECKPOINT_FILE.exists():
        return None
    with open(_CHECKPOINT_FILE) as f:
        return json.load(f)


def clear():
    if _CHECKPOINT_FILE.exists():
        _CHECKPOINT_FILE.unlink()


def get_progress():
    cp = load()
    if cp is None:
        return None

    pct = cp["processed"] / cp["total"] * 100 if cp["total"] else 0
    elapsed_m = cp.get("elapsed", 0) / 60

    info = (
        f"Progreso: {cp['processed']}/{cp['total']} glosas ({pct:.1f}%)\n"
        f"Entrada: {cp['input_file']}\n"
        f"Salida:  {cp['output_file']}\n"
        f"Tamaño de lote: {cp['batch_size']}"
    )

    stats = cp.get("stats", {})
    if stats:
        info += (
            f"\nLotes OK: {stats.get('batches_ok', 0)}"
            f"  |  →99: {stats.get('batches_fallback_99', 0)}"
            f"\nTokens: {stats.get('total_tokens', 0):,}"
            f" (prompt: {stats.get('prompt_tokens', 0):,}"
            f" | completion: {stats.get('completion_tokens', 0):,})"
        )

    if elapsed_m > 0:
        info += f"\nTiempo acumulado: {elapsed_m:.0f}m {cp.get('elapsed', 0) % 60:.0f}s"
        if cp["processed"] > 0 and cp["processed"] < cp["total"]:
            rate = cp["processed"] / cp["elapsed"] if cp["elapsed"] > 0 else 0
            remaining = cp["total"] - cp["processed"]
            eta_s = remaining / rate if rate > 0 else 0
            eta_m = eta_s / 60
            info += f"  |  ETA restante: {eta_m:.0f}m {eta_s % 60:.0f}s"

    return info
