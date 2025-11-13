# 🤖 GitMate.AI  
### *Intelligent GitHub Assistant — powered by Agentic AI*

GitMate.AI is an AI-powered assistant that integrates directly with GitHub to help you analyze pull requests, manage issues, and streamline repository insights — all through intelligent, agentic automation built with **LangGraph, LangChain, and Streamlit**.

---
## 🧩 Architecture (AWS)
<img width="1280" height="720" alt="GitMate-AI Architecture" src="https://github.com/user-attachments/assets/c3012c6d-e8ae-4935-8f02-a80c5d926b7b" />


 # 📁 File Organization
- Refer [file_organization.txt](./file_organization.txt) for more details.
```
/app
 ├── main.py                # Entry point – launches Streamlit + initializes environment
 ├── .env                   # Environment variables
 ├── /ui/                   # Streamlit UI and helper utilities
 ├── /graph/                # LangGraph orchestration and LLM initialization
 ├── /tools/                # GitHub + YouTube tools, token handler, log manager
 ├── /config/               # App private keys
 ├── /docker/               # Dockerfile, requirements.txt, .dockerignore
 ├── /logs/                 # Runtime logs (dynamically created)
 └── /history/              # Conversation and user session history (dynamically created)

```

---


# ⚙️ Prerequisites
- This app is built using Python and uses **Langgraph**, **Langgchain**, **Pygithub**, **Streamlit** and flexible LLM models (**Bedrock**, **OpenAI**, **Ollama**). 
- Refer [requirements.txt](./app/Docker/requirements.txt) for comprehensive list of dependecies. Ensure you have installed all the required dependencies.
  > 💡 *Use pip command to install packages:*
  ```
  pip install -r docker/requirements.txt
  ```
- Create and register a Github app by following these [instructions](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/registering-a-github-app). Make sure your app have permissions for:
  - Contents (read and write)
  - Discussions (read and write)
  - Issues (read and write)
  - Metadata (read only)
  - Pull requests (read and write)
- Based on your preference you may use one of the following **LLMs**:
  - **AWS Bedrock**:
    - AWS credentials must be configured in your local environment (`aws configure`). These credentials will be used to connect to **AWS Bedrock**.
    - Ensure you have access to a **Large Language Model (LLM)** in AWS bedrock
  - **OpenAI (Gpt)**:
    - Login to **OpenAI API Platform** page and create API keys in [Organization Settings](https://platform.openai.com/settings/organization/api-keys).    
  - **Ollama** LLM model:    
    - Install Ollama from the webiste [Ollama.com](https://ollama.com/)
    - Once Ollama is installed then download the preferred LLM model of your choice. Below is the sample command for downloading hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF:latest LLM model. This is sourced from [Hugging Face](https://huggingface.co/):
      
    ```
    ollama pull hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF:latest    
    ```
 
---

# 🐳 Steps to Deploy this App
- **Local Deployment**
  - **Step 1:** Copy the entire project folder [app](./app) to your local machine or server.
  - **Step 2:** Copy your github app's private key .pem file in `/config` folder.
  - **Step 3:** Update `.env` file. Summary of required variables:
    
   | Category       | Description                                                                 |
   |----------------|-----------------------------------------------------------------------------|
   | GitHub Configs | App ID, Private Key path, Repository name                                   |
   | LLM Config     | Type of LLM backend to use (Ollama, Bedrock, GPT, etc.), Model ID           |
   | API Keys       | OpenAI API key or other LLM keys if applicable                              |
   | Logging        | Paths for conversation history, logs, debug settings                        |
   | Optional Flags | Enable/disable LangChain message logging, debug mode                        |

   > **Note:** Replace placeholders with your actual credentials and paths.
   - **Step 4:** Run the App using following command:
    ```
    streamlit run main.py
    ```

