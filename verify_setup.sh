#!/bin/bash

# Script de verificacion del proyecto Chatbot GM LLM
# Uso: bash verify_setup.sh

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Verificando configuracion del proyecto Chatbot GM LLM..."
echo ""

check_python() {
    echo "- Verificando Python..."
    if command -v python3 &> /dev/null; then
        VERSION=$(python3 --version)
        echo -e "${GREEN} $VERSION encontrado${NC}"
        return 0
    fi
    echo -e "${RED} Python 3.10+ no encontrado${NC}"
    return 1
}

check_venv() {
    echo "- Verificando entorno virtual..."
    if [ -d ".venv" ]; then
        echo -e "${GREEN} Entorno virtual (.venv) encontrado${NC}"
        if [ -z "$VIRTUAL_ENV" ]; then
            echo -e "${YELLOW} Entorno no activado. Ejecuta: source .venv/bin/activate${NC}"
        else
            echo -e "${GREEN} Entorno activado${NC}"
        fi
        return 0
    fi
    echo -e "${RED} Entorno virtual no encontrado${NC}"
    return 1
}

check_modules() {
    echo "- Verificando modulos Python..."
    python -c "import chainlit; print('  Chainlit OK')" 2>/dev/null || echo -e "${RED}  Chainlit no instalado${NC}"
    python -c "import neo4j; print('  Neo4j OK')" 2>/dev/null || echo -e "${RED}  Neo4j no instalado${NC}"
    python -c "import langchain_neo4j; print('  LangChain-Neo4j OK')" 2>/dev/null || echo -e "${RED}  LangChain-Neo4j no instalado${NC}"
    python -c "import langchain_huggingface; print('  LangChain-HF OK')" 2>/dev/null || echo -e "${RED}  LangChain-HuggingFace no instalado${NC}"
}

check_docker() {
    echo "- Verificando Docker..."
    if command -v docker &> /dev/null; then
        echo -e "${GREEN} Docker instalado${NC}"
        if docker ps &> /dev/null; then
            echo -e "${GREEN} Docker daemon corriendo${NC}"
        else
            echo -e "${RED} Docker daemon no esta corriendo${NC}"
        fi
    else
        echo -e "${RED} Docker no instalado${NC}"
    fi
}

check_files() {
    echo "- Verificando archivos del proyecto..."

    FILES=(
        "requirements.txt"
        "app.py"
        "src/graph/rag_pipeline.py"
        "src/graph/load_bp_knowledge.py"
        "docker/docker-compose.yml"
        "docker/Dockerfile"
        "data/processed/bp_chunks.json"
        "data/processed/bp_entities.json"
        "data/processed/bp_relationships.json"
        "data/qa_pairs/bp_qa_pairs.json"
    )

    for file in "${FILES[@]}"; do
        if [ -f "$file" ]; then
            echo -e "${GREEN}  $file${NC}"
        else
            echo -e "${RED}  $file NO ENCONTRADO${NC}"
        fi
    done
}

check_neo4j() {
    echo "- Verificando Neo4j..."
    if command -v docker &> /dev/null; then
        if docker ps | grep -q "neo4j"; then
            echo -e "${GREEN} Neo4j esta corriendo${NC}"
        else
            echo -e "${YELLOW} Neo4j no esta corriendo${NC}"
            echo "   docker compose -f docker/docker-compose.yml up -d neo4j"
        fi
    fi
}

check_env() {
    echo "- Verificando .env..."
    if [ -f ".env" ]; then
        echo -e "${GREEN} .env encontrado${NC}"
    else
        echo -e "${YELLOW} .env no encontrado. Copia .env.example a .env${NC}"
    fi
}

main() {
    check_python || exit 1
    check_venv || exit 1
    check_modules
    check_docker
    check_files
    check_neo4j
    check_env

    echo ""
    echo -e "${GREEN} Verificacion completada${NC}"
    echo ""
    echo "Proximos pasos:"
    echo "   1. docker compose -f docker/docker-compose.yml up -d neo4j"
    echo "   2. python src/graph/load_bp_knowledge.py"
    echo "   3. chainlit run app.py --port 8001"
}

main
