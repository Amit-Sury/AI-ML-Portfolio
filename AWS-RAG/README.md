# Architecture
<img width="986" height="545" alt="image" src="https://github.com/user-attachments/assets/fb3e1b40-ec75-4009-b046-147a852e9774" />

# Architecture Summary
This RAG chatbot architecture consists of two phases:
  - Preprocessing (Offline Phase): Documents from S3 are chunked, converted into embeddings using an embedding model, and stored in a vector database (AWS OpenSearch).
  - Online Phase: A user query is sent from the UI to AWS Bedrock. Relevant knowledge chunks are retrieved from the vector DB and passed to the LLM to generate a context-aware response, which is then returned to the user.

---

# Prerequisites
- The chatbot UI is a **Python script** that uses **Boto3** and **Streamlit**.
- Ensure you have the following installed locally:
  - `Python 3.8'+` 
  - `boto3`  
  - `streamlit`  
- AWS credentials must be configured in your local environment (`aws configure`).  
  - These credentials will be used to connect to **AWS Bedrock**.
 
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
