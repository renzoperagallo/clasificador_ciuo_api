import argparse
import sys
from src.config import validate, MODEL_NAME, BATCH_SIZE, to_dict
from src.classifier import classify_csv


def main():
    parser = argparse.ArgumentParser(
        description="Clasificador CIUO.08CL — Clasifica descripciones "
                    "ocupacionales usando un LLM"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Ruta al archivo CSV de entrada (columnas: id, glosa)",
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Ruta al archivo CSV de salida",
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

    try:
        validate()
    except ValueError as e:
        print(f"Error de configuración: {e}", file=sys.stderr)
        sys.exit(1)

    classify_csv(
        input_path=args.input,
        output_path=args.output,
        model=args.model,
        batch_size=args.batch_size,
    )
