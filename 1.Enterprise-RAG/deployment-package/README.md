# Enterprise RAG Deployment Guide

This document explains the deployment order of the Enterprise RAG application. Also summarizes the whole architecture along the lines.

> 💡 * [enterprise-rag-deploy.sh](./enterprise-rag-deploy.sh) automates this whole deployment process.*

## 1. Create ECR Registry

Create an ECR repository and upload the Retrieval Service container image.

---

## 2. Deploy `cfn-s3-stack`

Creates the S3 bucket used to store Lambda deployment artifacts.

### Resources Created

* S3 bucket for Lambda artifacts

---

## 3. Upload Lambda Artifacts

Upload the required packages to create lambda function:

* Lambda function code
* Lambda Layer package containing required Python dependencies

---

## 4. Deploy `cfn-services-stack`

### Resources Created

#### OpenSearch Serverless Collection

Used as the vector database.

#### Ingestion Lambda Function

* Creates Lambda function and IAM role
* Uses artifacts uploaded in Step 3
* This acts as data ingestion pipeline for storing documents into the OpenSearch vector database

---

## 5. Create EKS Cluster

Create the EKS cluster using `eksctl`.

All application pods will run in this cluster.

---

## 6. Deploy `cfn-infra-stack`

### Resources Created

### Retrieval Service IAM Role

Provides access to:

```text
pods.eks.amazonaws.com
```

Allows EKS pods to temporarily obtain AWS permissions and securely access AWS services.

### External Secrets Operator IAM Role

Provides access to:

```text
pods.eks.amazonaws.com
```

Allows External Secrets Operator (ESO) to access:

* AWS Parameter Store
* AWS Secrets Manager

### VPC Link

Creates a VPC Link for private subnets.

Purpose:

```text
API Gateway → VPC Link → Internal Resources
```

Allows API Gateway to communicate with pod resources inside private VPC subnets.

### API Gateway

Handles external traffic and routes requests through:

```text
API Gateway
    ↓
VPC Link
    ↓
NLB
    ↓
Pods
```

### Cognito Resources

Creates resources required for managed login and authentication.

---

## 7. Create Environment Parameters

Create required environment parameters in:

* AWS Systems Manager Parameter Store

---

## 8. Install Argo CD 

Argo CD becomes responsible for deploying and managing the Retrieval Service.

### Responsibilities

#### Deploy Retrieval Service

Deploys:

```text
deployment.yaml
```

into EKS pods.

#### Retrieve Configuration

* ConfigMaps from AWS Parameter Store
* Secrets from AWS Secrets Manager

#### GitOps Management

* Monitors cluster health
* Detects drift
* Synchronizes manifests automatically

---

## 9. Install External Secrets Operator (ESO)

Install ESO in EKS and configure IAM access. ESO will be responsible to retrieve .env configurations from AWS parameter store and creates configMap in the EKS cluster. Service Pods will use this configMap as .env 

### ESO Installation

ESO installation is done by Helm. The Helm installation creates following resources for ESO:

```text
Namespace:
external-secrets

ServiceAccount:
external-secrets
```

### Create Pod Identity Association for ESO

The ESO pod uses a Kubernetes ServiceAccount mapped to an AWS IAM role. This allows ESO to read:

* AWS Parameter Store
* AWS Secrets Manager

After installation, create a pod identity association between ESO service account and ESO IAM role.    Once mapped, ESO will be able to assume that role and retrieve secrets from Parameter Store or Secrets Manager, creating Kubernetes Secrets or ConfigMaps for the workloads.

```text
ESO ServiceAccount
        ↔
ESO IAM Role
```

Purpose:

* Allows ESO to assume the IAM role
* Retrieve secrets and parameters from AWS

### ESO Output

ESO creates:

* Kubernetes Secrets
* Kubernetes ConfigMaps

for workloads running inside the cluster.

---

## 10. Create Kubernetes Namespace and ServiceAccount

* Create a namespace where all application resources will be deployed.
* Create Kubernetes ServiceAccount

Purpose:

* Gives pods an identity within Kubernetes
* Enables AWS permissions to be attached to workloads

---

## 11. Deploy Kubernetes Service (`LoadBalancer`)

Deploy a Kubernetes Service of type (loadbalancer). This creates an internal NLB which is needed to create API Gateway<->NLB integration, API gateway will forward incoming traffic to this NLB via VPC link. NLB will then forward the traffic towards available pods.

```yaml
type: LoadBalancer
```

### What Happens

* Kubernetes automatically creates an internal AWS Network Load Balancer (NLB)
* NLB annotations instruct EKS to:

  * Create an internal AWS NLB
  * Route traffic directly to Pod IPs

---

## 12. Create Pod Identity Association (for Retrieval Service)

Create a Pod Identity Association between kubernetes service account and Retrival service IAM role. This links Kubernetes ServiceAccount with the AWS IAM role of retrieval service so that pods can access required AWS services securely.   

```text
Kubernetes ServiceAccount
        ↔
AWS Retrieval Service IAM Role
```

Purpose:

* Allows Retrieval Service pods to securely access AWS services

---

## 13. Deploy `cfn-integration-stack`

This is done after creating K8s service because this stack needs NLB DNS which will be used to create integration between API gateway and NLB

### Resources Created

### API Gateway ↔ NLB Integration

Uses:

```text
Link Type = VPC_LINK
```

Purpose (incoming traffic from users will flow as shown below):

```text
Internet
    ↓
API Gateway
    ↓
VPC Link
    ↓
NLB
    ↓
Retrieval Service Pods
```

Allows API Gateway to forward requests to services running in EKS.

### API Gateway Route

Defines which API path(s) are routed to the NLB integration. Creates both public and private endpoints.

### API Gateway Stage

Publishes the API configuration and makes it active for external traffic.

---

# Deployment Order Summary

```text
1. Create ECR Registry
2. Deploy cfn-s3-stack
3. Upload Lambda Artifacts
4. Deploy cfn-services-stack
5. Create EKS Cluster
6. Deploy cfn-infra-stack
7 Create Parameter Store Entries
8. Install Argo CD
9. Install ESO and Create Pod Identity Association
10. Create Kubernetes Namespace
11. Create Kubernetes ServiceAccount
12. Deploy Kubernetes Service (LoadBalancer)
13. Create Retrieval Service Pod Identity Association
14. Deploy cfn-integration-stack
15. Validate End-to-End Traffic Flow
```

- 📁 File Organization

```
├── /K8s-manifests/             # Kubernetes manifest files
├── /lambda-package/            # Ingestion service: Lambda package
├── /stacks/                    # AWS Cloudformation Stacks
├── enterprise-rag-delete.sh    # Cleanup script. Deletes all the AWS resources for enterprise-rag
├── enterprise-rag-deploy.sh    # Installation script. Creates all the required AWS resources for enterprise-rag
```
