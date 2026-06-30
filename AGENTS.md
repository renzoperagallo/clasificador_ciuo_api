# AGENTS.md — Clasificador CIUO.08CL

Proyecto Python para clasificar descripciones ocupacionales (glosas) según la Clasificación Internacional Uniforme de Ocupaciones adaptada para Chile (CIUO.08CL), usando modelos LLM via API OpenAI-compatible.

## Estructura del proyecto

```
clasificador_ciuo_api/
├── data/                      # CSV de entrada (id, glosa)
│   ├── glosas.csv             # Dataset de prueba (10 glosas)
│   └── glosas_2.csv           # Dataset real (~5306 glosas)
├── build/                     # CSV de salida clasificados + checkpoint
├── contexto/                  # Manual CIUO.08CL en .xlsx
│   └── ciuo-08-cL.xlsx        # 627 filas, 8 columnas, 1 hoja "CIUO 08.CL"
├── prompt.txt                 # Prompt del sistema para el LLM
├── src/
│   ├── __init__.py
│   ├── main.py                # CLI con argparse
│   ├── config.py              # Carga .env, variables de entorno
│   ├── api_client.py          # Cliente HTTP OpenAI-compatible
│   ├── classifier.py          # Orquestador de clasificación por lotes
│   ├── csv_handler.py         # Lectura/escritura de CSV
│   ├── excel_reader.py        # Lee .xlsx del manual (formato compacto)
│   ├── prompt_builder.py      # Construye prompt sistema + lote de glosas
│   └── checkpoint.py          # Checkpoint para reanudación
├── .env.example               # Plantilla de configuración
├── .env                       # Credenciales reales (NO se sube a git)
├── .gitignore
├── requirements.txt           # openai, python-dotenv, pandas, openpyxl
└── README.md                  # Documentación de uso
```

## Configuración (.env)

```bash
API_BASE_URL=https://integrate.api.nvidia.com/v1
API_KEY=nvapi-...
MODEL_NAME=deepseek-ai/deepseek-v4-flash
TEMPERATURE=0.1
MAX_TOKENS=65536
BATCH_SIZE=25
MAX_RETRIES=3
REQUEST_TIMEOUT=1800
```

- API: NVIDIA NIM, endpoint OpenAI-compatible (`/v1/chat/completions`)
- Modelo principal: `deepseek-ai/deepseek-v4-flash` (~80s por lote de 25 glosas)
- `deepseek-ai/deepseek-v4-pro` no responde en tier gratuito
- BATCH_SIZE=25 es el máximo tolerado por la API gratuita de Nvidia (con 30 da InternalServerError)
- Soporta cualquier API OpenAI-compatible cambiando `API_BASE_URL` y `API_KEY`

## Flujo de clasificación

1. `main.py` → `classifier.classify_csv()`
2. Lee CSV de entrada (`csv_handler.read_input`)
3. Construye system message: `prompt.txt` + contenido del `.xlsx` en `contexto/` (`prompt_builder.build_system_message`)
4. Divide glosas en lotes de `BATCH_SIZE`
5. Por cada lote:
   - Construye user message con las glosas
   - Llama a la API (`api_client.chat_completion`) con hasta `MAX_RETRIES` reintentos
   - Parsea JSON de respuesta
   - **Si API falla tras reintentos**: detiene el proceso y guarda checkpoint (NO marca como 99)
   - **Si API responde pero JSON malformado**: marca lote como `99` y continúa
   - Guarda checkpoint (`checkpoint.save`) y CSV parcial tras cada lote
6. Al terminar, limpia checkpoint y escribe CSV final

## Sistema de reanudación (checkpoint)

- **Checkpoint**: `build/.checkpoint.json` (excluido de git)
- Se guarda después de CADA lote procesado
- Contiene: `processed`, `total`, `input_file`, `output_file`, `batch_size`, `elapsed`, `stats`
- **Reanudación**: `python -m src.main --resume` lee el CSV de salida existente para recuperar resultados, salta las filas ya procesadas, y continúa
- La API caída NO se marca como 99 — se detiene el proceso y el usuario reanuda cuando la API esté disponible

## Comandos CLI

