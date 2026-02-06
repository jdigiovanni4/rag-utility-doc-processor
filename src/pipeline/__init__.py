"""Main pipeline for processing utility documents."""

import os
from pathlib import Path
from typing import Callable, Optional

from config.settings import validate_environment, ensure_directories
from .pdf_processor import process_pdf_rotation
from .document_parser import parse_pdf_to_generic_json
from .json_converter import convert_to_final_json
from .qc_checker import check_single_document


def process_single_pdf(
    pdf_path: Path,
    status_callback: Optional[Callable[[str], None]] = None,
    skip_rotation: bool = False
) -> dict:
    """Process a single PDF through the complete pipeline.
    
    Pipeline stages:
    1. PDF rotation correction (optional)
    2. PDF to generic JSON conversion
    3. Generic JSON to structured final JSON
    4. QC checking and flagging
    
    Args:
        pdf_path: Path to source PDF file
        status_callback: Optional callback for status updates
        skip_rotation: If True, skip rotation correction step
        
    Returns:
        Final structured JSON as dictionary
    """
    validate_environment()
    ensure_directories()
    
    base_name = pdf_path.stem
    
    if skip_rotation:
        corrected_path = pdf_path
        if status_callback:
            status_callback("Skipping rotation correction (demo mode)")
    else:
        corrected_path = process_pdf_rotation(pdf_path, status_callback)
    
    generic_json_path = parse_pdf_to_generic_json(corrected_path, status_callback)
    
    final_json = convert_to_final_json(generic_json_path, base_name, status_callback)
    
    source_pdf = Path(pdf_path)
    check_single_document(final_json, source_pdf, status_callback)
    
    return final_json

