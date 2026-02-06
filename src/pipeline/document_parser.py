"""PDF to generic JSON conversion using AgenticDoc."""

import json
from pathlib import Path
from agentic_doc.parse import parse

from config.settings import GENERIC_JSON_DIR


def parse_pdf_to_generic_json(pdf_path: Path, status_callback=None) -> Path:
    """Convert PDF to generic JSON format using AgenticDoc.
    
    Args:
        pdf_path: Path to PDF file
        status_callback: Optional callback function for status updates
        
    Returns:
        Path to generated generic JSON file
    """
    GENERIC_JSON_DIR.mkdir(parents=True, exist_ok=True)
    
    if status_callback:
        status_callback(f"Running AgenticDoc for {pdf_path.name}...")
    
    results = parse(
        [str(pdf_path)],
        include_marginalia=False,
        include_metadata_in_markdown=False
    )
    
    base_name = pdf_path.stem
    output_path = GENERIC_JSON_DIR / f"{base_name}.json"
    
    chunks_data = [chunk.dict() for chunk in results[0].chunks]
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks_data, f, indent=2)
    
    return output_path

