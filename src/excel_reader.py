import pandas as pd
from pathlib import Path


def _find_manual():
    contexto_dir = Path(__file__).parent.parent / "contexto"
    xlsx_files = list(contexto_dir.glob("*.xlsx"))
    if not xlsx_files:
        return None
    return xlsx_files[0]


def _truncate(text, max_chars=150):
    if pd.isna(text) or not isinstance(text, str):
        return ""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(".", 1)[0] + "."


def read_manual(manual_path=None):
    manual_path = manual_path or _find_manual()
    if manual_path is None:
        raise FileNotFoundError(
            "No se encontró archivo .xlsx en la carpeta contexto/"
        )

    excel_file = pd.ExcelFile(manual_path)
    parts = []

    for sheet in excel_file.sheet_names:
        df = pd.read_excel(manual_path, sheet_name=sheet)

        # Normalizar: convertir códigos a string sin .0
        for col in ["Gran Grupo", "Subgrupo Principal", "Subgrupo", "Grupo Primario"]:
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda x: str(int(x)) if pd.notna(x) else ""
                )

        # Separar en niveles jerárquicos
        gran_grupo_rows = df[df["Subgrupo Principal"] == ""]
        subgrupo_principal_rows = df[
            (df["Subgrupo Principal"] != "") & (df["Subgrupo"] == "")
        ]
        subgrupo_rows = df[
            (df["Subgrupo"] != "") & (df["Grupo Primario"] == "")
        ]
        grupo_primario_rows = df[df["Grupo Primario"] != ""]

        parts.append(f"=== Hoja: {sheet} ===\n")

        # 1. GRANDES GRUPOS (1 dígito)
        parts.append("--- GRANDES GRUPOS ---")
        for _, row in gran_grupo_rows.iterrows():
            code = row["Gran Grupo"]
            name = str(row["Glosa"]).strip() if pd.notna(row["Glosa"]) else ""
            desc = _truncate(row.get("Descripción", ""), 150)
            parts.append(f"  {code}: {name}")
            if desc:
                parts.append(f"     {desc}")
        parts.append("")

        # 2. SUBGRUPOS PRINCIPALES (2 dígitos)
        parts.append("--- SUBGRUPOS PRINCIPALES ---")
        for _, row in subgrupo_principal_rows.iterrows():
            code = row["Subgrupo Principal"]
            name = str(row["Glosa"]).strip() if pd.notna(row["Glosa"]) else ""
            desc = _truncate(row.get("Descripción", ""), 100)
            parts.append(f"  {code}: {name}")
            if desc:
                parts.append(f"     {desc}")
        parts.append("")

        # 3. GRUPOS PRIMARIOS (4 dígitos) — el nivel más detallado
        parts.append("--- GRUPOS PRIMARIOS (clasificación completa) ---")
        for _, row in grupo_primario_rows.iterrows():
            code = row["Grupo Primario"]
            name = str(row["Glosa"]).strip() if pd.notna(row["Glosa"]) else ""
            incluidas = str(row.get("Ocupaciones Incluidas", "")).strip()
            no_incluidas = str(row.get("Ocupaciones No Incluidas", "")).strip()

            parts.append(f"  {code}: {name}")
            if incluidas and incluidas != "nan":
                parts.append(f"     Incluye: {_truncate(incluidas, 200)}")
            if no_incluidas and no_incluidas != "nan":
                parts.append(f"     Excluye: {_truncate(no_incluidas, 200)}")
        parts.append("")

    return "\n".join(parts)