```bash
# Clasificar
python -m src.main -i data/glosas.csv -o build/clasificadas.csv

# Reanudar proceso interrumpido
python -m src.main --resume

# Ver progreso sin ejecutar
python -m src.main --status

# Mostrar configuración cargada
python -m src.main --show-config

# Opciones adicionales
python -m src.main -i ... -o ... -b 5       # batch_size=5
python -m src.main -i ... -o ... -m <model> # modelo alternativo
```

## Formato de entrada/salida

### CSV de entrada
```csv
id,glosa
1,Médico cirujano en hospital público
2,Profesor de enseñanza básica
```

### CSV de salida
```csv
id,glosa,gran_grupo,subgrupo_principal,subgrupo,grupo_primario
1,Médico cirujano en hospital público,2,22,221,2212
2,Profesor de enseñanza básica,2,23,234,2341
3,Trabajador,99,99,99,99
```

- `gran_grupo`: 1 dígito
- `subgrupo_principal`: 2 dígitos
- `subgrupo`: 3 dígitos
- `grupo_primario`: 4 dígitos
- `"99"` en cualquier nivel = información insuficiente
- `"99"` en TODOS los niveles = glosa inclasificable

## Reglas de clasificación CIUO.08CL

10 Grandes Grupos:
| Código | Nombre |
|---|---|
| 0 | Ocupaciones Militares |
| 1 | Directores, Gerentes y Administradores |
| 2 | Profesionales Científicos e Intelectuales |
| 3 | Técnicos y Profesionales de Nivel Medio |
| 4 | Personal de Apoyo Administrativo |
| 5 | Trabajadores de los Servicios y Vendedores |
| 6 | Agricultores y Trabajadores Calificados |
| 7 | Oficiales, Operarios y Artesanos |
| 8 | Operadores de Instalaciones, Máquinas y Ensambladores |
| 9 | Ocupaciones Elementales |

- Clasificar al nivel más específico posible
- `"99"` donde no haya información suficiente
- NO buscar en internet — solo usar el manual adjunto y conocimiento CIUO.08CL
- No inventar especialidades ni suponer detalles

## Manual de clasificación (contexto/)

- `ciuo-08-cL.xlsx`: 627 filas × 8 columnas en 1 hoja "CIUO 08.CL"
- Columnas: Gran Grupo, Subgrupo Principal, Subgrupo, Grupo Primario, Glosa, Descripción, Ocupaciones Incluidas, Ocupaciones No Incluidas
- `excel_reader.py` extrae un formato compacto (~175K chars, ~44K tokens):
  - GRANDES GRUPOS: código + nombre + descripción truncada a 150 chars
  - SUBGRUPOS PRINCIPALES: código + nombre + descripción truncada a 100 chars
  - GRUPOS PRIMARIOS: código + nombre + listas de incluidos/excluidos truncadas a 200 chars
- Las descripciones largas se truncan para mantener el prompt dentro del contexto

## Dependencias

```
openai>=1.0       # Cliente OpenAI-compatible
python-dotenv>=1.0 # Carga .env
pandas>=2.0       # Lectura del .xlsx
openpyxl>=3.1     # Soporte .xlsx para pandas
```

## Entorno

- Python 3.10+
- Venv en `venv/` (creado con `python -m venv venv`)
- El usuario usa fish shell (no source `venv/bin/activate` — usar `venv/bin/python` directamente)
- `python -m src.main` requiere ejecutarse desde la raíz del proyecto

## Notas importantes

- El `.env` contiene la API key real y NUNCA debe subirse a git (está en `.gitignore`)
- `build/*.csv` y `build/.checkpoint.json` están en `.gitignore`
- Para usar otro modelo, cambiar `MODEL_NAME` en `.env`
- El sistema build_message de `prompt_builder.py` concatena `prompt.txt` + manual del contexto
- Si no hay `.xlsx` en `contexto/`, el sistema funciona solo con `prompt.txt`
- La API de Nvidia es gratuita pero tiene rate limits — `REQUEST_TIMEOUT=1800s` (30 min) para lotes grandes
- BATCH_SIZE máximo probado: 25. Con 30 o más da InternalServerError en tier gratuito
