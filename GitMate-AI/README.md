# 🤖 GitMate-AI  
### *Intelligent GitHub Assistant — powered by Agentic AI*

GitMate.AI is an AI-powered assistant that integrates directly with GitHub to help you analyze pull requests, manage issues, and streamline repository insights — all through intelligent, agentic automation built with **LangGraph, LangChain, and Streamlit**.

---
## 🔁 Call Flow
<img width="1046" height="410" alt="image" src="https://github.com/user-attachments/assets/d20554e0-25dd-4b38-bf29-05408290dc67" />


---
## 🧩 Architecture (AWS)
<img width="1280" height="720" alt="GitMate-AI Architecture" src="https://github.com/user-attachments/assets/51241c4d-95cd-4684-84c0-890bf31e4e6b" />

- GitMate-AI App runs inside a dedicated VPC spanning two Availability Zones. Each subnet hosts EC2 instances that runs App containers.
- Traffic enters through an internet-facing **Application Load Balancer (ALB)**, which distributes requests across the EC2 fleet using round-robin routing.
- The compute layer is managed by an **Auto Scaling Group (ASG)** backed by a Launch Template, to ensure high availability and elasticity.
- During bootstrapping, each EC2 instance retrieves runtime configuration from **AWS SSM Parameter Store**, and pulls the required Docker image from **AWS ECR** via user data. 
- Whole infrastructure components—including VPC, networking and compute are **provisioned through AWS CloudFormation**.

---
# ⚙️ Prerequisites
- This app is built using Python and uses **Langgraph**, **Langgchain**, **Pygithub**, **Streamlit** and flexible LLM models (**Bedrock**, **OpenAI**, **Ollama**). 
- Refer [requirements.txt](./app/Docker/requirements.txt) for comprehensive list of dependecies. Ensure you have installed all the required dependencies.
  > 💡 *Use pip command to install packages.*
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
- **AWS Deployment**
  > 💡 *Make sure Docker is running, and AWS credentials are configured using (`aws configure`).*
  - **Step 1:** Download the entire project folder [app](./app) to your local machine or server in a separate folder.
  - **Step 2:** In a terminal, navigate into the `/app` folder and build the Docker image:
  ```
    docker build --no-cache -f docker/Dockerfile -t gitmate-ai .
  ```
  - **Step 3** Login to AWS Console and create:
    - An EC2 key pair in your desired region.
    - An EC2 IAM Role / Instance Profile with permissions for:
      - `AmazonSSMManagedInstanceCore`
      - AWS Bedrock
      - ECR
      - SSM Parameter Store
  - **Step 4** Download `gitmateai_aws_deploy.sh`, `gitmateai_deploy.yaml`, `gitmateai_aws_delete.sh` from [Scripts](.app/Scripts) folder to a temporary local folder.
  - **Step 5** Copy your Github APP `private_key.pem` file into the same temporary folder. In case you want to use OpenAI then add your OpenAI API key to a file named `openai.key`, otherwise just create a openai.key file with some dummy text. 
  - **Step 6** Edit `gitmateai_aws_deploy.sh` and update the `VARIABLES BLOCK` as per your preference. `AWS_ACCOUNT_ID, AWS_REGION, KEY_PAIR, EC2_IAM_PROFILE, GITHUB_APP_ID, GITHUB_REPOSITORY, GITHUB_APP_PRIVATEKEY_PATH, OPENAI_API_KEY_PATH, LLM_TYPE, LLM_MODEL_ID` must be updated.  
  - **Step 7:** Deploy the app by executing `./gitmateai_aws_deploy.sh`. 
  - **Step 8** After deployment, log in to the AWS Console → EC2 → Load Balancers, and copy the Load Balancer DNS name. Open it in your browser:
   ```
   http://<load-balancer-url>:8501
   ``` 
  - - **Step 9** To delete all deployed AWS resources, run `./gitmateai_aws_delete.sh`. Make sure to update the `AWS_REGION` in the delete script before running it. 
       
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
---

## 📁 File Organization
- Refer [file_organization.txt](./Scripts/file_organization.txt) for more details.
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
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC_BY--NC_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)


---
