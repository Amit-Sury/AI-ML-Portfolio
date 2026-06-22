# Enterprise-RAG
Enterprise-grade AI Knowledge Platform on AWS showcasing **DataOps, LLMOps, GitOps, Security, and Observability** through automated document ingestion, semantic retrieval, guardrails, LLM evaluation, and Kubernetes-native deployment on Amazon EKS.

### 🔁 Key Features
- **Platform Engineering**
  - FastAPI application
  - EKS deployment
  - API Gateway integration
  - Cognito authentication
  - ArgoCD GitOps deployment
  - Fluent Bit → CloudWatch logging
  - Deployment and teardown automation
- **Security**
  - JWT-based authentication flow
  - Session management
  - Prompt injection detection
  - PII checks
  - PCI checks
  - Input/output guardrails
- **LLM Engineering**
  - RAG pipeline
  - OpenSearch integration
  - Context construction
  - LLM-as-a-Judge evaluation
  - Response validation
  - Bedrock integration
- **Production Readiness**
  - Cache implementation
  - Selective caching strategy
  - Failure recovery in deployment scripts
  - Checkpoint-based resume capability
  - Safe deletion workflow
  - Centralized monitoring and logging

---
# 🧩 Deployment Architecture (AWS)
<img width="1536" height="1024" alt="architecture" src="https://github.com/user-attachments/assets/1d897bd5-e102-4166-8632-1fd103f90b03" />


---
# 🔁 Query Processing Flow

<img width="1895" height="487" alt="retrieval_flow" src="https://github.com/user-attachments/assets/317d5f48-fd33-4d55-9983-4d80d76f3a9d" />

---
# 🔐 Authentication Flow

[e2e-auth-flow](./call-flows/auth.md)

---

# 🐳 Steps to Deploy 
> 💡 *README file of [deployment-package](./deployment-package) summarizes overall deployment process. Its a good reference to get overview of whole deployment process.*

> 💡 *Make sure Docker is running, and AWS credentials are configured using (`aws configure`).*

  - **Step 1:** Download the [scripts](./scripts) and [deployment-package](./deployment-package), folders to your local machine or server in a separate folder.
  - **Step 2:** In a terminal, navigate into the `/scripts` folder and build the Docker image:
  ```
    docker build --no-cache -f ./Dockerfile -t enterpriese-rag .
  ```
  - **Step 3:** Follow the steps mentioned in [README.md](./deployment-package/lambda-package/README.md) to prepare following files. Keep these zip files under lambda-package folder.
    - lambda.zip
    - lambda-layer.zip
    - authorizer-lambda-layer.zip
    - authorizer-lambda.zip.
     
  - **Step 4:** Update "AWS_REGION" present in `VARIABLES BLOCK` in the script `enterprise-rag-deploy.sh` of 'deployment-package' folder.  
  - **Step 5:** Deploy the app by executing `./enterprise-rag-deploy.sh`.
     > 💡 *Script will create a "output" folder in the current directory, do not delete `deletion_checkpoint.log` file. Delete script use this to find all resources which are created successfully.*
  - **Step 6:** After deployment, script will display all the resource created and will show the API gateway URI. Use api gateway URI in your browser to access the app. 
   
  - **Step 7:** To delete all created AWS resources, run `./enterprise-rag-delete.sh`. Make sure to update the `AWS_REGION` in the delete script before executing it. 


> 📝 Note: This project is actively evolving. If you spot any issues or have suggestions, feel free to share feedback! 
