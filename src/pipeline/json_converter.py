"""Convert generic JSON to structured final JSON using LLM."""

import json
from pathlib import Path
from openai import OpenAI

from config.settings import PROMPT_FILE, FINAL_JSON_DIR, LLM_MODEL, LLM_TEMPERATURE


def load_prompt_template() -> str:
    """Load the extraction prompt template."""
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(f"Prompt file not found: {PROMPT_FILE}")
    
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()


def convert_to_final_json(
    generic_json_path: Path,
    document_id: str,
    status_callback=None
) -> dict:
    """Convert generic JSON to structured final JSON using OpenAI.
    
    Args:
        generic_json_path: Path to generic JSON file
        document_id: Document identifier
        status_callback: Optional callback function for status updates
        
    Returns:
        Final structured JSON as dictionary
    """
    FINAL_JSON_DIR.mkdir(parents=True, exist_ok=True)
    
    if status_callback:
        status_callback(f"Structuring data with OpenAI for {generic_json_path.name}...")
    
    prompt_template = load_prompt_template()
    
    with open(generic_json_path, "r", encoding="utf-8") as f:
        generic_json_content = f.read()
    
    prompt = prompt_template.replace("{{generic_json_content}}", generic_json_content)
    prompt = prompt.replace("{{document_id_placeholder}}", document_id)
    
    client = OpenAI()
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=LLM_TEMPERATURE,
        response_format={"type": "json_object"}
    )
    
    final_json_str = response.choices[0].message.content
    final_json_obj = json.loads(final_json_str)
    
    output_path = FINAL_JSON_DIR / f"{document_id}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_json_obj, f, indent=2)
    
    return final_json_obj

