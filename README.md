# 🚀 AI/ML Portfolio
Welcome to my **AI/ML Project Portfolio**. This repository showcases selected projects I’ve worked on, highlighting my skills in **machine learning, deep learning, data science, and cloud deployment**.  

🔗 Feel free to explore the projects below. Each project folder contains code, documentation, and instructions for running the work.

---

## 📂 Projects

### 1. [CNN](./CNN)
- **Goal**: A **Convolutional Neural Network (CNN)** that classifies images of animals.  
- **Tech Stack**: Python, TensorFlow, Keras, Pandas, Matplotlib  
- **Highlights**:
  - Trained on a dataset of 3,900 images (1,300 each of Dog, Elephant, Horse) with additional 450 images for validation set. Dataset sourced from [Kaggle](https://www.kaggle.com/).  
  - Applied preprocessing and data augmentation (rotation, flipping, normalization) to improve model generalization.  
  - Leveraged **AWS SageMaker Script Mode** for custom training, packaging dependencies, and handling deployment.  
  - Deployed the model on **AWS SageMaker** for inference. 
- **Demo/Notebook**: [Link to Jupyter Notebook](./CNN/Notebook/cnn-tensorflow-sagemaker.ipynb)

---

### 2. [AWS-RAG](./AWS-RAG)
- **Goal**: A knowledge assistant chatbot using **Large Language Models (LLMs)** and **Retrieval-Augmented Generation (RAG)** to deliver accurate, context-aware responses.
- **Tech Stack**: AWS (Bedrock, S3, OpenSearch), Python, Boto3, Streamlit 
- **Highlights**:
  - Leveraged **AWS Bedrock** with Titan Embeddings for vector generation and **Anthropic Claude** as the LLM.  
  - Designed a **knowledge base pipeline** leveraging S3 and OpenSearch for scalable document storage and retrieval.
  - **Leveraged RAG for proprietary knowledge** retrieval while using the **LLM for general conversational capability**.
  - Built an **interactive UI with Streamlit** for seamless user interaction.
- **Demo/Script**: [Link to Chatbot UI Script](./AWS-RAG/Script/aws-rag-chatbot.py)

---

### 3. [Local-RAG](./Local-RAG)
- **Goal**: Build and interact with a **Local Retrieval-Augmented Generation (RAG) chatbot** using ChromaDB and Ollama. The chatbot allows you to query documents intelligently using embeddings.
- **Tech Stack**: Python, Chroma DB, Ollama, Hugging face, Streamlit 
- **Highlights**:
  - **Ollama** is used to build the RAG model locally.  
  - **Chroma DB** as vector store for a persistent knowledge base.
  - **Leveraged RAG for proprietary knowledge** retrieval while using the **LLM for general conversational capabilities**.
  - Built an **interactive UI with Streamlit** for seamless user interaction.
  - **Embedding model link**: https://hf.co/CompendiumLabs/bge-base-en-v1.5-gguf
  - **Language model link**: https://hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF

- **Demo/Script**:
  - [Link to Indexing Script](./Local-RAG/Script/local-rag-indexing.py)
  - [Link to Chatbot UI Script](./Local-RAG/Script/local-rag-chatbot.py)
---

## 🛠️ Tools & Technologies
- **Programming**: Python (NumPy, Pandas, Matplotlib)  
- **ML/DL**: TensorFlow, Keras, Ollama, Hugging Face, Chroma DB (for vector store)  
- **Cloud & Deployment**: AWS: SageMaker/Bedrock/S3/OpenSearch/Boto3, Streamlit (for app deployment)  
