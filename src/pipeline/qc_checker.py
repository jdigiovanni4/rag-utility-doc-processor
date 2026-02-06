"""Quality control checking and flagging of extracted documents."""

import json
import shutil
from pathlib import Path

from config.settings import FINAL_JSON_DIR, SOURCE_PDF_DIR, REVIEW_DIR


def check_and_flag_documents(status_callback=None) -> tuple[int, int]:
    """Check all final JSON files for QC flags and move flagged PDFs to review.
    
    Args:
        status_callback: Optional callback function for status updates
        
    Returns:
        Tuple of (total_count, flagged_count)
    """
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    
    if not FINAL_JSON_DIR.exists():
        raise FileNotFoundError(
            f"Final JSON directory not found: {FINAL_JSON_DIR}. "
            "Run JSON conversion first."
        )
    
    flagged_count = 0
    total_count = 0
    
    for json_file in FINAL_JSON_DIR.glob("*.json"):
        total_count += 1
        
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
            
            if data.get("_qc_flag") is True:
                flagged_count += 1
                reason = data.get("_qc_reason", "No reason specified")
                
                if status_callback:
                    status_callback(f"FLAGGED: {json_file.name} - {reason}")
                
                doc_id = json_file.stem
                original_pdf_path = SOURCE_PDF_DIR / f"{doc_id}.pdf"
                destination_path = REVIEW_DIR / f"{doc_id}.pdf"
                
                if original_pdf_path.exists():
                    shutil.move(str(original_pdf_path), str(destination_path))
                    if status_callback:
                        status_callback(f"Moved {doc_id}.pdf to review folder")
                else:
                    if status_callback:
                        status_callback(f"Warning: Could not find PDF for {doc_id}")
        
        except Exception as e:
            if status_callback:
                status_callback(f"Error reading {json_file.name}: {e}")
    
    return total_count, flagged_count


def check_single_document(json_data: dict, pdf_path: Path, status_callback=None) -> bool:
    """Check a single document and move to review if flagged.
    
    Args:
        json_data: Final JSON data
        pdf_path: Path to source PDF
        status_callback: Optional callback function for status updates
        
    Returns:
        True if flagged, False otherwise
    """
    if json_data.get("_qc_flag") is True:
        REVIEW_DIR.mkdir(parents=True, exist_ok=True)
        
        reason = json_data.get("_qc_reason", "No reason specified")
        if status_callback:
            status_callback(f"QC Flag: {reason}")
        
        destination_path = REVIEW_DIR / pdf_path.name
        if pdf_path.exists():
            shutil.move(str(pdf_path), str(destination_path))
        
        return True
    return False

