# Enterprise-RAG
Enterprise-grade AI Knowledge Platform on AWS showcasing **DataOps, LLMOps, GitOps, Security, and Observability** through automated document ingestion, semantic retrieval, guardrails, LLM evaluation, and Kubernetes-native deployment on Amazon EKS.

---
## 🧩 Deployment Architecture (AWS)


---
# 🔁 Query Processing Flow


---
# 🐳 Steps to Deploy 
> 💡 *README file of [deployment-package](./deployment-package) summarizes overall deployment process. Its a good reference to get overview of whole deployment process.*

> 💡 *Make sure Docker is running, and AWS credentials are configured using (`aws configure`).*

  - **Step 1:** Download the [scripts](./scripts) and [deployment-package](./deployment-package), folders to your local machine or server in a separate folder.
  - **Step 2:** In a terminal, navigate into the `/scripts` folder and build the Docker image:
  ```
    docker build --no-cache -f ./Dockerfile -t enterpriese-rag .
  ```
  - **Step 3:** Follow the steps mentioned in [build_command.txt](./deployment-package/lambda-package/build_command.txt) to prepare lambda.zip and lambda-layer.zip (lambda layer). Keep these files in lambda-package folder.
  - **Step 4:** Update "AWS_REGION", "AWS_ACCOUNT_ID" present in `VARIABLES BLOCK` in the script `enterprise-rag-deploy.sh` of 'deployment-package' folder.  
  - **Step 5:** ** Deploy the app by executing `./enterprise-rag-deploy.sh`.
     > 💡 *Script will create a "output" folder in the current directory, do not delete `deletion_checkpoint.log` file. Delete script use this to find which all resources were created.*
  - **Step 6** After deployment, script will display all the resource created and will show the API gateway URI. Use this URI in your browser to access the app. 
   
  - **Step 7** To delete all created AWS resources, run `./enterprise-rag-delete.sh`. Make sure to update the `AWS_REGION` in the delete script before executing it. 
