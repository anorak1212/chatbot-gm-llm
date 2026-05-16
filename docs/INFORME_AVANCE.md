# Informe de Avance — Chatbot GM LLM

> **Proyecto:** Integrativa Profesional — 26A-IP-M1 GM | UAEM FICO
> **Cliente:** General Motors
> **Fecha:** Mayo 2026

---

## 1. Resumen Ejecutivo

El chatbot GM es un asistente de ingenieria automotriz especializado en **7 Best Practices (BPs)** de diseno de trim interior de puertas. El sistema utiliza **GraphRAG** (Neo4j + LangChain) para recuperar informacion tecnica de una base de conocimientos y un LLM local (**Gemma-4** via LM Studio) para generar respuestas.

**Estado actual:** Funcional con streaming, memoria conversacional, soporte de imagenes multimodales y deteccion inteligente de intencion.

---

## 2. Arquitectura Original vs Implementada

### Lo que planeaba el README original

```
Capa 3: Chainlit + FastAPI + vLLM + mem0
Capa 2: Neo4j + LlamaIndex PropertyGraph
Capa 1: Llama 3 (70B/405B) + QLoRA + Unsloth + Fine-tuning
```

### Lo que realmente esta implementado

```
┌──────────────────────────────────────┐
│         UI: Chainlit (app.py)        │
│   - Streaming en tiempo real         │
│   - Memoria de conversacion          │
│   - Soporte de imagenes              │
└──────────────┬───────────────────────┘
               │
┌──────────────▼───────────────────────┐
│    GraphRAG Pipeline (LangChain)     │
│  - Clasificacion de intencion (LLM)  │
│  - Neo4jVector (vector search)       │
│  - Neo4jGraph (Cypher queries)       │
│  - all-MiniLM-L6-v2 (embeddings)     │
│  - Reranker lexico local             │
└──────────────┬───────────────────────┘
               │
┌──────────────▼───────────────────────┐
│      LLM: Gemma-4 via LM Studio      │
│      (OpenAI-compatible API)         │
│  - Multimodal (texto + imagenes)     │
│  - Streaming nativo                  │
│  - max_tokens: 2000                  │
└──────────────┬───────────────────────┘
               │
┌──────────────▼───────────────────────┐
│         Neo4j 5.23 (Docker)          │
│  - 7 CHUNK nodes (Best Practices)    │
│  - 23 COMPONENTE/CONCEPTO nodes      │
│  - 12 relaciones semanticas          │
│  - Vector index (chunk_index)        │
└──────────────────────────────────────┘
```

**Diferencia clave:** Se simplifico la arquitectura eliminando fine-tuning, vLLM, LlamaIndex y mem0. Se reemplazo Llama 3 por Gemma-4 via LM Studio, y LlamaIndex por LangChain. El resultado es un sistema mas ligero, funcional y mantenible.

---

## 3. Cambios Realizados

### 3.1 Documentacion

| Archivo | Cambio |
|---|---|
| `README.md` | Reescrito completo. Refleja arquitectura real, stack tecnologico actual, tabla de 7 BPs, seccion de deteccion de intencion |
| `INSTALLATION.md` | Simplificado. Eliminadas secciones de fine-tuning, GPU, CUDA. Pasos claros y funcionales |
| `chainlit.md` | De texto default a contenido personalizado con descripcion del asistente y ejemplos de uso |
| `.env.example` | Corregido password Neo4j (`admin` → `admin1234`). Agregadas variables de LM Studio |
| `.gitignore` | Corregida inconsistencia: ya no ignora `data/processed/` ni `data/qa_pairs/` |

### 3.2 Dependencias

| Archivo | Antes | Ahora |
|---|---|---|
| `requirements.txt` | 65 lineas, 25+ paquetes (torch, unsloth, vllm, llama-index, ragas, wandb, mlflow, etc.) | 22 lineas, solo paquetes que se usan realmente |
| `requirements-minimal.txt` | Lista parcial de deps | Ahora hace `-r requirements.txt` (no hay diferencia) |

