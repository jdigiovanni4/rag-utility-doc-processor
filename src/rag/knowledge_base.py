"""RAG knowledge base management using ChromaDB."""

import os
import json
from pathlib import Path
from typing import List, Dict

import chromadb
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from config.settings import (
    FINAL_JSON_DIR,
    VECTOR_DB_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    EMBEDDING_BATCH_SIZE
)


def load_documents_from_json_dir(source_dir: Path) -> List[Document]:
    """Load all JSON files from directory as LangChain documents.
    
    Each JSON file is loaded as a single document to preserve context.
    
    Args:
        source_dir: Directory containing JSON files
        
    Returns:
        List of Document objects
    """
    all_docs = []
    
    if not source_dir.exists():
        return []
    
    json_files = list(source_dir.glob("*.json"))
    
    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            content_string = json.dumps(data, indent=2)
            doc = Document(
                page_content=content_string,
                metadata={"source": json_file.name}
            )
            all_docs.append(doc)
        
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {json_file.name}. Skipping.")
    
    return all_docs


def create_knowledge_base(documents: List[Document] = None) -> None:
    """Create and populate the vector database from JSON documents.
    
    Args:
        documents: Optional list of documents. If None, loads from FINAL_JSON_DIR.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set.")
    
    if documents is None:
        documents = load_documents_from_json_dir(FINAL_JSON_DIR)
    
    if not documents:
        print("No documents to embed.")
        return
    
    embedding_function = OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name=EMBEDDING_MODEL
    )
    
    client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function
    )
    
    langchain_embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    
    print(f"Populating database with {len(documents)} documents in batches...")
    
    for i in range(0, len(documents), EMBEDDING_BATCH_SIZE):
        batch_docs = documents[i:i + EMBEDDING_BATCH_SIZE]
        batch_num = i // EMBEDDING_BATCH_SIZE + 1
        total_batches = (len(documents) + EMBEDDING_BATCH_SIZE - 1) // EMBEDDING_BATCH_SIZE
        
        print(f"Processing batch {batch_num}/{total_batches}...")
        
        page_contents = [doc.page_content for doc in batch_docs]
        batch_embeddings = langchain_embeddings.embed_documents(page_contents)
        
        current_count = collection.count()
        ids = [f"doc_{current_count + j}" for j in range(len(batch_docs))]
        
        collection.add(
            ids=ids,
            embeddings=batch_embeddings,
            documents=page_contents,
            metadatas=[doc.metadata for doc in batch_docs]
        )
    
    print(f"Database populated. Total documents: {collection.count()}")


def update_knowledge_base(final_json_list: List[Dict]) -> None:
    """Add new documents to the existing knowledge base.
    
    Args:
        final_json_list: List of final JSON dictionaries to add
    """
    if not final_json_list:
        return
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set.")
    
    embedding_function = OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name=EMBEDDING_MODEL
    )
    
    client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function
    )
    
    docs_to_ingest = []
    for final_json in final_json_list:
        doc = Document(
            page_content=json.dumps(final_json, indent=2),
            metadata={"source": f"{final_json.get('documentId')}.json"}
        )
        docs_to_ingest.append(doc)
    
    if not docs_to_ingest:
        return
    
    langchain_embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    page_contents = [doc.page_content for doc in docs_to_ingest]
    embeddings = langchain_embeddings.embed_documents(page_contents)
    
    current_count = collection.count()
    ids = [f"doc_{current_count + i}" for i in range(len(docs_to_ingest))]
    
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=page_contents,
        metadatas=[doc.metadata for doc in docs_to_ingest]
    )
    
    print(f"Added {len(docs_to_ingest)} new document(s) to knowledge base.")


def query_knowledge_base(query_text: str, n_results: int = 15) -> List[str]:
    """Query the knowledge base for relevant documents.
    
    Args:
        query_text: Query string
        n_results: Number of results to return
        
    Returns:
        List of relevant document contents
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set.")
    
    embedding_function = OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name=EMBEDDING_MODEL
    )
    
    client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function
    )
    
    results = collection.query(query_texts=[query_text], n_results=n_results)
    return results["documents"][0] if results.get("documents") else []

