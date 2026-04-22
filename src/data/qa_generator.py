"""
qa_generator.py
Convierte los documentos BP/GMW procesados en pares pregunta-respuesta
en formato ShareGPT para el fine-tuning con Unsloth/LLaMA-Factory.

Uso: python qa_generator.py --input data/processed/ --output data/qa_pairs/
"""

import os
import json
import argparse
from pathlib import Path
from loguru import logger


# Plantilla ShareGPT — el formato que espera Unsloth/LLaMA-Factory
def to_sharegpt_format(question: str, answer: str, system_prompt: str) -> dict:
    return {
        "conversations": [
            {"from": "system", "value": system_prompt},
            {"from": "human", "value": question},
            {"from": "gpt", "value": answer},
        ]
    }


SYSTEM_PROMPT = (
    "Eres un asistente experto en los procedimientos de Mejores Prácticas (BPs) "
    "y Guías de Manufactura en Obra (GMWs) de General Motors. "
    "Responde de forma precisa, técnica y basada únicamente en los documentos oficiales de GM. "
    "Si no tienes información suficiente, indícalo claramente."
)


def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200) -> list[str]:
    """Divide el texto en chunks con overlap para no perder contexto."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def generate_qa_from_chunk(chunk: str, doc_name: str, chunk_idx: int) -> dict:
    """
    Genera un par Q&A a partir de un chunk de texto.
    
    NOTA: En producción esto se puede automatizar con un LLM más grande
    (ej. GPT-4 o Claude) para generar preguntas de forma automática.
    Por ahora genera pares estructurados para revisión manual del equipo.
    """
    # Formato base — el equipo completará las preguntas reales
    # después de revisar los documentos BP/GMW
    qa = to_sharegpt_format(
        question=f"[REVISAR] ¿Qué información contiene el documento {doc_name} en la sección {chunk_idx + 1}?",
        answer=chunk.strip(),
        system_prompt=SYSTEM_PROMPT,
    )
    qa["_meta"] = {
        "source": doc_name,
        "chunk_index": chunk_idx,
        "status": "pending_review",  # El equipo cambia a "approved" al validar
    }
    return qa


def process_documents(input_dir: str, output_dir: str, chunk_size: int = 1500):
    """Procesa todos los JSONs de documentos y genera el dataset de Q&A."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    json_files = [f for f in input_path.glob("*.json") if f.name != "all_documents.json"]

    if not json_files:
        logger.warning(f"No se encontraron JSONs en {input_dir}")
        return

    logger.info(f"Procesando {len(json_files)} documentos")
    all_qa_pairs = []

    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as f:
            doc = json.load(f)

        doc_name = doc["filename"]
        content = doc["content"]
        chunks = chunk_text(content, chunk_size=chunk_size)

        logger.info(f"{doc_name}: {len(chunks)} chunks generados")

        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 100:  # Ignorar chunks muy pequeños
                continue
            qa = generate_qa_from_chunk(chunk, doc_name, i)
            all_qa_pairs.append(qa)

    # Guardar en formato JSONL (un objeto por línea — estándar para fine-tuning)
    output_file = output_path / "gm_qa_dataset.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for pair in all_qa_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    # También guardar versión JSON legible para revisión
    review_file = output_path / "gm_qa_dataset_review.json"
    with open(review_file, "w", encoding="utf-8") as f:
        json.dump(all_qa_pairs, f, ensure_ascii=False, indent=2)

    logger.success(f"Dataset generado: {len(all_qa_pairs)} pares Q&A")
    logger.info(f"JSONL para training: {output_file}")
    logger.info(f"JSON para revisión: {review_file}")
    logger.warning("IMPORTANTE: Revisar y aprobar los pares antes del fine-tuning")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador de pares Q&A para fine-tuning GM")
    parser.add_argument("--input", default="data/processed/", help="Carpeta con JSONs procesados")
    parser.add_argument("--output", default="data/qa_pairs/", help="Carpeta de salida")
    parser.add_argument("--chunk-size", type=int, default=1500, help="Tamaño de chunks en caracteres")
    args = parser.parse_args()

    process_documents(args.input, args.output, args.chunk_size)