**Paquetes eliminados:** `torch`, `torchvision`, `torchaudio`, `peft`, `trl`, `bitsandbytes`, `datasets`, `tokenizers`, `huggingface-hub`, `llama-cpp-python`, `autoawq`, `llama-index`, `llama-index-graph-stores-neo4j`, `llama-index-llms-ollama`, `docling`, `pymupdf4llm`, `vllm`, `ragas`, `deepeval`, `wandb`, `mlflow`

### 3.3 Codigo Eliminado

| Archivo | Motivo |
|---|---|
| `src/models/model_loader.py` | Stub vacio de 8 lineas (solo tenia `pass`) |
| `src/config.py` | Importaba `pydantic_settings` (no estaba en deps), no se usaba en ningun lado |
| `src/models/` | Directorio vacio tras eliminar model_loader.py |
| `src/data/` | Directorio vacio (solo tenia `__init__.py`) |
| `src/training/` | Directorio vacio (solo tenia `__init__.py`) |

### 3.4 Codigo Corregido

| Archivo | Problema | Solucion |
|---|---|---|
| `src/api/main.py` | Importaba `src.config` que fue eliminado | Simplificado sin dependencias externas |
| `docker/Dockerfile` | Healthcheck apuntaba a puerto 8000 pero Chainlit corre en 8001 | Eliminado healthcheck innecesario |
| `verify_setup.sh` | Verificaba archivos que ya no existen | Actualizado a estructura real |

---

## 4. Pipeline RAG — Evolucion

El archivo `src/graph/rag_pipeline.py` fue reescrito 5 veces:

### Version 1 — Original
- RAG incondicional: siempre buscaba en Neo4j sin importar la pregunta
- `k=4` documentos, `top 3` tras reranking
- `max_tokens=500` (respuestas cortadas)
- IP de LM Studio hardcodeada
- Prompt duplicado (PromptTemplate + system_msg)
- Bug: variable `fallback_err` sin usar

### Version 2 — Deteccion de Intencion (Regex)
- Agregada funcion `is_conversational()` con regex y keywords
- Agregada funcion `is_list_all_query()` para detectar "listar todas las BPs"
- Ruta conversacional: responde sin RAG para saludos
- Ruta lista completa: Cypher directo para traer las 7 BPs ordenadas
- Ruta tecnica: vector search con reranking
- **Problema**: Regex hardcoded, fragil, no escala, falsos positivos

### Version 3 — Limpieza y Configuracion
- `max_tokens` aumentado de 500 a 2000
- `LM_STUDIO_URL` como variable de entorno
- Eliminado PromptTemplate duplicado
- Eliminado bug `fallback_err`
- Imagenes via OpenAI Vision API format (en lugar de multipart roto)
- `k=6`, `top 5` para mejor cobertura

### Version 4 — Streaming y Memoria
- `query()` ahora es `async` con generador
- Usa `llm.astream()` para streaming token por token
- Historial de conversacion: ultimos 10 turnos via `cl.user_session`
- El historial se inserta entre system prompt y mensaje actual
- Imagenes referenciadas por nombre en el historial (no base64 para ahorrar memoria)

### Version 5 — Clasificacion de Intencion LLM-based (Actual)
- Eliminadas todas las regex hardcoded (`GREETING_PATTERNS`, `CONVERSATIONAL_KEYWORDS`, `LIST_ALL_PATTERNS`)
- Agregado `_classify_intent()` que usa el mismo LLM para clasificar la intencion
- Prompt especializado con 3 categorias descriptivas
- Considera los ultimos 3 turnos del historial para desambiguar
- Cache local para textos ya clasificados (evita llamadas redundantes)
- Instancia separada `_intent_llm` con `temperature=0.0`, `max_tokens=16` (ligero, solo genera una palabra)
- Fallback seguro: si el LLM responde algo inesperado, default a `specific_query`

---

## 5. Funcionalidades Actuales

### 5.1 Clasificacion de Intencion (LLM-based)

El pipeline usa el mismo LLM para clasificar la intencion del usuario antes de decidir la ruta de procesamiento.

