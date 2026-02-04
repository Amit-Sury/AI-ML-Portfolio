# 🚀 AI/ML Portfolio
Welcome to my **AI/ML Project Portfolio**. This repository showcases selected projects I’ve worked on, highlighting my skills in **machine learning, deep learning, data science, and cloud deployment**.  

🔗 Feel free to explore the projects below. Each project folder contains code, documentation, and instructions for running the work.

---

## 📂 Projects

### 1. 🤖 [GitRepoAssist-AI](./GitRepoAssist-AI)
  
### *Intelligent GitHub Assistant — powered by Agentic AI*
- **Goal**: GitRepoAssist-AI is an **Multi-tool ReAct Agent** that **integrates directly with GitHub** to help you analyze **pull requests, manage issues, and streamline repository insights** — all through intelligent **agentic automation**.
- **Tech Stack**: LangChain + LangGraph (for agentic flow orchestration), PyGithub (GitHub API integration), Python, Boto3, Streamlit, AWS-Bedrock/OpenAI/Ollama (flexible LLM backends)
- **Highlights**:
  - 🧠 **Understands and summarizes PRs** — Get concise overviews of the latest pull requests.
  - 🗨️ **Fetches file contents & issue details** — Retrieve, read, and analyze files or discussions directly.
  - ⚙️ **Automates GitHub workflows** — Uses **LangGraph, LangChain, and PyGithub** for deep repository insights.
  - 🌐 **Deployable across environments** — Works with **AWS Bedrock, OpenAI, or local LLMs (Ollama).**
  - 🖥️ **Interactive Streamlit UI** — Offers a clean and intuitive user experience.
- **⭐ Key Features (Agentic Tooling Capabilities)**
  - 📁 Repository & File Intelligence
    - 🔍 Overview of all files in the main branch
    - 🗂️ List all files inside any directory
    - 📄 Fetch the content of any file from a directory
    - 🧾 Read file contents directly from a Pull Request
  - 🐛 Issue Management
    - 📝 Fetch all repository issues
    - 💬 Add comments to specific issues
    - 🧑‍💻 Get issue Creater Info   
  - 🧠 Get detailed insights & summaries for any PR
    - 🔀 Pull Request Analysis
    - 🚦 List all open Pull Requests
    - 🗃️ Overview of files included in a PR
    - 🧑‍💻 List all PR authors
    - 🗨️ Fetch all comments inside a PR 
- **Deployment/Code Details**: [Visit GitRepoAssist-AI Page](./GitRepoAssist-AI/)
---

### 2. [AWS-RAG](./AWS-RAG)
- **Goal**: A knowledge assistant chatbot using **Large Language Models (LLMs)** and **Retrieval-Augmented Generation (RAG)** to deliver accurate, context-aware responses.
- **Tech Stack**: AWS (Bedrock, S3, OpenSearch), Python, Boto3, Streamlit 
- **Highlights**:
  - Leveraged **AWS Bedrock** with Titan Embeddings for vector generation and **Anthropic Claude** as the LLM.  
  - Designed a **knowledge base pipeline** leveraging S3 and OpenSearch for scalable document storage and retrieval.
  - **Leveraged RAG for proprietary knowledge** retrieval while using the **LLM for general conversational capability**.
  - Built an **interactive UI with Streamlit** for seamless user interaction.
- **Deployment/Code Details**: [Visit AWS-RAG Page](./AWS-RAG/)

---
### 3. [Fine-Tuning LLM on AWS SageMaker](./Fine-Tune-LLM)
- **Goal**: Fine-tune a base **LLM** model (```meta/llama2-7b-hf```) using **Supervised Fine-Tuning (SFT)** and **PEFT techniques (LoRA)** on **AWS SageMaker** to gain hands-on experience, with a focus on domain specialization.  
- **Tech Stack**:
  - **Model**: meta/llama2-7b-hf (base/text generation), source: [Huggingface](https://huggingface.co/meta-llama/Llama-2-7b-hf)
  - **Training Framework**: HuggingFace TRL (SFTTrainer), PEFT/LoRA, transformers, Pytorch, AWS SageMaker (infrastructure)
  - **Datasets**: ```netop/TeleQnA```: a telecom QA benchmark dataset, source: [Huggingface](https://huggingface.co/datasets/netop/TeleQnA)
- **Highlights**:
  - Leveraged **AWS Sagemaker** for End-to-end fine-tuning workflow.
  - Fine-tuned **LLaMA-2 model** using instruction-style SFT. Used **LoRA (Low-Rank Adaptation)** technique to reduce GPU memory footprint and training cost.
  - Focused on telecom domain lingo and response structure. Dataset's (TeleQnA) original intent is to evaluate telecom knowledge in LLMs, in this project it is used to adapt the model to telecom domain language, terminology, and reasoning style.
  - The dataset was reshaped into an instruction-tuning format:
```
    ###Instruction: System prompt
    ###Input: Telecom-related questions
    ###Output: Answer
```
  - **Deployment/Code Details**: [Visit Fine-Tune-LLM Page](./Fine-Tune-LLM/)
---

### 4. [CNN](./CNN)
- **Goal**: A **Convolutional Neural Network (CNN)** that classifies images of animals.  
- **Tech Stack**: Python, TensorFlow, Keras, Pandas, Matplotlib  
- **Highlights**:
  - Trained on a dataset of 3,900 images (1,300 each of Dog, Elephant, Horse) with additional 450 images for validation set. Dataset sourced from [Kaggle](https://www.kaggle.com/).  
  - Applied preprocessing and data augmentation (rotation, flipping, normalization) to improve model generalization.  
  - Leveraged **AWS SageMaker Script Mode** for custom training, packaging dependencies, and handling deployment.  
  - Deployed the model on **AWS SageMaker** for inference. 
- **Deployment/Code Details**: [Visit CNN page](./CNN/)

---

### 5. [Local-RAG](./Local-RAG)
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

- **Deployment/Code Details**: [Visit Local-RAG Page](./Local-RAG/)
  
---

## 🛠️ Tools & Technologies
- **Programming**: Python (NumPy, Pandas, Matplotlib), PyGithub
- **ML/DL**: TensorFlow, Langgraph + Langchain (for agentic flow orchestration), Keras, TRL, OpenAI, Ollama, Hugging Face, Chroma DB (for vector store)  
- **Cloud & Deployment**: AWS: SageMaker/Bedrock/S3/OpenSearch/Boto3, Streamlit (for app deployment)


