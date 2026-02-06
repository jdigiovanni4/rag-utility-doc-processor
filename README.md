# Utility Document Processing Pipeline

An end-to-end system for extracting structured data from utility bills and contracts using Agentic RAG. Processes PDFs through OCR, structured extraction, quality control, and builds a searchable knowledge base.

This is a truncated demonstration of the entire project. The pipeline and agent cannot be run at this time due to the private and sensitive financial energy data used.

## Features

- **PDF Preprocessing**: Automatic rotation correction and deskewing
- **Document Parsing**: Converts PDFs to structured JSON using AgenticDoc
- **LLM Extraction**: Extracts structured data (usage history, locations, charges) using GPT-4
- **Quality Control**: Automatic flagging of documents requiring manual review
- **RAG Knowledge Base**: Vector database for semantic search and Q&A
- **Web Interface**: Streamlit app for document upload and querying

## Architecture

```
PDF → Rotation Fix → Generic JSON → Structured JSON → QC Check → Knowledge Base
```

1. **PDF Processing**: Corrects rotation/skew using OCRmyPDF
2. **Document Parsing**: Converts to generic JSON chunks using AgenticDoc
3. **Structured Extraction**: Uses GPT-4 to extract structured fields per schema
4. **Quality Control**: Flags documents with missing or suspicious data
5. **Knowledge Base**: Ingests structured JSON into ChromaDB for RAG queries

## Installation

### Prerequisites

Install system dependencies:

```bash
brew install tesseract poppler  # macOS
# or
sudo apt-get install tesseract-ocr poppler-utils  # Linux
```

### Python Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd Automated-Utility-Bill-and-Contract-Processing-using-Agentic-RAG
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set environment variables:
```bash
export OPENAI_API_KEY="your-openai-key"
export VISION_AGENT_API_KEY="your-vision-agent-key"
```

## Usage

### Command Line

Process all PDFs in the `source_pdfs/` directory:

```bash
python main.py
```

The pipeline will:
- Process each PDF through all stages
- Save structured JSON to `final_json_outputs/`
- Move flagged PDFs to `manual_review_needed/`
- Update the knowledge base

### Web Interface

Launch the Streamlit app:

```bash
streamlit run app.py
```

Features:
- **Query Knowledge Base**: Ask questions about processed documents
- **Upload Documents**: Process new PDFs with progress tracking
- **Demo Mode**: Skip rotation correction for faster processing

### Programmatic API

```python
from pathlib import Path
from src.pipeline import process_single_pdf
from src.rag import update_knowledge_base, query_knowledge_base

# Process a single PDF
pdf_path = Path("source_pdfs/document_123.pdf")
result = process_single_pdf(pdf_path, skip_rotation=False)

# Update knowledge base
update_knowledge_base([result])

# Query knowledge base
results = query_knowledge_base("What is the total usage for account 12345?")
```

## Project Structure

```
.
├── src/
│   ├── pipeline/          # Core processing modules
│   │   ├── pdf_processor.py      # PDF rotation correction
│   │   ├── document_parser.py    # PDF to generic JSON
│   │   ├── json_converter.py     # Generic to structured JSON
│   │   └── qc_checker.py         # Quality control
│   └── rag/               # RAG knowledge base
│       └── knowledge_base.py
├── config/
│   └── settings.py        # Configuration and paths
├── prompts/
│   └── extraction_prompt.txt
├── main.py                # CLI entry point
├── app.py                 # Streamlit web app
└── requirements.txt
```

## Output Schema

Extracted documents follow this JSON schema:

- `documentId`: Unique document identifier
- `issuer`: Utility company name
- `documentType`: "sampleBill" or "contract"
- `customerName`: Customer name
- `locations`: Array of service locations with:
  - `accountNumber`, `serviceAddress`, `meterNumber`
  - `usageHistory`: Monthly usage array
  - Charges and rates
- `usageHistory`: Document-level usage history
- `_qc_flag`: Boolean flag for manual review
- `_qc_reason`: Reason for flagging (if flagged)

## Quality Control

Documents are automatically flagged for manual review if:
- Missing issuer, customer name, or service addresses
- Missing total usage on bills
- No usage history table found
- All usage values are zero

Flagged documents are moved to `manual_review_needed/` directory.

## Configuration

Edit `config/settings.py` to customize:
- Directory paths
- LLM model and temperature
- Embedding model
- Batch sizes
- Vector database settings

## Requirements

- Python 3.8+
- OpenAI API key
- Vision Agent API key (for AgenticDoc)
- Tesseract OCR
- Poppler (for PDF processing)

## License

[Add your license here]

## Acknowledgments

Developed as part of the Applied Data Science Master's program at University of Chicago, in collaboration with PowerKiosk.
