import csv
from pathlib import Path


def read_input(csv_path):
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "id": row["id"].strip(),
                "glosa": row["glosa"].strip(),
            })
    return rows


def read_output(csv_path):
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "id": row["id"].strip(),
                "glosa": row["glosa"].strip(),
                "gran_grupo": row["gran_grupo"].strip(),
                "subgrupo_principal": row["subgrupo_principal"].strip(),
                "subgrupo": row["subgrupo"].strip(),
                "grupo_primario": row["grupo_primario"].strip(),
            })
    return rows


def write_output(csv_path, rows):
    Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id",
        "glosa",
        "gran_grupo",
        "subgrupo_principal",
        "subgrupo",
        "grupo_primario",
    ]

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
