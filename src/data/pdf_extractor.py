"""
pdf_extractor.py
Extrae texto limpio de los PDFs de BP/GMW de General Motors.
Uso: python pdf_extractor.py --input data/raw/ --output data/processed/
"""

import os
import json
import argparse
from pathlib import Path
from loguru import logger
import pymupdf4llm


def extract_text_from_pdf(pdf_path: str) -> dict:
    """Extrae texto de un PDF y retorna un dict con metadata + contenido."""
    path = Path(pdf_path)
    logger.info(f"Procesando: {path.name}")

    # pymupdf4llm extrae en formato Markdown, ideal para LLMs
    md_text = pymupdf4llm.to_markdown(str(path))

    return {
        "filename": path.name,
        "source": str(path),
        "content": md_text,
        "char_count": len(md_text),
    }


def process_folder(input_dir: str, output_dir: str):
    """Procesa todos los PDFs de una carpeta y guarda JSON por cada uno."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    pdfs = list(input_path.glob("*.pdf"))
    if not pdfs:
        logger.warning(f"No se encontraron PDFs en {input_dir}")
        return

    logger.info(f"Encontrados {len(pdfs)} PDFs para procesar")
    results = []

    for pdf in pdfs:
        try:
            doc = extract_text_from_pdf(str(pdf))
            results.append(doc)

            # Guardar JSON individual por documento
            out_file = output_path / (pdf.stem + ".json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(doc, f, ensure_ascii=False, indent=2)

            logger.success(f"Guardado: {out_file.name} ({doc['char_count']} chars)")

        except Exception as e:
            logger.error(f"Error procesando {pdf.name}: {e}")

    # Guardar también un archivo consolidado
    consolidated_path = output_path / "all_documents.json"
    with open(consolidated_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    logger.success(f"Consolidado guardado: {consolidated_path}")
    logger.info(f"Total procesados: {len(results)}/{len(pdfs)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extractor de PDFs BP/GMW")
    parser.add_argument("--input", default="data/raw/", help="Carpeta con PDFs")
    parser.add_argument("--output", default="data/processed/", help="Carpeta de salida")
    args = parser.parse_args()

    process_folder(args.input, args.output)
