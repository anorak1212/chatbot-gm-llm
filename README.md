# Chatbot GM — Asistente de Best Practices (Interior Trim Design)

> **Integrativa Profesional — 26A-IP-M1 GM | UAEM FICO**  
> Cliente: General Motors | Asesor: Prof. Jose Luis Nunez Mejia

Chatbot especialista en **Best Practices (BPs)** de manufactura para diseno de trim interior de puertas, construido con **GraphRAG (Neo4j + LangChain)** y un LLM local multimodal (**Gemma-4** via LM Studio).

---

## Equipo

| Nombre | Rol |
|---|---|
| Mercado Hernandez Jose Eduardo | ML Engineer |
| Jimenez Perez Mateo | ML Engineer |
| Acosta Bernal Maria Esperanza | Data Engineer (GraphRAG) |
| Reyes Conzuelo Camila | Data Engineer (GraphRAG) |

---

## Arquitectura

```
┌──────────────────────────────────────────────────┐
│              UI: Chainlit (app.py)               │
│  - Streaming en tiempo real                      │
│  - Memoria conversacional (ultimos 10 turnos)    │
│  - Soporte de imagenes multimodales              │
└──────────────────┬───────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────┐
│           GraphRAG Pipeline (LangChain)           │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │  Clasificador de Intencion (LLM-based)      │ │
│  │  - Conversational / List All / Specific     │ │
│  │  - Considera historial de conversacion      │ │
│  │  - Cache para textos repetidos              │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │  Neo4jVector (vector search + reranking)    │ │
│  │  Neo4jGraph (Cypher queries directas)       │ │
│  │  all-MiniLM-L6-v2 (embeddings)              │ │
│  └─────────────────────────────────────────────┘ │
└──────────────────┬───────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────┐
│         LLM: Gemma-4 via LM Studio               │
│         (OpenAI-compatible API, multimodal)      │
│  - Streaming nativo (astream)                    │
│  - Vision API (texto + imagenes base64)          │
│  - max_tokens: 2000                              │
└──────────────────┬───────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────┐
│            Neo4j 5.23 (Docker + APOC)            │
│  - 7 CHUNK nodes (Best Practices BP1-BP7)       │
│  - 23 COMPONENTE/CONCEPTO nodes                  │
│  - 12 relaciones semanticas                      │
│  - Vector index (chunk_index)                    │
└──────────────────────────────────────────────────┘
```

---

## Estructura del repositorio

```
chatbot-gm-llm/
│
├── app.py                          # Chainlit UI (streaming + memoria)
├── chainlit.md                     # Welcome screen personalizado
├── .env.example                    # Variables de entorno
│
├── src/
│   ├── graph/
│   │   ├── rag_pipeline.py         # Pipeline RAG completo
│   │   │   ├── _classify_intent()  # Clasificacion LLM-based
│   │   │   ├── _handle_conversational_stream()
│   │   │   ├── _handle_rag_stream()
│   │   │   ├── _get_all_chunks_ordered()  # Cypher directo
│   │   │   └── _get_context_vector()      # Vector search
│   │   └── load_bp_knowledge.py    # Carga de datos a Neo4j
│   └── api/
│       └── main.py                 # FastAPI stub (health check)
│
├── data/
│   ├── processed/
│   │   ├── bp_chunks.json          # 7 Best Practices (BP1-BP7)
│   │   ├── bp_entities.json        # 23 entidades (componentes, conceptos)
│   │   ├── bp_relationships.json   # 12 relaciones semanticas
│   │   └── README_KNOWLEDGE_BASE.md
│   └── qa_pairs/
│       └── bp_qa_pairs.json        # 15 pares Q&A para evaluacion
│
├── docker/
│   ├── docker-compose.yml           # Neo4j con Docker
│   └── Dockerfile
│
├── docs/
│   └── INFORME_AVANCE.md            # Informe detallado del proyecto
│
├── requirements.txt                 # Dependencias (solo las usadas)
├── requirements-minimal.txt         # -r requirements.txt
├── verify_setup.sh                  # Script de verificacion
├── INSTALLATION.md                  # Guia de instalacion
└── README.md
```

---

## Stack tecnologico

| Componente | Tecnologia |
|---|---|
| UI | Chainlit |
| RAG Framework | LangChain (langchain-neo4j, langchain-huggingface, langchain-openai) |
| Embeddings | all-MiniLM-L6-v2 (Sentence Transformers) |
| Base de datos | Neo4j 5.23 (Docker + APOC) |
| LLM | Gemma-4-e4b-it via LM Studio (OpenAI-compatible API, multimodal) |
| Clasificacion de intencion | LLM-based (mismo modelo, temperature=0, max_tokens=16) |
| API | FastAPI (stub) |

---

## Inicio rapido

