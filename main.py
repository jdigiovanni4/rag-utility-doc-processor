"""Main entry point for batch processing PDFs through the pipeline."""

import sys
from pathlib import Path

from config.settings import SOURCE_PDF_DIR, ensure_directories, validate_environment
from src.pipeline import process_single_pdf
from src.rag import create_knowledge_base


def main():
    """Process all PDFs in source directory."""
    validate_environment()
    ensure_directories()
    
    pdf_files = list(SOURCE_PDF_DIR.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {SOURCE_PDF_DIR}")
        return
    
    print(f"Found {len(pdf_files)} PDF(s) to process.\n")
    
    processed_json_list = []
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] Processing {pdf_path.name}...")
        
        def status_callback(message):
            print(f"  {message}")
        
        try:
            final_json = process_single_pdf(pdf_path, status_callback)
            processed_json_list.append(final_json)
            print(f"  ✓ Completed {pdf_path.name}\n")
        except Exception as e:
            print(f"  ✗ Error processing {pdf_path.name}: {e}\n")
    
    if processed_json_list:
        print("Updating knowledge base...")
        from src.rag import update_knowledge_base
        update_knowledge_base(processed_json_list)
        print("Knowledge base updated.")
    
    print(f"\nPipeline complete. Processed {len(processed_json_list)} document(s).")


if __name__ == "__main__":
    main()

