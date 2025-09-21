# Introduction
This project implements a **local Retrieval-Augmented Generation (RAG) chatbot** using ChromaDB and Ollama. It allows you to query documents intelligently **without relying on any cloud services**.  
The workflow consists of two phases:
  - **`local-rag-indexing.py`** – This script builds the knowledge store from your documents by generating embeddings and storing them in a **persistent ChromaDB**, which acts as the **knowledge store** for semantic search..
  - **`local-rag-chatbot.py`** – This script launches a **Streamlit UI** to chat with the **RAG-powered chatbot** using the indexed documents. If an answer is not found in the knowledge store, the chatbot falls back to a general LLM response.

---

# Prerequisites
- The chatbot UI is a **Python script** that uses **ChromaDB**, **Ollama**, **Streamlit** and **embedding/LLM models** from Hugging Face.
- Ensure you have the following installed locally:
  - `Python 3.8'+` 
  - `boto3`  
  - `streamlit`  
- Download ollama and required models.  
  - Install Ollama from the webiste https://ollama.com/
  - Once Ollama is installed then download the models using following commands:
    ```
    ollama pull hf.co/CompendiumLabs/bge-base-en-v1.5-gguf
    ollama pull hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF
    ```
 
---

# Steps to Deploy this Model
💡 *Note: I've used Amazon Titan Text Embeddings V2 as embedding model & Anthropic Claude 3 Haiku as LLM.* 
- **Step 1:** Create an **S3 bucket** and upload your documents (`.pdf`, `.doc`, `.txt`, etc.) containing proprietary information. This will act as the **knowledge source** for RAG.  
- **Step 2:** In the **AWS Bedrock Console → Knowledge Bases**, create a knowledge base with the S3 bucket as the data source.  
  - Choose an **Embeddings model** (e.g., *Amazon Titan Text Embeddings V2*).  
  - Choose a **Vector store** (e.g., *AWS OpenSearch*).  
  - Once created, ensure the data is synced.  
- **Step 3:** Ensure you have access to a **Large Language Model (LLM)** (e.g., *Anthropic Claude 3 Haiku*).  
  - This will be referenced in the chatbot UI script. You may need to update `ask_bedrock()` function in the script in case you're using model other than Anthropic Claude 3 Haiku.
- **Step 4:** Update the following in `aws-rag-chatbot.py`:  
  - `kb_id` → your Knowledge Base ID  
  - `model_id` → the Model ID of your LLM  
  - `region_name` → the AWS region of your knowledge base  
  - `model_arn` → ARN of your chosen LLM  
- **Step 6:** Run the script using following command:  
  ```bash
  streamlit run aws-rag-chatbot.py
  ```
- **Step 7:** After testing, make sure to clean up following to avoid unnecessary charges in AWS:
  - Delete the Knowledge Base
  - Delete the Vector store
  - Delete the objects in S3 bucket  
