# Chatbot GM — Especialista en BPs/GMWs con LLM

> **Integrativa Profesional — 26A-IP-M1 GM | UAEM FICO**  
> Cliente: General Motors | Asesor: Prof. José Luis Núñez Mejia

Chatbot especialista en **Best Practices (BPs)** y **General Motors Worldwide (GMWs)** de manufactura, construido sobre un LLM open-source (Llama 3) con fine-tuning QLoRA y recuperación aumentada por grafos (GraphRAG + Neo4j).

---

## Equipo

| Nombre | Rol principal |
|---|---|
| Mercado Hernández José Eduardo | ML Engineer (Fine-tuning) |
| Jiménez Pérez Mateo | ML Engineer (Fine-tuning) |
| Acosta Bernal María Esperanza | Data Engineer (GraphRAG) |
| Reyes Conzuelo Camila | Data Engineer (GraphRAG) |

---

## Arquitectura del sistema

```
┌─────────────────────────────────────────────────┐
│              Capa 3 — Interfaz                  │
│         Chainlit + FastAPI + vLLM               │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│           Capa 2 — Estructura RAG               │
│        Neo4j + LlamaIndex PropertyGraph         │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│            Capa 1 — Modelo LLM                  │
│     Llama 3 (70B/405B) + QLoRA + Unsloth        │
└─────────────────────────────────────────────────┘
```

---

## Estructura del repositorio

```
chatbot-gm-llm/
│
├── data/
│   ├── raw/              # PDFs originales de BP/GMW (NO subir a Git)
│   ├── processed/        # Datasets limpios en JSON/JSONL
│   └── qa_pairs/         # Pares pregunta-respuesta para fine-tuning
│
├── notebooks/
│   ├── 01_data_processing.ipynb     # Limpieza y extracción de Q&A
│   ├── 02_finetuning_qlora.ipynb    # Fine-tuning con Unsloth + QLoRA
│   └── 03_evaluation.ipynb          # Evaluación del modelo
│
├── src/
│   ├── data/
│   │   ├── pdf_extractor.py         # Extracción de texto de PDFs
│   │   └── qa_generator.py          # Generación de pares Q&A
│   ├── training/
│   │   ├── config.py                # Hiperparámetros y configuración
│   │   └── trainer.py               # Pipeline de entrenamiento
│   ├── graph/
│   │   ├── neo4j_loader.py          # Carga de docs a Neo4j
│   │   └── graph_query.py           # Consultas Cypher
│   └── api/
│       ├── main.py                  # FastAPI app
│       └── chatbot.py               # Lógica del chatbot
│
├── models/                          # Checkpoints del modelo (NO subir a Git)
│
├── docs/
│   ├── Bitacora_Trabajo.docx
│   ├── Objetivos_Proyecto.docx
│   └── architecture.md
│
├── docker/
│   ├── docker-compose.yml           # Neo4j + API
│   └── Dockerfile
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Stack tecnológico

### Capa 1 — Fine-tuning
| Herramienta | Propósito |
|---|---|
| Llama 3.1 8B / 70B | Modelo base |
| Unsloth | Fine-tuning 2x más rápido, menos VRAM |
| QLoRA (PEFT) | Entrenamiento eficiente en GPU comercial |
| SFTTrainer (TRL) | Trainer de HuggingFace |
| GGUF (q4_k_m) | Formato de exportación comprimido |
| Weights & Biases | Monitoreo del entrenamiento |

### Capa 2 — GraphRAG
| Herramienta | Propósito |
|---|---|
| Neo4j (Docker) | Base de datos de grafos |
| LlamaIndex PropertyGraphIndex | Conexión LLM ↔ Neo4j |
| APOC Library | Procesamiento avanzado de texto en Neo4j |
| Docling | Extracción de texto de PDFs |

### Capa 3 — Interfaz
| Herramienta | Propósito |
|---|---|
| Chainlit | UI de chat con streaming |
| FastAPI | API REST entre modelo e interfaz |
| vLLM | Serving de alta eficiencia |
| mem0 | Gestión de sesiones conversacionales |

---

## Inicio rápido

### 1. Clonar el repositorio
```bash
git clone https://github.com/TU_USUARIO/chatbot-gm-llm.git
cd chatbot-gm-llm
```

### 2. Crear entorno virtual
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 3. Levantar Neo4j con Docker
```bash
docker compose -f docker/docker-compose.yml up -d neo4j
```

### 4. Ejecutar el chatbot (una vez entrenado el modelo)
```bash
uvicorn src/api/main:app --reload
chainlit run src/api/chatbot.py
```

---

## Cronograma (12 semanas)

| Fase | Semanas | Actividad | Responsable |
|---|---|---|---|
| I. Análisis y Setup | 1–2 | Configuración de entorno y análisis de docs BP/GMW | Todo el equipo |
| II. Procesamiento de datos | 3–4 | Limpieza de PDFs y generación de pares Q&A | Data Engineer |
| III. Desarrollo del modelo | 5–8 | Fine-tuning QLoRA de Llama 3 | ML Engineer |
| IV. Integración y lógica | 9–10 | Motor de búsqueda GraphRAG + interfaz | Backend Dev |
| V. Evaluación y pulido | 11–12 | Pruebas con set de evaluación GM | Todo el equipo |

---

## Notas importantes

- Los archivos PDF de BP/GMW son **confidenciales** — nunca subir a Git. Están en `.gitignore`.
- Los checkpoints de modelo (carpeta `models/`) tampoco se suben — demasiado pesados y confidenciales.
- Usar **Git LFS** si necesitan versionar datasets grandes.
- El código debe estar en **Python 3.10+**.

---

## Referencias

- [LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory)
- [Unsloth](https://github.com/unslothai/unsloth)
- [LlamaIndex PropertyGraphIndex](https://docs.llamaindex.ai/en/stable/examples/property_graph/)
- [vLLM](https://github.com/vllm-project/vllm)
- [Chainlit](https://github.com/Chainlit/chainlit)
- [Neo4j APOC](https://neo4j.com/labs/apoc/)
