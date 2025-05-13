import os
from langchain_community.document_loaders import TextLoader, PyPDFLoader, DedocFileLoader
from store import vector_store, text_splitter

def load_and_split(file_path: str):
    if file_path.endswith(".pdf"):
        return text_splitter.split_documents(PyPDFLoader(file_path).load())
    elif file_path.endswith(".txt"):
        return text_splitter.split_documents(TextLoader(file_path).load())
    elif file_path.endswith(".docx"):
        return text_splitter.split_documents(DedocFileLoader(file_path).load())
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

def ingest_file(file_path: str) -> int:
    chunks = load_and_split(file_path)
    for doc in chunks:
        doc.metadata["source_file"] = os.path.basename(file_path)  # keep for traceability
    vector_store.add_documents(chunks)
    return len(chunks)
