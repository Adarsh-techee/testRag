import streamlit as st
import requests
import os

BASE_URL = "http://127.0.0.1:8001"  

st.title("RAG With llama2")

st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Choose an option", ["Ingest File", "Ingest Multiple Files", "Ask a Question"])

if page == "Ingest File":
    st.header("Upload a File for Ingestion")
    uploaded_file = st.file_uploader("Choose a file (.pdf, .txt, .docx)", type=["pdf", "txt", "docx"])

    if st.button("Upload File"):
        if uploaded_file:
            with open(uploaded_file.name, "wb") as f:
                f.write(uploaded_file.getbuffer())

            file_path = os.path.abspath(uploaded_file.name)

            payload = {"file": file_path}
            response = requests.post(f"{BASE_URL}/ingest-file", json=payload)

            if response.status_code == 200:
                st.success(response.json()["message"])
                st.write(f"Chunks created: {response.json().get('chunks', 0)}")
            else:
                st.error(response.json().get("error", "Something went wrong."))

            os.remove(file_path)
        else:
            st.warning("Please select a file.")



elif page == "Ingest Multiple Files":
    st.header("Upload Multiple Files for Ingestion")
    uploaded_files = st.file_uploader("Choose multiple files (.pdf, .txt, .docx)", type=["pdf", "txt", "docx"], accept_multiple_files=True)

    if st.button("Upload Multiple Files"):
        if uploaded_files:
            files = []
            for uploaded_file in uploaded_files:
                files.append(('files', (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)))

            response = requests.post(f"{BASE_URL}/ingest-multiple-files", files=files)

            if response.status_code == 200:
                st.success(response.json()["message"])
                st.write(f"Total Chunks Created: {response.json().get('total_chunks', 0)}")
                if response.json().get("errors"):
                    st.error("Some errors occurred:")
                    st.write(response.json()["errors"])
            else:
                st.error(response.json().get("error", "Something went wrong."))
        else:
            st.warning("Please select at least one file.")



elif page == "Ask a Question":
    st.header("Ask a Question")
    query = st.text_area("Your Question")

    if st.button("Submit Question"):
        if query:
            payload = {"query": query}
            response = requests.post(f"{BASE_URL}/ask", json=payload)

            if response.status_code == 200:
                st.success("Answer:")
                st.write(response.json()["answer"]["result"])
            else:
                st.error(response.json().get("error", "Something went wrong."))
        else:
            st.warning("Please enter a question.")
