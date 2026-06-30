import pandas as pd
from pathlib import Path


def _find_manual():
    contexto_dir = Path(__file__).parent.parent / "contexto"
    xlsx_files = list(contexto_dir.glob("*.xlsx"))
    if not xlsx_files:
        return None
    return xlsx_files[0]


def read_manual(manual_path=None):
    manual_path = manual_path or _find_manual()
    if manual_path is None:
        raise FileNotFoundError(
            "No se encontró archivo .xlsx en la carpeta contexto/"
        )

    excel_file = pd.ExcelFile(manual_path)
    full_text = []

    for sheet in excel_file.sheet_names:
        df = pd.read_excel(manual_path, sheet_name=sheet)
        full_text.append(f"--- Hoja: {sheet} ---")
        full_text.append(df.to_string(index=False))
        full_text.append("")

    return "\n".join(full_text)