| Intencion | Descripcion | Ejemplo | Comportamiento |
|---|---|---|---|
| `conversational` | Saludos, despedidas, charla casual | "hola", "gracias", "quien eres" | Responde con LLM directo, sin RAG |
| `list_all` | Lista completa de todas las BPs | "cuales son las best practices?", "dame la lista" | Trae las 7 BPs via Cypher, ordenadas BP1-BP7 |
| `specific_query` | Pregunta tecnica sobre un BP especifico | "cual es el torque del tirador?" | Vector search + reranking lexico |

**Como funciona:**
- Prompt especializado con 3 categorias descriptivas
- Considera los ultimos 3 turnos del historial para desambiguar referencias contextuales
- Cache local: textos ya clasificados no requieren llamada al LLM
- Instancia separada con `temperature=0.0`, `max_tokens=16` — solo genera una palabra
- Fallback seguro: si el LLM responde algo inesperado, default a `specific_query`

**Ventajas sobre regex:**
- Entiende cualquier variacion linguistica sin agregar patrones
- Considera el contexto de la conversacion
- Cero mantenimiento — para agregar una nueva categoria solo se agrega la descripcion al prompt
- Costo minimo: 16 tokens max por clasificacion

### 5.2 Streaming

- La respuesta aparece token por token en la UI
- Usa `llm.astream()` de LangChain (compatible con LM Studio)
- El usuario ve la respuesta generarse en tiempo real

### 5.3 Memoria Conversacional

- Persiste los ultimos 10 turnos (user + assistant)
- Permite referencias como "ahora hazlo en ingles" o "explicame mas sobre eso"
- El modelo entiende el contexto de toda la conversacion
- Las imagenes se referencian por nombre en el historial

### 5.4 Imagenes Multimodales

- El usuario puede subir imagenes directamente en Chainlit
- Se convierten a base64 y se envian en formato OpenAI Vision API
- Gemma-4 es multimodal y puede analizar planos, diagramas, fotos de componentes
- La imagen se analiza junto con el contexto RAG

### 5.5 Base de Conocimientos

| BP | Titulo | Categoria | Prioridad |
|---|---|---|---|
| BP 1 | Clearance Map Pocket a Asiento | Requisitos Dimensionales | Alta |
| BP 2 | Interfaz Trim/Side Closures - Trim Foot | Requisitos Dimensionales | Alta |
| BP 3 | Interfaz Tirador de Puerta a Chapa Metalica | Requisitos Mecanicos | Alta |
| BP 4 | Interfaz Taza de Puerta a Chapa Metalica | Requisitos Mecanicos | Alta |
| BP 5 | Interfaz Cinturon de Seguridad a Panel de Puerta | Seguridad | Critica |
| BP 6 | Ubicacion de Etiqueta del Panel de Puerta | Identificacion | Media |
| BP 7 | Estrategia de Cinta Protectora | Empaque y Logistica | Media |

**Entidades:** 23 (12 componentes, 8 conceptos tecnicos, 2 segmentos, 2 organizaciones)
**Relaciones:** 12 relaciones semanticas entre entidades
**Q&A Pairs:** 15 pares pregunta-respuesta para evaluacion

---

## 6. Flujo de una Consulta

```
1. Usuario envia mensaje (texto +/- imagenes) via Chainlit
2. app.py extrae imagenes como base64 desde message.elements
3. app.py recupera historial de cl.user_session
4. rag_pipeline.query() clasifica intencion via LLM:
   ├── Cache: texto ya clasificado? → usar resultado cacheado
   ├── Si no → _intent_llm.invoke(prompt con historial) → conversational / list_all / specific_query
   └── Guardar resultado en cache
5. Ejecutar ruta segun intencion:
   ├── conversational → LLM directo con historial, sin RAG
   ├── list_all → Cypher MATCH (c:CHUNK) ORDER BY c.id → trae las 7 BPs
   └── specific_query → Vector search k=6 → reranking lexico → top 5
6. Construye mensajes:
   [system] → [historial: ultimos 10 turnos] → [contexto RAG] → [user + imagenes]
7. Streaming via llm.astream() token por token
8. app.py acumula respuesta completa
9. Actualiza historial: append user + assistant
10. Persiste en cl.user_session para el siguiente turno
```

