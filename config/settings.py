"""Configuration settings for the utility document processing pipeline."""

import os
from pathlib import Path

# Base project directory
PROJECT_ROOT = Path(__file__).parent.parent

# Directory paths
SOURCE_PDF_DIR = PROJECT_ROOT / "source_pdfs"
CORRECTED_PDF_DIR = PROJECT_ROOT / "corrected_pdfs"
GENERIC_JSON_DIR = PROJECT_ROOT / "generic_json_outputs"
FINAL_JSON_DIR = PROJECT_ROOT / "final_json_outputs"
REVIEW_DIR = PROJECT_ROOT / "manual_review_needed"
VECTOR_DB_DIR = PROJECT_ROOT / "vector_db"

# Vector database settings
COLLECTION_NAME = "utility_docs"
EMBEDDING_MODEL = "text-embedding-3-small"

# LLM settings
LLM_MODEL = "gpt-4o"
LLM_TEMPERATURE = 0.0

# Prompt file
PROMPT_FILE = PROJECT_ROOT / "prompts" / "extraction_prompt.txt"

# Batch processing settings
EMBEDDING_BATCH_SIZE = 100

# Required environment variables
REQUIRED_ENV_VARS = ["OPENAI_API_KEY", "VISION_AGENT_API_KEY"]

def validate_environment():
    """Check that all required environment variables are set."""
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    return True

def ensure_directories():
    """Create all necessary directories if they don't exist."""
    directories = [
        SOURCE_PDF_DIR,
        CORRECTED_PDF_DIR,
        GENERIC_JSON_DIR,
        FINAL_JSON_DIR,
        REVIEW_DIR,
        VECTOR_DB_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

