from fastapi import FastAPI, HTTPException, Body, UploadFile, File
from fastapi.responses import JSONResponse
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_elasticsearch import ElasticsearchStore
from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from pydantic import BaseModel
from typing import List
from ingest_file import ingest_file
from store import vector_store
import os

from langchain.schema import Document

app = FastAPI()

embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
llm = ChatOllama(model="llama2", temperature=0.8)

template = """
Use the following context to answer the question. If the answer is not contained within the context, just say "I don't know."
Context:
{context}
Question:
{question}
"""
prompt = PromptTemplate(input_variables=["context", "question"], template=template)

def ask_question(query: str) -> str:
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})
    rag_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, chain_type="stuff", chain_type_kwargs={"prompt": prompt})
    return rag_chain.invoke(query)

class Query(BaseModel):
    query: str

@app.post("/ask")
def ask_api(request: Query = Body(...)):
    try:
        answer = ask_question(request.query)
        return {"query": request.query, "answer": answer}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

class IngestFileRequest(BaseModel):
    file: str

@app.post("/ingest-file")
async def ingest_file_api(request: IngestFileRequest = Body(...)):
    file_path = request.file
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found.")
    if not file_path.endswith((".pdf", ".txt", ".docx")):
        return JSONResponse(status_code=400, content={"error": "Unsupported file type."})
    try:
        chunk_count = ingest_file(file_path)
        return {"message": "Ingestion complete.", "chunks": chunk_count}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/ingest-multiple-files")
async def ingest_multiple_files_api(
    files: List[UploadFile] = File(...)
):
    total_chunks = 0
    errors = []

    try:
        for uploaded_file in files:
            filename = uploaded_file.filename
            if not filename.endswith((".pdf", ".txt", ".docx")):
                errors.append(f"Unsupported file type: {filename}")
                continue

            temp_file_path = f"temp_{filename}"
            with open(temp_file_path, "wb") as f:
                f.write(await uploaded_file.read())

            try:
                chunk_count = ingest_file(temp_file_path)
                total_chunks += chunk_count
            except Exception as e:
                errors.append(f"Failed to ingest {filename}: {str(e)}")
            finally:
                os.remove(temp_file_path)

        return {
            "message": "Ingestion completed with some possible errors.",
            "total_chunks": total_chunks,
            "errors": errors
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
