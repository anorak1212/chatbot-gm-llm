# Guia de Instalacion — Chatbot GM LLM

## Instalacion Rapida

### Paso 1: Crear entorno virtual
```bash
python3.10 -m venv .venv
source .venv/bin/activate
```

### Paso 2: Instalar dependencias
```bash
pip install -r requirements.txt
```

### Paso 3: Configurar variables de entorno
```bash
cp .env.example .env
# Edita .env — especialmente LM_STUDIO_URL y NEO4J_PASSWORD
```

### Paso 4: Iniciar Neo4j con Docker
```bash
docker compose -f docker/docker-compose.yml up -d neo4j
# Espera 15-20 segundos
```

Neo4j estara disponible en:
- Bolt: `bolt://localhost:7687`
- Browser: `http://localhost:7474`
- Credenciales: `neo4j / admin1234`

### Paso 5: Cargar la base de conocimiento
```bash
python src/graph/load_bp_knowledge.py
```

Se cargaran 7 chunks, 23 entidades y 12 relaciones.

### Paso 6: Iniciar LM Studio
Asegurate de tener **Gemma-4-e4b-it** cargado y el servidor corriendo en la URL configurada en `.env`.

### Paso 7: Probar la interfaz
```bash
chainlit run app.py --port 8001 -w
```

Disponible en: `http://localhost:8001`

---

## Verificacion

```bash
python -c "
import chainlit, neo4j, langchain_neo4j, langchain_huggingface, langchain_openai
print('All imports OK')
"
```

---

## Solucion de Problemas

### Error: `No module named 'neo4j'`
```bash
pip install neo4j>=5.23.0
```

### Error: Neo4j no conecta
Verifica que Docker este corriendo y que `NEO4J_PASSWORD` en `.env` coincida con `docker-compose.yml` (`admin1234`).

### Error: LM Studio no responde
Verifica que `LM_STUDIO_URL` en `.env` apunte a la IP correcta y que el modelo este cargado.

### Error de compilacion de paquetes
```bash
sudo apt-get install build-essential python3.10-dev
```
