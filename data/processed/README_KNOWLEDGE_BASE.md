# Base de Conocimiento Estructurada — Best Practices GM Interior Trim Design

## 📋 Descripción

Esta carpeta contiene la base de conocimiento estructurada y preparada para un sistema **RAG (Retrieval Augmented Generation)** con **Neo4j GraphRAG**. Todos los datos provienen del documento confidencial `26A Best Practices_Modified.docx` de General Motors.

---

## 📁 Archivos de la Base de Conocimiento

### 1. `bp_chunks.json`
**Propósito:** Fragmentación semántica del contenido en bloques recuperables.

**Estructura:**
```json
{
  "metadata": {...},
  "chunks": [
    {
      "id": "C01",
      "title": "BP 1: ...",
      "content": "Descripción del requisito",
      "keywords": ["palabra_clave_1", ...],
      "category": "Categoría temática",
      "priority": "Alta/Media/Baja",
      "consequence": "Impacto de no cumplir",
      "requirements": {...}
    }
  ]
}
```

**Uso:**
- Indexar en motor de búsqueda (Elasticsearch, FAISS, etc.)
- Crear embeddings para recuperación semántica
- Servir como chunks de contexto en prompts RAG

**Contenido:**
- 7 Best Practices (C01-C07)
- Cada chunk incluye criterios técnicos, límites dimensionales, y consecuencias

---

### 2. `bp_entities.json`
**Propósito:** Extracción de entidades para construcción del grafo de conocimiento.

**Estructura:**
```json
{
  "entity_types": {
    "components": [...],
    "technical_concepts": [...],
    "vehicle_segments": [...],
    "organizations": [...]
  }
}
```

**Uso:**
- Crear nodos en Neo4j
- Validar referencias cruzadas entre documentos
- Construir índice de términos técnicos

**Entidades incluidas:**
- 12 componentes (Panel de Puerta, Tirador, Cinturón, etc.)
- 8 conceptos técnicos (Torque, Clearance, M4.2, etc.)
- 2 segmentos de vehículos (Coupe, Convertible)
- Organizaciones (GM, UEAMex)

---

### 3. `bp_relationships.json`
**Propósito:** Relaciones entre entidades, listas para importación a Neo4j.

**Estructura:**
```json
{
  "relationships": [
    {
      "id": "R01",
      "source": "Panel de Puerta",
      "relationship": "TIENE_INTERFAZ_CON",
      "target": "Asientos",
      "bp_reference": "BP1",
      "cypher_format": "(Panel de Puerta)-[:TIENE_INTERFAZ_CON]->(Asientos)"
    }
  ]
}
```

**Uso:**
- Importar directamente en Neo4j con Cypher
- Construir grafo de conocimiento
- Realizar consultas de relaciones para RAG

**Relaciones incluidas:**
- 12 relaciones temáticas
- Cada relación incluye restricciones técnicas
- Algunos marcados como "mutuamente excluyentes" (tirador vs. taza)

---

### 4. `bp_qa_pairs.json`
**Propósito:** Pares pregunta-respuesta para entrenamiento y validación de RAG.

**Estructura:**
```json
{
  "qa_pairs": [
    {
      "id": "Q001",
      "question": "¿Pregunta?",
      "answer": "Respuesta exacta del documento",
      "bp_reference": "BP1",
      "category": "Categoría temática",
      "difficulty": "Básico/Medio/Alto"
    }
  ]
}
```

**Uso:**
- Fine-tuning de modelos de lenguaje
- Evaluación de retrieval (RAGAS, etc.)
- Validación de respuestas del chatbot

**Contenido:**
- 15 Q&A pairs
- Dificultad variada (básico → avanzado)
- Cobertura de todos los BPs

---

## 🔄 Flujo de Integración con el Proyecto

### Fase 1: Carga Inicial en Neo4j
```bash
# 1. Cargar entidades como nodos
python -c "
import json
from neo4j import GraphDatabase

# Leer entities
with open('data/processed/bp_entities.json') as f:
    entities = json.load(f)

# Crear nodos en Neo4j (TODO)
"

# 2. Cargar relaciones como edges
# python scripts/load_relationships_to_neo4j.py
```

### Fase 2: Indexar Chunks para Retrieval
```python
# Usar chunks para crear embeddings
from llama_index import Document, VectorStoreIndex

chunks_data = json.load(open('data/processed/bp_chunks.json'))
documents = [
    Document(text=chunk['content'], 
             metadata={
                 'id': chunk['id'],
                 'title': chunk['title'],
                 'bp': chunk['id'],
                 'priority': chunk['priority']
             })
    for chunk in chunks_data['chunks']
]

index = VectorStoreIndex.from_documents(documents)
```

