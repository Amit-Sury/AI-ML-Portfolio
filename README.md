# 🚀 AI/ML Portfolio
Welcome to my **AI/ML Project Portfolio**. This repository showcases selected projects I’ve worked on, highlighting my skills in **machine learning, deep learning, data science, and cloud deployment**.  

🔗 Feel free to explore the projects below. Each project folder contains code, documentation, and instructions for running the work.

---

## 📂 Projects

### 1. 🤖 [GitMate-AI](./GitMate-AI)
  
### *Intelligent GitHub Assistant — powered by Agentic AI*
- **Goal**: GitMate-AI is an **AI-powered** assistant that **integrates directly with GitHub** to help you analyze **pull requests, manage issues, and streamline repository insights** — all through intelligent, **agentic automation**.
- **Tech Stack**: LangChain + LangGraph (for agentic flow orchestration), PyGithub (GitHub API integration), Python, Boto3, Streamlit, AWS-Bedrock/Ollama/OpenAI (flexible LLM backends)
- **Highlights**:
  - 🧠 **Understands and summarizes PRs** — Get concise overviews of the latest pull requests.
  - 🗨️ **Fetches file contents & issue details** — Retrieve, read, and analyze files or discussions directly.
  - ⚙️ **Automates GitHub workflows** — Uses LangGraph, LangChain, and PyGithub for deep repository insights.
  - 🌐 **Deployable across environments** — Works with AWS Bedrock, OpenAI, or local LLMs (Ollama).
  - 🖥️ **Interactive Streamlit UI** — Offers a clean and intuitive user experience.
- **Demo/Script**: [Link to GitMate-AI Scripts](./GitMate-AI/app/)
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

### 3. [CNN](./CNN)
- **Goal**: A **Convolutional Neural Network (CNN)** that classifies images of animals.  
- **Tech Stack**: Python, TensorFlow, Keras, Pandas, Matplotlib  
- **Highlights**:
  - Trained on a dataset of 3,900 images (1,300 each of Dog, Elephant, Horse) with additional 450 images for validation set. Dataset sourced from [Kaggle](https://www.kaggle.com/).  
  - Applied preprocessing and data augmentation (rotation, flipping, normalization) to improve model generalization.  
  - Leveraged **AWS SageMaker Script Mode** for custom training, packaging dependencies, and handling deployment.  
  - Deployed the model on **AWS SageMaker** for inference. 
- **Demo/Notebook**: [Link to Jupyter Notebook](./CNN/Notebook/cnn-tensorflow-sagemaker.ipynb)

---

### 4. [Local-RAG](./Local-RAG)
- **Goal**: Build and interact with a **Local Retrieval-Augmented Generation (RAG) chatbot** using ChromaDB and Ollama. The chatbot allows you to query documents intelligently using embeddings.
- **Tech Stack**: Python, Chroma DB, Ollama, Hugging face, Streamlit 
- **Highlights**:
  - **Ollama** is used to build the RAG model locally.  
  - **Chroma DB** as vector store for a persistent knowledge base.
  - **Leveraged RAG for proprietary knowledge** retrieval while using the **LLM for general conversational capabilities**.
  - Built an **interactive UI with Streamlit** for seamless user interaction.
  - Embeddings and LLM models are sourced from [Hugging Face](https://huggingface.co/).
    - **Embedding model link**: https://hf.co/CompendiumLabs/bge-base-en-v1.5-gguf
    - **Language model link**: https://hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF

- **Demo/Script**:
  - [Link to Indexing Script](./Local-RAG/Script/local-rag-indexing.py)
  - [Link to Chatbot UI Script](./Local-RAG/Script/local-rag-chatbot.py)
---

## 🛠️ Tools & Technologies
- **Programming**: Python (NumPy, Pandas, Matplotlib), PyGithub
- **ML/DL**: TensorFlow, Langgraph + Langchain (for agentic flow orchestration), Keras, OpenAI, Ollama, Hugging Face, Chroma DB (for vector store)  
- **Cloud & Deployment**: AWS: SageMaker/Bedrock/S3/OpenSearch/Boto3, Streamlit (for app deployment)


