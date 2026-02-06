"""Streamlit web application for document processing and RAG queries."""

__import__("pysqlite3")
import sys
sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

import streamlit as st
import os
import json
import pandas as pd
import shutil
from pathlib import Path
from openai import OpenAI

from config.settings import SOURCE_PDF_DIR, CORRECTED_PDF_DIR, GENERIC_JSON_DIR, validate_environment
from src.pipeline import process_single_pdf
from src.rag import update_knowledge_base, query_knowledge_base


st.set_page_config(
    layout="wide",
    page_title="Document Intelligence Pipeline",
    page_icon="🤖"
)

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        background-color: #FFFFFF !important;
    }
    h1, h2, h3, h4, h5, h6, p, li, label, .st-emotion-cache-16idsys p {
        color: #1d1d1f !important;
    }
    [data-testid="stInfo"] {
        background-color: #e9f5ff;
        border-radius: 10px;
        border: 1px solid #cce5ff;
    }
    [data-testid="stInfo"] p {
        color: #004085 !important;
    }
    [data-testid="stTextInput"] input {
        background-color: #FFFFFF !important;
        color: #1d1d1f !important;
        border: 1px solid #d2d2d7 !important;
        border-radius: 8px !important;
    }
    [data-testid="stTabs"] button {
        color: #888888;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        color: #0071e3;
        border-bottom: 2px solid #0071e3;
    }
    .stButton>button {
        border-radius: 8px;
        border: 1px solid #0071e3;
        background-color: #0071e3;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)


def generate_answer(query_text: str, retrieved_docs: list) -> str:
    """Generate answer from retrieved documents using OpenAI."""
    if not retrieved_docs:
        return "I couldn't find any relevant documents to answer that."
    
    client = OpenAI()
    context_str = "\n\n---\n\n".join(retrieved_docs)
    system_prompt = (
        "You are an expert Q&A system. Answer the user's question based ONLY on "
        "the provided context documents. If the answer isn't in the context, say so."
    )
    user_prompt = f"CONTEXT DOCUMENTS:\n{context_str}\n\nUSER'S QUESTION:\n{query_text}\n\nANSWER:"
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0
    )
    return response.choices[0].message.content


def cleanup_intermediate_folders():
    """Clear intermediate processing directories."""
    dirs_to_clean = [SOURCE_PDF_DIR, CORRECTED_PDF_DIR, GENERIC_JSON_DIR]
    for directory in dirs_to_clean:
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True, exist_ok=True)


st.title("Document Intelligence Pipeline")
st.write("An end-to-end solution for ingesting, structuring, and querying utility documents.")

try:
    validate_environment()
except ValueError as e:
    st.error(f"Configuration Error: {e}")
    st.stop()

if "processed_data" not in st.session_state:
    st.session_state.processed_data = []

tab1, tab2 = st.tabs(["Query Knowledge Base", "Add New Documents"])

with tab1:
    st.header("Ask a Question")
    st.info("The knowledge base is ready. Ask any question about the ingested documents.")
    
    query = st.text_input("Enter your question:", key="rag_query")
    
    if query:
        with st.spinner("Searching..."):
            retrieved = query_knowledge_base(query)
            answer = generate_answer(query, retrieved)
            st.success("Answer:")
            st.markdown(answer)

with tab2:
    st.header("Upload and Process New PDFs")
    
    demo_mode = st.checkbox(
        "🚀 Enable Fast Demo Mode (skips slow rotation fix)",
        value=True
    )
    
    if demo_mode:
        st.warning(
            "Demo Mode is ON. Results for rotated or skewed documents may be inaccurate.",
            icon="⚠️"
        )
    else:
        st.success("Full Accuracy Mode is ON. All processing steps will run.", icon="✅")
    
    uploaded_files = st.file_uploader(
        "Choose PDF files to add to the knowledge base",
        type="pdf",
        accept_multiple_files=True
    )
    
    if st.button("Process Uploaded Files"):
        if uploaded_files:
            cleanup_intermediate_folders()
            
            saved_file_paths = []
            for uploaded_file in uploaded_files:
                file_path = SOURCE_PDF_DIR / uploaded_file.name
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                saved_file_paths.append(file_path)
            
            st.session_state.processed_data = []
            processed_json_list = []
            progress_bar = st.progress(0, text="Starting pipeline...")
            status_text = st.empty()
            
            for i, file_path in enumerate(saved_file_paths):
                filename = file_path.name
                progress_percentage = i / len(saved_file_paths)
                progress_bar.progress(
                    progress_percentage,
                    text=f"Processing file {i+1}/{len(saved_file_paths)}: {filename}"
                )
                
                def status_callback(message):
                    status_text.info(f"File: {filename} - {message}")
                
                try:
                    final_json = process_single_pdf(
                        file_path,
                        status_callback,
                        skip_rotation=demo_mode
                    )
                    processed_json_list.append(final_json)
                except Exception as e:
                    status_text.error(f"Error processing {filename}: {e}")
            
            if processed_json_list:
                status_text.info("All files processed. Updating knowledge base...")
                progress_bar.progress(95, text="Updating knowledge base...")
                update_knowledge_base(processed_json_list)
                
                st.session_state.processed_data = processed_json_list
                progress_bar.progress(100, text="Pipeline complete!")
                status_text.success("Pipeline complete! The knowledge base has been updated.")
                st.balloons()
        else:
            st.warning("Please upload at least one PDF file.")
    
    if st.session_state.processed_data:
        st.divider()
        st.header("Extracted Information from Last Run")
        
        for item in st.session_state.processed_data:
            with st.expander(f"**{item.get('documentId')}** - Issuer: {item.get('issuer')}"):
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Customer", item.get("customerName", "N/A"))
                col2.metric("Statement Date", item.get("statementDate", "N/A"))
                col3.metric(
                    "Total Usage",
                    f"{item.get('totalUsage', 0)} {item.get('unit', '')}"
                )
                
                if item.get("_qc_flag"):
                    col4.error(f"QC Flag: {item.get('_qc_reason')}")
                else:
                    col4.success("QC Passed")
                
                st.write("**Usage History:**")
                if item.get("usageHistory"):
                    df = pd.DataFrame(item["usageHistory"])
                    st.dataframe(df, use_container_width=True)
                else:
                    st.write("No usage history found.")
                
                with st.popover("View Full Extracted JSON"):
                    st.json(item)
