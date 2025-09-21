# Introduction
This project implements a **local Retrieval-Augmented Generation (RAG) chatbot** using ChromaDB and Ollama. It allows you to query documents intelligently **without relying on any cloud services**.  
The workflow consists of two phases:
  - **`local-rag-indexing.py`** – This script builds the knowledge store from your documents by generating embeddings and storing them in a **persistent ChromaDB**, which acts as the **knowledge store** for semantic search..
  - **`local-rag-chatbot.py`** – This script launches a **Streamlit UI** to chat with the **RAG-powered chatbot** using the indexed documents. If an answer is not found in the knowledge store, the chatbot falls back to a general LLM response.

---

# Prerequisites
- The chatbot UI is a **Python script** that uses **ChromaDB**, **Ollama**, **Streamlit** and **embedding/LLM models** from Hugging Face.
- Ensure you have the following installed locally:
  - `Python 3.8'+` (Make sure you’re using Python 3.8+ and ideally a virtual environment to avoid conflicts)
  - `streamlit`
  - `python-docx`
  - `PyPDF2`
  - `chromadb`
  - `ollama`
    
  💡 *Use pip command to install packages.*
  ```
  pip install streamlit python-docx PyPDF2 chromadb ollama
  ```  
- Download ollama and required models.  
  - Install Ollama from the webiste [Ollama.com](https://ollama.com/)
  - Once Ollama is installed then download the models by executing following commands in a terminal:
    ```
    ollama pull hf.co/CompendiumLabs/bge-base-en-v1.5-gguf
    ollama pull hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF
    ```
 
---

# Steps to Deploy this Model
 
- **Step 1:** Build the **Knowledge Store** by executing **`local-rag-indexing.py`** script.
   ```
  python local-rag-indexing.py
  ``` 
  - **What it Does**
    - Reads the documents from your specified document folder.
    - Creates a persistent **ChromaDB** vector store at your specified location.
    - Generates embeddings using EMBEDDING_MODEL and stores it in persistent ChromaDB vector store. This vector store acts as the knowledge base for the chatbot.
  - **Notes**
    - Run this script only once or whenever you add new documents.
    - Supported document formats: .pdf, .docx files. You may have to extend this script to use other required formats.
 - **Step 2:** Update `path` variable in **`local-rag-chatbot.py`** script to specify the location of your **ChromaDB** vector store which was created in the previous step.
- **Step 3:** Start the Streamlit chatbot UI 
  ```bash
  streamlit run local-rag-chatbot.py
  ```
  - **What it Does**
    - Starts a **Interactive web-based** chat interface.
    - Based on your query it will first search the knowledge store for answers to the queries.
    - If the answer is not found in the knowledge store then it will fall back to general LLM. 

