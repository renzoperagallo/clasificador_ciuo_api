# Clasificador CIUO.08CL

Clasifica descripciones ocupacionales (glosas) según la Clasificación Internacional Uniforme de Ocupaciones adaptada para Chile (CIUO.08CL), usando modelos de lenguaje (LLM) a través de la API de [NVIDIA NIM](https://build.nvidia.com/explore/discover).

## Estructura del proyecto

```
├── data/                  # Archivos CSV de entrada (id, glosa)
├── build/                 # Archivos CSV de salida clasificados
├── contexto/              # Manual CIUO.08CL en formato .xlsx
├── prompt.txt             # Prompt del sistema para el LLM
├── src/                   # Código fuente
│   ├── main.py            # Entrada CLI
│   ├── config.py          # Configuración desde .env
│   ├── api_client.py      # Cliente HTTP OpenAI-compatible
│   ├── classifier.py      # Orquestador de clasificación
│   ├── csv_handler.py     # Lectura/escritura de CSV
│   ├── excel_reader.py    # Lectura del manual .xlsx
│   └── prompt_builder.py  # Construcción de prompts
└── .env.example           # Plantilla de variables de entorno
```

## Requisitos

- Python 3.10+
- API Key de [NVIDIA NIM](https://build.nvidia.com/explore/discover)

## Instalación

```bash
git clone https://github.com/renzoperagallo/clasificador_ciuo_api.git
cd clasificador_ciuo_api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuración del archivo `.env`

1. Copia la plantilla:

```bash
cp .env.example .env
```

2. Edita `.env` con tus credenciales:

```bash
# URL base de la API NVIDIA NIM (OpenAI-compatible)
API_BASE_URL=https://integrate.api.nvidia.com/v1

# API Key de NVIDIA (obtenla en https://build.nvidia.com/explore/discover)
API_KEY=nvapi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Modelo a utilizar
MODEL_NAME=deepseek-ai/deepseek-v4-flash

# Parámetros de generación
TEMPERATURE=0.1
MAX_TOKENS=65536

# Tamaño del lote (25 es el máximo en tier gratuito)
BATCH_SIZE=25

# Reintentos máximos por lote
MAX_RETRIES=3

# Timeout por request (30 min para lotes grandes)
REQUEST_TIMEOUT=1800
```

> **IMPORTANTE**: El archivo `.env` contiene tu API key. **Nunca** lo subas a git. Ya está incluido en `.gitignore`.

### Obtener una API Key de NVIDIA

1. Ve a [build.nvidia.com](https://build.nvidia.com/explore/discover)
2. Inicia sesión o crea una cuenta
3. Ve a la sección de API Keys
4. Genera una nueva clave y cópiala en `API_KEY`

### Cambiar de modelo

El proyecto soporta cualquier modelo disponible en la API de NVIDIA NIM (OpenAI-compatible). Para cambiar el modelo, edita `MODEL_NAME` en `.env`. Algunos modelos disponibles:

| Modelo | ID |
|---|---|
| DeepSeek V4 Flash | `deepseek-ai/deepseek-v4-flash` |
| Nemotron 3 Ultra | `nvidia/nemotron-3-ultra-550b-a55b` |
| Mistral Large 3 | `mistralai/mistral-large-3-675b-instruct-2512` |
| Llama 3.3 Nemotron | `nvidia/llama-3.3-nemotron-super-49b-v1.5` |

También puedes usar cualquier otra API OpenAI-compatible (OpenAI, DeepSeek, OpenRouter, etc.) cambiando `API_BASE_URL`, `API_KEY` y `MODEL_NAME`.

## Preparar los datos

### 1. Archivo de glosas (`data/`)

Coloca tu archivo CSV con dos columnas:

```csv
id,glosa
1,Médico cirujano en hospital público
2,Vendedor ambulante de frutas
3,Operario de fábrica
```

### 2. Manual de clasificación (`contexto/`)

Coloca el archivo `.xlsx` con el manual CIUO.08CL en la carpeta `contexto/`. El sistema leerá **todas las hojas** automáticamente y las incluirá como contexto en el prompt del LLM.

### 3. Prompt del sistema (`prompt.txt`)

El archivo `prompt.txt` contiene las instrucciones de clasificación. Puedes editarlo para ajustar el comportamiento del clasificador. El contenido del manual `.xlsx` se concatenará automáticamente al final del prompt.

## Uso

```bash
# Desde el directorio raíz del proyecto
python -m src.main --input data/glosas.csv --output build/clasificadas.csv
```

### Opciones

| Opción | Descripción |
|---|---|
| `-i, --input` | Ruta al CSV de entrada (obligatorio) |
| `-o, --output` | Ruta al CSV de salida (obligatorio) |
| `-m, --model` | Modelo a usar (sobrescribe .env) |
| `-b, --batch-size` | Tamaño del lote (sobrescribe .env) |
| `-r, --resume` | Reanuda desde el último checkpoint |
| `-s, --status` | Muestra el progreso actual y sale |
| `--show-config` | Muestra la configuración cargada |

### Ejemplo

```bash
# Clasificar
python -m src.main -i data/glosas.csv -o build/resultado.csv

# Reanudar tras interrupción
python -m src.main --resume

# Ver progreso
python -m src.main --status
```

## Formato de salida

El archivo CSV de salida contiene 6 columnas:

| id | glosa | gran_grupo | subgrupo_principal | subgrupo | grupo_primario |
|---|---|---|---|---|---|
| 1 | Médico cirujano en hospital público | 2 | 22 | 221 | 2212 |
| 2 | Trabajador | 9 | 99 | 99 | 99 |

- `"99"` indica que no hay suficiente información para clasificar ese nivel
- `"99"` en TODOS los niveles indica una glosa completamente inclasificable
