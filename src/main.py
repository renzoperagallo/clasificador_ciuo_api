import argparse
import sys
from src.config import validate, MODEL_NAME, BATCH_SIZE, to_dict
from src.classifier import classify_csv
from src.checkpoint import load as load_checkpoint
from src.checkpoint import get_progress

sys.stdout.reconfigure(line_buffering=True) if hasattr(
    sys.stdout, "reconfigure"
) else None


def main():
    parser = argparse.ArgumentParser(
        description="Clasificador CIUO.08CL — Clasifica descripciones "
                    "ocupacionales usando un LLM"
    )
    parser.add_argument(
        "--input", "-i",
        default=None,
        help="Ruta al archivo CSV de entrada (columnas: id, glosa). "
             "No requerido si se usa --resume.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Ruta al archivo CSV de salida. "
             "No requerido si se usa --resume.",
    )
    parser.add_argument(
        "--model", "-m",
        default=None,
        help=f"Modelo a utilizar (por defecto: {MODEL_NAME})",
    )
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=None,
        help=f"Tamaño del lote (por defecto: {BATCH_SIZE})",
    )
    parser.add_argument(
        "--resume", "-r",
        action="store_true",
        help="Reanuda desde el último checkpoint guardado",
    )
    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="Muestra el progreso del último checkpoint y sale",
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Muestra la configuración cargada y sale",
    )

    args = parser.parse_args()

    if args.show_config:
        print("Configuración actual:")
        for key, value in to_dict().items():
            print(f"  {key} = {value}")
        return

    if args.status:
        info = get_progress()
        if info:
            print(info)
        else:
            print("No hay un proceso de clasificación en curso.")
        return

    try:
        validate()
    except ValueError as e:
        print(f"Error de configuración: {e}", file=sys.stderr)
        sys.exit(1)

    if args.resume:
        cp = load_checkpoint()
        if cp is None:
            print("Error: No hay checkpoint para reanudar.",
                  file=sys.stderr)
            sys.exit(1)

        input_file = args.input or cp.get("input_file")
        output_file = args.output or cp.get("output_file")

        if not input_file or not output_file:
            print("Error: Checkpoint incompleto. Especifica --input y --output.",
                  file=sys.stderr)
            sys.exit(1)

        print(f"Entrada: {input_file}")
        print(f"Salida:  {output_file}")

        classify_csv(
            input_path=input_file,
            output_path=output_file,
            model=args.model,
            batch_size=args.batch_size or cp.get("batch_size"),
            resume=True,
        )
    else:
        if not args.input or not args.output:
            parser.print_help()
            print("\nError: --input y --output son requeridos.",
                  file=sys.stderr)
            sys.exit(1)

        print(f"Iniciando clasificación: {args.input} → {args.output}")
        classify_csv(
            input_path=args.input,
            output_path=args.output,
            model=args.model,
            batch_size=args.batch_size,
            resume=False,
        )