### Fase 3: Usar Q&A para Validación
```python
# Evaluar retrieval con RAGAS
from ragas.metrics import faithfulness, answer_relevancy
from ragas.run_on_dataset import evaluate

qa_data = json.load(open('data/qa_pairs/bp_qa_pairs.json'))

# Crear dataset para evaluación
dataset = {
    'question': [q['question'] for q in qa_data['qa_pairs']],
    'ground_truth': [q['answer'] for q in qa_data['qa_pairs']]
}

results = evaluate(dataset, retriever, llm_model)
```

---

## 🛠️ Scripts Recomendados para Implementación

### Script 1: Cargar Entidades y Relaciones a Neo4j
```python
# src/graph/load_bp_knowledge.py
import json
from neo4j import GraphDatabase

def load_entities_to_neo4j(driver):
    with open('data/processed/bp_entities.json') as f:
        entities_data = json.load(f)
    
    with driver.session() as session:
        # Crear nodos COMPONENTE
        for component in entities_data['entity_types']['components']:
            session.run("""
                CREATE (c:COMPONENTE {
                    name: $name,
                    description: $description,
                    category: $category
                })
            """, name=component['name'], 
                description=component['description'],
                category=component['category'])

def load_relationships_to_neo4j(driver):
    with open('data/processed/bp_relationships.json') as f:
        rels_data = json.load(f)
    
    with driver.session() as session:
        for rel in rels_data['relationships']:
            # Aquí ejecutar comando Cypher del formato cypher_format
            pass
```

### Script 2: Crear Embeddings de Chunks
```python
# src/data/embed_chunks.py
import json
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('multilingual-MiniLM-L12-v2')

with open('data/processed/bp_chunks.json') as f:
    chunks = json.load(f)['chunks']

embeddings = []
for chunk in chunks:
    emb = model.encode(chunk['content'])
    embeddings.append({
        'chunk_id': chunk['id'],
        'embedding': emb.tolist()
    })

with open('data/processed/bp_chunks_embeddings.json', 'w') as f:
    json.dump(embeddings, f)
```

### Script 3: Validar RAG con Q&A
```python
# src/evaluation/validate_rag.py
import json
from ragas.metrics import AnswerRelevancy
from ragas import evaluate

qa_pairs = json.load(open('data/qa_pairs/bp_qa_pairs.json'))['qa_pairs']

# Crear dataset RAGAS
dataset_dict = {
    'question': [q['question'] for q in qa_pairs],
    'ground_truth': [q['answer'] for q in qa_pairs]
}

# Evaluar retrieval del RAG
# results = evaluate(dataset_dict, metrics=[answer_relevancy])
```

---

## 📊 Estadísticas de la Base de Conocimiento

| Métrica | Valor |
|---------|-------|
| **Chunks Semánticos** | 7 |
| **Entidades Totales** | 23 |
| **Relaciones** | 12 |
| **Pares Q&A** | 15 |
| **Palabras Clave Únicas** | ~50 |
| **Categorías Temáticas** | 8 |
| **Best Practices Cubiertos** | 7 (BP1-BP7) |

---

## 🔐 Consideraciones de Seguridad

⚠️ **CONFIDENCIALIDAD: DOCUMENTO PROPIETARIO GM**

- ✅ No distribuir fuera del equipo del proyecto
- ✅ No subir a repositorios públicos
- ✅ Incluir en `.gitignore` (ya configurado)
- ✅ Usar solo bajo NDA (Non-Disclosure Agreement)
- ✅ Acceso restringido al servidor de producción

---

## 📝 Próximos Pasos

1. **Implementar carga en Neo4j** → Usar `bp_entities.json` + `bp_relationships.json`
2. **Crear vector index** → Usar `bp_chunks.json` para embeddings
3. **Validar retrieval** → Usar `bp_qa_pairs.json` con métricas RAGAS
4. **Conectar al chatbot** → Integrar pipeline RAG en `src/graph/rag_pipeline.py`
5. **Fine-tuning del modelo** → Usar `bp_qa_pairs.json` como datos de entrenamiento

---

## 📚 Referencias

- [LlamaIndex PropertyGraphIndex](https://docs.llamaindex.ai/en/stable/examples/property_graph/)
- [Neo4j Cypher Guide](https://neo4j.com/docs/cypher-manual/current/)
- [RAGAS Evaluation Framework](https://docs.ragas.io/)
- [HuggingFace Datasets](https://huggingface.co/docs/datasets)

---

**Documento creado:** 2025-05-25  
**Última actualización:** 2025-05-25  
**Versión Base de Conocimiento:** 1.0
