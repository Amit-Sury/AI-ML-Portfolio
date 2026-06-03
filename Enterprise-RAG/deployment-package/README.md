# Enterprise-RAG deployment package

- 📁 File Organization

```
├── /K8s-manifests/             # Kubernetes manifest files
├── /lambda-package/            # Ingestion service: Lambda package
├── /stacks/                    # AWS Cloudformation Stacks
├── enterprise-rag-delete.sh    # Cleanup script. Deletes all the AWS resources for enterprise-rag
├── enterprise-rag-deploy.sh    # Installation script. Creates all the required AWS resources for enterprise-rag
```