---

## 7. Estructura Final del Repositorio

```
chatbot-gm-llm/
│
├── app.py                          # Chainlit UI (streaming + memoria)
├── chainlit.md                     # Welcome screen personalizado
├── .env.example                    # Neo4j + LM Studio config
├── requirements.txt                # 22 deps (solo las usadas)
├── requirements-minimal.txt        # -r requirements.txt
├── verify_setup.sh                 # Script de verificacion
├── INSTALLATION.md                 # Guia de instalacion
├── README.md                       # Documentacion principal
├── .gitignore                      # Archivos ignorados
│
├── docker/
│   ├── docker-compose.yml          # Neo4j 5.23 + APOC
│   └── Dockerfile                  # Imagen Docker simplificada
│
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py                 # FastAPI stub (/health, /)
│   └── graph/
│       ├── __init__.py
│       ├── load_bp_knowledge.py    # Carga datos a Neo4j
│       └── rag_pipeline.py         # Pipeline RAG completo
│
└── data/
    ├── processed/
    │   ├── bp_chunks.json          # 7 Best Practices
    │   ├── bp_entities.json        # 23 entidades
    │   ├── bp_relationships.json   # 12 relaciones
    │   └── README_KNOWLEDGE_BASE.md
    └── qa_pairs/
        └── bp_qa_pairs.json        # 15 pares Q&A
```

---

## 8. Stack Tecnologico

| Componente | Tecnologia |
|---|---|
| UI | Chainlit |
| RAG Framework | LangChain (langchain-neo4j, langchain-huggingface, langchain-openai) |
| Embeddings | all-MiniLM-L6-v2 (Sentence Transformers) |
| Base de datos | Neo4j 5.23 (Docker + APOC plugin) |
| LLM | Gemma-4-e4b-it via LM Studio (OpenAI-compatible API, multimodal) |
| Clasificacion de intencion | LLM-based (mismo modelo, temperature=0, max_tokens=16, con cache) |
| API | FastAPI (stub con /health y /) |
| Python | 3.10+ |

---

## 9. Como Usar

### Instalacion rapida

```bash
# 1. Crear entorno virtual
python3.10 -m venv .venv && source .venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables
cp .env.example .env
# Editar .env con LM_STUDIO_URL y NEO4J_PASSWORD correctos

# 4. Levantar Neo4j
docker compose -f docker/docker-compose.yml up -d neo4j

# 5. Cargar base de conocimiento
python src/graph/load_bp_knowledge.py

# 6. Iniciar LM Studio con Gemma-4-e4b-it cargado

# 7. Iniciar chatbot
chainlit run app.py --port 8001 -w
```

### Ejemplos de uso

| Pregunta | Tipo de respuesta |
|---|---|
| "Hola" | Saludo conversacional sin RAG |
| "Cuales son las best practices?" | Lista completa de BP1-BP7 |
| "Cual es el torque del tirador?" | BP3: >=2 x M4.2, 5 +/- 0.5 Nm |
| "Que clearance necesita el cinturon?" | BP5: >=30mm |
| [Subir imagen de plano] + "que BP aplica aqui?" | Analisis de imagen + contexto RAG |
| [Despues de una respuesta] "ahora en ingles" | Traduce la respuesta anterior (memoria) |

---

## 10. Proximos Pasos Sugeridos

| Prioridad | Accion | Descripcion |
|---|---|---|
| Alta | Tests automatizados | No hay ningun test en el proyecto |
| Media | Personalizar UI de Chainlit | Logo, colores, descripcion en config.toml |
| Media | Mejorar reranker | Reemplazar overlap lexico por cross-encoder |
| Baja | Implementar FastAPI completo | Agregar endpoints reales al API |
| Baja | Agregar evaluacion RAG | Usar los 15 Q&A pairs para validar retrieval |
| Baja | Logo y branding | Agregar imagen personalizada al chatbot |