### 1. Clonar el repositorio
```bash
git clone https://github.com/TU_USUARIO/chatbot-gm-llm.git
cd chatbot-gm-llm
```

### 2. Crear entorno virtual e instalar dependencias
```bash
python3.10 -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 3. Configurar variables de entorno
```bash
cp .env.example .env
# Edita .env con tus valores (especialmente LM_STUDIO_URL y NEO4J_PASSWORD)
```

### 4. Levantar Neo4j con Docker
```bash
docker compose -f docker/docker-compose.yml up -d neo4j
# Espera 15-20 segundos a que inicie
```

### 5. Cargar la base de conocimiento
```bash
python src/graph/load_bp_knowledge.py
```

Se cargaran:
- 7 chunks de conocimiento (BP1-BP7)
- 23 entidades (componentes, conceptos tecnicos, segmentos)
- 12 relaciones semanticas

### 6. Iniciar LM Studio
Asegurate de tener **Gemma-4-e4b-it** cargado en LM Studio y el servidor corriendo. Configura la URL en `.env`:
```
LM_STUDIO_URL=http://192.168.1.80:1234
```

### 7. Probar la interfaz Chainlit
```bash
chainlit run app.py --port 8001 -w
```

La interfaz estara disponible en: `http://localhost:8001`

---

## Base de Conocimiento

Basada en el documento confidencial de General Motors **"Best Practices for Interior Trim Design"**:

| BP | Titulo | Categoria | Prioridad |
|---|---|---|---|
| BP 1 | Clearance Map Pocket a Asiento | Requisitos Dimensionales | Alta |
| BP 2 | Interfaz Trim/Side Closures - Trim Foot | Requisitos Dimensionales | Alta |
| BP 3 | Interfaz Tirador de Puerta a Chapa Metalica | Requisitos Mecanicos | Alta |
| BP 4 | Interfaz Taza de Puerta a Chapa Metalica | Requisitos Mecanicos | Alta |
| BP 5 | Interfaz Cinturon de Seguridad a Panel de Puerta | Seguridad | Critica |
| BP 6 | Ubicacion de Etiqueta del Panel de Puerta | Identificacion | Media |
| BP 7 | Estrategia de Cinta Protectora | Empaque y Logistica | Media |

Para mas detalles, ver [data/processed/README_KNOWLEDGE_BASE.md](data/processed/README_KNOWLEDGE_BASE.md).

---

## Clasificacion de Intencion (LLM-based)

El pipeline clasifica automaticamente la intencion del usuario usando el mismo LLM con un prompt especializado. Esto permite entender cualquier variacion linguistica sin necesidad de regex hardcoded.

### Categorias

| Intencion | Descripcion | Ejemplo | Comportamiento |
|---|---|---|---|
| `conversational` | Saludos, despedidas, charla casual | "hola", "gracias", "quien eres?" | Responde sin RAG |
| `list_all` | Lista completa de todas las BPs | "cuales son las best practices?", "dame la lista de BPs" | Trae las 7 BPs via Cypher directo |
| `specific_query` | Pregunta tecnica sobre un BP especifico | "cual es el torque del tirador?", "que clearance necesita el cinturon?" | Vector search + reranking |

### Caracteristicas

- **Contexto del historial**: Incluye los ultimos 3 turnos de conversacion para desambiguar referencias como "ahora en ingles" o "explicame mas"
- **Cache**: Textos ya clasificados se cachean para evitar llamadas redundantes al LLM
- **Ligero**: Usa el mismo modelo con `temperature=0.0` y `max_tokens=16` — solo genera una palabra
- **Escalable**: Para agregar una nueva categoria, solo se agrega la descripcion al prompt

---

## Funcionalidades

### Streaming
La respuesta aparece token por token en la UI en tiempo real, sin esperar el resultado completo.

### Memoria Conversacional
Persiste los ultimos 10 turnos (user + assistant). Permite referencias como "ahora hazlo en ingles" o "explicame mas sobre eso" sin perder el contexto.

### Imagenes Multimodales
El usuario puede subir imagenes directamente en Chainlit (planos, diagramas, fotos de componentes). Se envian en formato OpenAI Vision API y Gemma-4 las analiza junto con el contexto RAG.

---

## Notas importantes

- Los archivos PDF de BP/GMW son **confidenciales** — nunca subir a Git.
- El LLM corre localmente via **LM Studio** — necesitas tenerlo instalado y corriendo.
- Python **3.10+** requerido.
- Neo4j requiere **Docker**.

---

## Referencias

- [LangChain Neo4j](https://python.langchain.com/docs/integrations/providers/neo4j/)
- [Neo4j APOC](https://neo4j.com/labs/apoc/)
- [Chainlit](https://github.com/Chainlit/chainlit)
- [LM Studio](https://lmstudio.ai/)
- [Sentence Transformers](https://www.sbert.net/)
