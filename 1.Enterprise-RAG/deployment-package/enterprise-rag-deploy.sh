#! /bin/bash

############## Variables Block  ###################

#aws parameters
AWS_REGION="region_name" #Default region
AWS_ACCOUNT_ID="************" #AWS Account ID

#env parameters
API_ROOT_PATH="/production"
LLM_MODEL_ID="qwen.qwen3-32b-v1:0"
EMBEDDING_MODEL_ID="amazon.titan-embed-text-v2:0"
INDEX_NAME="enterprise-rag-index"
VECTOR_TOP_K="10"
RE_RANKED_TOP_K="5"
ENABLE_GUARDRAILS="1"
LLM_AS_JUDGE_MODEL_ID="qwen.qwen3-32b-v1:0"
FAITHFULNESS_THRESHOLD="0.9"

#Following resources are created by stack
#VECTOR_DB_HOSTNAME : Will be assigned dynamically after Opensearch collection creation
#COGNITO_DOMAIN_URI: Will be assigned dynamically after Cognito User pool creation
#CLIENT_ID: Will be assigned dynamically after Cognito User pool creation
#CLIENT_SECRET: Will be assigned dynamically after Cognito User pool creation
#REDIRECT_URI: Will be assigned dynamically after api gateway creation

############## END  ###################

## Output file handling
OUTPUT_DIR="output"
RESOURCE_FILE="$OUTPUT_DIR/resource_tracker.txt"

mkdir -p "$OUTPUT_DIR"

# clear old output file
> "$RESOURCE_FILE"
echo "ℹ️ Following resources are created in region: $AWS_REGION " >> "$RESOURCE_FILE"
echo "========================================" >> "$RESOURCE_FILE"

## delete tracker
OUTPUT_DIR="output"
CHECKPOINT_LOGGER="$OUTPUT_DIR/deletion_checkpoint.log"

# clear old checkpiont file
> "$CHECKPOINT_LOGGER"

############## low-level functions  ###################
next_step(){

    if [ "$INTERACTIVE" = true ]; then
        echo "continue? (y/n): "
        read PROCEED
        if [[ "$PROCEED" != "y" && "$PROCEED" != "Y" ]]; then
            echo "Deployment aborted."
            exit 0
        fi
    fi

}

## create cloudformation stack ##
create_stack() {
    
    local stack_name=$1

    if [ "$stack_name" = "cfn-infra-stack" ]; then
        aws cloudformation deploy --stack-name "$stack_name" \
        --region "$AWS_REGION" --template-file "./stacks/${stack_name}.yaml" \
        --capabilities CAPABILITY_NAMED_IAM \
        --parameter-overrides VPCId=$2 PrivateSubnetIds=$3
    elif [ "$stack_name" = "cfn-integration-stack" ]; then
        aws cloudformation deploy --stack-name "$stack_name" \
        --region "$AWS_REGION" --template-file "./stacks/${stack_name}.yaml" \
        --parameter-overrides APIGatewayHttpApi=$2 VpcLink=$3 K8sNLBDnsName=$4
    else
        aws cloudformation deploy --stack-name "$stack_name" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$AWS_REGION" --template-file "./stacks/${stack_name}.yaml" 
    fi

    if [ $? -ne 0 ]; then
        echo "❌ Error: Creating $stack_name failed."
        exit 1
    else
        echo "✅ Stack $stack_name created successfully."
    fi 

}
## end ##

## get variable from stack ##
get_value() {
    
    local stack_name=$1
    local variable_name=$2

    VALUE=$(aws cloudformation describe-stacks \
        --stack-name $stack_name \
        --region "$AWS_REGION" \
        --query "Stacks[0].Outputs[?ExportName=='$variable_name'].OutputValue" \
        --output text 2>/dev/null)

    if [ $? -ne 0 ]; then
        echo "❌ Error: Stack $stack_name not found." >&2
        exit 1
    else
        echo "$VALUE"
    fi
}
## end ##

## uploads object into bucket ##
upload_file() {

    local file_name=$1
    
    ## get lambda artifact bucket
    local LAMBDA_BUCKET=$(get_value cfn-s3-stack cfn-s3-stack-LambdaArtifactBucketName) 
    
    aws s3api put-object --bucket "$LAMBDA_BUCKET" --key "$file_name" \
    --region "$AWS_REGION" --body "./lambda-packages/${file_name}" --content-type application/zip 2>/dev/null

    if [ $? -ne 0 ]; then
        echo "❌ Error: Uploading $file_name to $LAMBDA_BUCKET bucket failed." >&2
        exit 1
    fi

    echo "✅ $file_name successfully uploaded to $LAMBDA_BUCKET bucket."
    echo "✅ $file_name uploaded to $LAMBDA_BUCKET bucket." >> "$RESOURCE_FILE"

}
## end ##

## get network loadbalancer DNS name which is created by k8s service
get_nlb_dns() {
    
    local namespace=$1
    local service_name=$2

    echo "Fetching NLB DNS name..."

    nlb_dns=$(kubectl get svc "$service_name" \
        -n "$namespace" \
        -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

    if [ -z "$nlb_dns" ]; then
        echo "❌ Error: Unable to fetch NLB DNS name."
        return 1
    fi

    echo "Obtained value of nlb_dns is: $nlb_dns" >&2
    echo "$nlb_dns"
    
}

################### low-level functions end ###################

################### high-level functions ###################
## Create parameters in parameter store 
put_parameters(){

    echo "Creating .env parameters in AWS Systems Manager Parameter Store..."
    aws ssm put-parameter --region $AWS_REGION  --name " /enterprise-rag/API_ROOT_PATH" --value $API_ROOT_PATH \
    --type "String" --description "API Gateway stage root path" > /dev/null 2>&1

    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to create parameter in Parameter Store." \
            "Please ensure AWS credentials have necessary permissions."
        exit 1
    else
        echo " /enterprise-rag/API_ROOT_PATH created."        
        echo "Parameter Store objects:" >> "$RESOURCE_FILE"
        echo "      ✅/enterprise-rag/API_ROOT_PATH" >> "$RESOURCE_FILE"
    fi

    aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/EMBEDDING_MODEL_ID" \
        --value "$EMBEDDING_MODEL_ID" --type "String" --description "embedding model id" > /dev/null 2>&1
    echo " /enterprise-rag/EMBEDDING_MODEL_ID created."
    echo "      ✅/enterprise-rag/EMBEDDING_MODEL_ID" >> "$RESOURCE_FILE"

    aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/INDEX_NAME" \
        --description "Opensearch collection index name" --value $INDEX_NAME \
        --type "String" > /dev/null 2>&1
    echo " /enterprise-rag/INDEX_NAME created."
    echo "      ✅/enterprise-rag/INDEX_NAME" >> "$RESOURCE_FILE"

    aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/VECTOR_TOP_K" \
        --description "Top_k matches to be retrieved from vector db" \
        --value "$VECTOR_TOP_K" --type "String" > /dev/null 2>&1
    echo " /enterprise-rag/VECTOR_TOP_K created."
    echo "      ✅/enterprise-rag/VECTOR_TOP_K" >> "$RESOURCE_FILE"

    aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/RE_RANKED_TOP_K" \
        --value $RE_RANKED_TOP_K --type "String" \
        --description "Top-k after re-ranking" > /dev/null 2>&1
    echo " /enterprise-rag/RE_RANKED_TOP_K created."
    echo "      ✅/enterprise-rag/RE_RANKED_TOP_K" >> "$RESOURCE_FILE"

    aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/LLM_MODEL_ID" \
        --value $LLM_MODEL_ID --type "String" \
        --description "LLM Model ID in bedrock" > /dev/null 2>&1
    echo " /enterprise-rag/LLM_MODEL_ID created."
    echo "      ✅/enterprise-rag/LLM_MODEL_ID" >> "$RESOURCE_FILE"

    VECTOR_DB_HOSTNAME=$(get_value "cfn-services-stack" "cfn-services-stack-OpenSearchCollection")

    aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/VECTOR_DB_HOSTNAME" \
        --value $VECTOR_DB_HOSTNAME --type "String" \
        --description "Opensearch serverless collection name" > /dev/null 2>&1
    echo " /enterprise-rag/VECTOR_DB_HOSTNAME created."
    echo "      ✅/enterprise-rag/VECTOR_DB_HOSTNAME" >> "$RESOURCE_FILE"

    aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/ENABLE_GUARDRAILS" \
        --value $ENABLE_GUARDRAILS --type "String" \
        --description "Enable input, output guardrails. 0:disable, 1:enable" > /dev/null 2>&1
    echo " /enterprise-rag/ENABLE_GUARDRAILS created."
    echo "      ✅/enterprise-rag/ENABLE_GUARDRAILS" >> "$RESOURCE_FILE"

    aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/LLM_AS_JUDGE_MODEL_ID" \
        --value $LLM_AS_JUDGE_MODEL_ID --type "String" \
        --description "Model Id for LLM-as-Judge. Use for guardrails" > /dev/null 2>&1
    echo " /enterprise-rag/LLM_AS_JUDGE_MODEL_ID created."
    echo "      ✅/enterprise-rag/LLM_AS_JUDGE_MODEL_ID" >> "$RESOURCE_FILE"

    aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/FAITHFULNESS_THRESHOLD" \
        --value $FAITHFULNESS_THRESHOLD --type "String" \
        --description "Faithfulness threshold, use to determine hallucination" > /dev/null 2>&1
    echo " /enterprise-rag/FAITHFULNESS_THRESHOLD created."
    echo "      ✅/enterprise-rag/FAITHFULNESS_THRESHOLD" >> "$RESOURCE_FILE"

    COGNITO_DOMAIN_URI="https://enterprise-rag.auth.${AWS_REGION}.amazoncognito.com"

    aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/COGNITO_DOMAIN_URI" \
        --value $COGNITO_DOMAIN_URI --type "String" \
        --description "Cognito Domain URI" > /dev/null 2>&1
    echo " /enterprise-rag/COGNITO_DOMAIN_URI created."
    echo "      ✅/enterprise-rag/COGNITO_DOMAIN_URI" >> "$RESOURCE_FILE"

    CLIENT_ID=$(get_value "cfn-infra-stack" "cfn-infra-stack-CognitoUserpoolClientID")

    aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/CLIENT_ID" \
        --value $CLIENT_ID --type "String" \
        --description "Cognito App client id" > /dev/null 2>&1
    echo " /enterprise-rag/CLIENT_ID created."
    echo "      ✅/enterprise-rag/CLIENT_ID" >> "$RESOURCE_FILE"

    CLIENT_SECRET=$(aws cognito-idp describe-user-pool-client \
        --user-pool-id "enterprise-rag-userpool" \
        --client-id "$CLIENT_ID" \
        --query "UserPoolClient.ClientSecret" \
        --output text)
    
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to get cognito client secret."
        exit 1
    else
        echo "✅ Cognito client secret obtained successfully."        
    fi

    aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/CLIENT_SECRET" \
        --value $CLIENT_SECRET --type "SecureString" \
        --description "Cognito App client secret" > /dev/null 2>&1
    echo " /enterprise-rag/CLIENT_SECRET created."
    echo "      ✅/enterprise-rag/CLIENT_SECRET" >> "$RESOURCE_FILE"

    REDIRECT_URI=$(get_value "cfn-infra-stack" "cfn-infra-stack-APIGatewayUrl")

    aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/REDIRECT_URI" \
        --value $REDIRECT_URI --type "String" \
        --description "Redirect URI for the app, this will be api gateway uri" > /dev/null 2>&1
    echo " /enterprise-rag/REDIRECT_URI created."
    echo "      ✅/enterprise-rag/REDIRECT_URI" >> "$RESOURCE_FILE"

    echo "----------------------------------" >> "$RESOURCE_FILE"
    echo >> "$RESOURCE_FILE"
    echo "DEL_PARAMETERS=true" >> "$CHECKPOINT_LOGGER"
    next_step
}
## end ##

## upload container in ecr ##
upload_container(){

    echo "Checking if repo enterprise-rag already exists in AWS ECR..."

    if aws ecr describe-repositories --repository-names enterprise-rag \
        --region "$AWS_REGION" >/dev/null 2>&1; then
    
        echo "ℹ️ Repo already exists. Proceeding with next steps..."
    else
        echo "⚙️ Repo doesn't exists. Creating repo..."
        aws ecr create-repository --repository-name enterprise-rag --region $AWS_REGION 
    fi

    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to create repo in AWS ECR."
        exit 1
    else
        echo "✅ Repo enterprise-rag created successfully."
        echo "DEL_ECR_REPO=true" >> "$CHECKPOINT_LOGGER"
        echo "AWS ECR:" >> "$RESOURCE_FILE"
        echo "      ✅AWS ECR Repo: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com" >> "$RESOURCE_FILE"
    fi  

    
    ## Tag and push docker image ##
    echo "Tagging and pushing docker image to ECR repository..."
    ECR_REPO_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

    docker tag enterprise-rag:latest ${ECR_REPO_URI}/enterprise-rag:latest
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to tag docker image. Make sure the image 'enterprise-rag' exists" \
        "locally and docker engine is running."
        exit 1
    else
        echo "✅ Tagging docker image is successful."
    fi  

    echo "Docker image tagged: ${ECR_REPO_URI}/enterprise-rag:latest"
    echo "Logging in to AWS ECR..."
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin ${ECR_REPO_URI}

    if [ $? -ne 0 ]; then
        echo "❌ Error: Docker login to ECR failed. Please check your AWS credentials and docker setup."
        exit 1
    else
        echo "✅ Docker login to ECR successful."
    fi

    echo "Pushing docker image to ECR repository..."
    docker push ${ECR_REPO_URI}/enterprise-rag:latest

    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to push Docker image to ECR."
        exit 1
    else
        echo "✅ Docker image pushed to ECR successfully."
        echo "      ✅Docker image uploaded: ${ECR_REPO_URI}/enterprise-rag:latest" >> "$RESOURCE_FILE"
    fi
    
    echo "----------------------------------" >> "$RESOURCE_FILE"
    echo >> "$RESOURCE_FILE"
    next_step

}
## end ##

## create cfn_s3_stack ##
create_cfn_s3_stack(){

    echo "Creating cfn-s3-stack..."
    create_stack "cfn-s3-stack"
    echo "cfn-s3-stack:" >> "$RESOURCE_FILE"
    echo "      ✅Bucket: enterprise-rag-lambda-artifacts" >> "$RESOURCE_FILE"
    echo "----------------------------------" >> "$RESOURCE_FILE"
    echo >> "$RESOURCE_FILE"
    echo "DEL_S3_STACK=true" >> "$CHECKPOINT_LOGGER"
    next_step
}
## end ##

## uploads lambda artifacts to bucket ##
upload_lambda_artifacts(){
    
    ## upload lambda.zip into bucket  
    echo "Uploading lambda.zip..."
    upload_file lambda.zip
    next_step

    ## upload lambda-layer.zip into bucket  
    echo "Uploading lambda-layer.zip..."
    upload_file lambda-layer.zip
    echo "----------------------------------" >> "$RESOURCE_FILE"
    echo >> "$RESOURCE_FILE"
    echo "DEL_UPLOADED_FILES=true" >> "$CHECKPOINT_LOGGER"
    next_step
}
## end ## 

## creates cfn-services-stack ##
create_cfn_services_stack(){

    echo "creating cfn-services-stack..."
    create_stack "cfn-services-stack"
    echo "cfn-services-stack:" >> "$RESOURCE_FILE"
    echo "      ✅Bucket: enterprise-rag-knowledge-docs" >> "$RESOURCE_FILE"
    echo "      ✅OpenSearch Serverless Encryption Policy: enterprise-rag-encryption-policy" >> "$RESOURCE_FILE"
    echo "      ✅OpenSearch Serverless Network Policy: enterprise-rag-network-policy" >> "$RESOURCE_FILE"
    echo "      ✅OpenSearch Serverless Data Access Policy: enterprise-rag-access-policy" >> "$RESOURCE_FILE"
    echo "      ✅OpenSearch Serverless Collection: enterprise-rag-collection" >> "$RESOURCE_FILE"
    echo "      ✅IAM Role: enterprise-rag-lambda-execution-role" >> "$RESOURCE_FILE"
    echo "      ✅Lambda Function: enterprise-rag-ingestion-lambda" >> "$RESOURCE_FILE"
    echo "      ✅Lambda Function Layer: enterprise-rag-lambda-layer" >> "$RESOURCE_FILE"
    echo "----------------------------------" >> "$RESOURCE_FILE"
    echo >> "$RESOURCE_FILE"
    echo "DEL_SERVICES_STACK=true" >> "$CHECKPOINT_LOGGER"
    next_step
}
## end ##

## creates eks cluster ##
create_eks_cluster(){

    echo "creating eks cluster (using eksctl)..."

    eksctl create cluster --name "enterprise-rag" --nodegroup-name "eks-ng" \
    --region "$AWS_REGION" --node-type t3.medium --nodes 2
    if [ $? -ne 0 ]; then
        echo "❌ Error: Creating EKS cluster enterprise-rag failed."
        exit 1
    else
        echo "✅ EKS cluster enterprise-rag created successfully."
        echo "✅EKS cluster: enterprise-rag" >> "$RESOURCE_FILE"
    fi 

    aws eks create-addon --cluster-name enterprise-rag \
    --region "$AWS_REGION" --addon-name eks-pod-identity-agent

    if [ $? -ne 0 ]; then
        echo "❌ Error: Creating addon eks-pod-identity-agent in enterprise-rag cluster failed."
        exit 1
    else
        echo "✅ addon eks-pod-identity-agent in enterprise-rag cluster is created successfully."        
    fi 

    echo "----------------------------------" >> "$RESOURCE_FILE"
    echo >> "$RESOURCE_FILE"
    echo "DEL_EKS_CLUSTER=true" >> "$CHECKPOINT_LOGGER"
    next_step
}
## end ##

## creates cfn-infra-stack ##
create_cfn_infra_stack(){

    ## get vpcid from eksctl stack 
    VPC_ID=$(get_value "eksctl-enterprise-rag-cluster" "eksctl-enterprise-rag-cluster::VPC")

    ## get subnetids from eksctl stack 
    SUBNETS=$(get_value "eksctl-enterprise-rag-cluster" "eksctl-enterprise-rag-cluster::SubnetsPrivate")

    echo "creating cfn-infra-stack..."
    create_stack "cfn-infra-stack" $VPC_ID $SUBNETS
    echo "cfn-infra-stack:">> "$RESOURCE_FILE"
    echo "      ✅IAM Role: enterprise-rag-retrieval-service-role" >> "$RESOURCE_FILE"
    echo "      ✅IAM Role: enterprise-rag-eso-role" >> "$RESOURCE_FILE"
    echo "      ✅VPC Link: enterprise-rag-eks-vpc-link" >> "$RESOURCE_FILE"
    echo "      ✅VPC Link Security group: VpcLinkSecurityGroup" >> "$RESOURCE_FILE"
    echo "      ✅API Gateway: enterprise-rag-http-apigateway" >> "$RESOURCE_FILE"
    echo "      ✅API Gateway JwtAuthorizer: enterprise-rag-CognitoCookieAuthorizer" >> "$RESOURCE_FILE"
    echo "      ✅Cognito Userpool: enterprise-rag-userpool" >> "$RESOURCE_FILE"
    echo "      ✅Cognito UserPoolDomain: enterprise-rag" >> "$RESOURCE_FILE"
    echo "      ✅Cognito UserPoolClient: enterprise-rag-login-client" >> "$RESOURCE_FILE"
    echo "----------------------------------" >> "$RESOURCE_FILE"
    echo >> "$RESOURCE_FILE"
    echo "DEL_INFRA_STACK=true" >> "$CHECKPOINT_LOGGER"
    next_step
}
## end ##

## creates cfn-integration-stack ##
create_cfn_integration_stack(){

    ## get nlb DNS name, ARN 
    K8SNLBDNSNAME=$(get_nlb_dns "enterprise-rag" "enterprise-rag-service")

    if [ $? -eq 0 ]; then
        APIGATEWAYHTTPAPI=$(get_value "cfn-infra-stack" "cfn-infra-stack-APIGatewayId")
        VPCLINK=$(get_value "cfn-infra-stack" "cfn-infra-stack-VpcLinkId")
        echo "create cfn-integration-stack..." 
        create_stack "cfn-integration-stack" $APIGATEWAYHTTPAPI $VPCLINK $K8SNLBDNSNAME
    fi
    echo "cfn-integration-stack:">> "$RESOURCE_FILE"
    echo "      ✅NLB-APIgw-Integration: enterprise-rag-NLB-APIGw-integration">> "$RESOURCE_FILE"
    echo "      ✅API Gateway Private Routes: RouteKeys: default">> "$RESOURCE_FILE"
    echo "      ✅API Gateway Public Route: RouteKeys: /logged-out,/refresh,root (/)">> "$RESOURCE_FILE"
    echo "      ✅API Gateway Stage: production">> "$RESOURCE_FILE"
    echo "----------------------------------" >> "$RESOURCE_FILE"
    echo >> "$RESOURCE_FILE"
    echo "DEL_INTEGRATION_STACK=true" >> "$CHECKPOINT_LOGGER"
    next_step
}
## end ##

## creates k8s resources ##
create_k8s_resources(){

    ## create eso resources
    echo "creating ESO manifests (ClusterSecretStore, ExternalSecret)..."
    kubectl apply -f ./k8s-manifests/eso-manifests/eso-ClusterSecretStores.yaml    

    if [ $? -ne 0 ]; then
        echo "❌ Error: ESO manifests (ClusterSecretStore) creation failed."
        exit 1
    else
        echo "✅ ESO manifests (ClusterSecretStore) successfully created."        
    fi

    kubectl apply -f ./k8s-manifests/eso-manifests/eso-ExternalSecret.yaml    

    if [ $? -ne 0 ]; then
        echo "❌ Error: ESO manifests (ExternalSecret) creation failed."
        exit 1
    else
        echo "✅ ESO manifests (ExternalSecret) successfully created."        
    fi

    ## create k8s resources
    echo "creating k8s manifests (service, deployment)..."
    kubectl apply -f ./k8s-manifests/service.yaml

    if [ $? -ne 0 ]; then
        echo "❌ Error: Creating k8s manifests (service) failed."
        exit 1
    else
        echo "✅ k8s manifests (service) successfully created."        
    fi

    kubectl apply -f ./k8s-manifests/deployment.yaml

    if [ $? -ne 0 ]; then
        echo "❌ Error: Creating k8s manifests (deployment) failed."
        exit 1
    else
        echo "✅ k8s manifests (deployment) successfully created."        
    fi
    
    echo "DEL_MANIFESTS=true" >> "$CHECKPOINT_LOGGER"
    next_step

    ROLE_ARN=$(get_value "cfn-infra-stack" "cfn-infra-stack-RetrievalServiceRoleArn")

    echo "create-pod-identity-association for RetrievalServiceRole..."

    aws eks create-pod-identity-association \
        --region $AWS_REGION \
        --cluster-name "enterprise-rag" \
        --namespace "enterprise-rag" \
        --service-account "enterprise-rag-service-account" \
        --role-arn "$ROLE_ARN"
    
    if [ $? -ne 0 ]; then
        echo "❌ Error: create-pod-identity-association for RetrievalServiceRole failed."
        exit 1
    else
        echo "✅ create-pod-identity-association for RetrievalServiceRole successfully completed."        
    fi

    echo "DEL_RETRIEVAL_ROLE_ASSOCIATION=true" >> "$CHECKPOINT_LOGGER"

    echo "EKS Cluser(enterprise-rag) resources:" >> "$RESOURCE_FILE"
    echo "      ✅ArgoCD" >> "$RESOURCE_FILE"
    echo "      ✅ESO" >> "$RESOURCE_FILE"
    echo "      ✅ESO manifests (ClusterSecretStore, ExternalSecret)">> "$RESOURCE_FILE"        
    echo "      ✅Namespace: enterprise-rag, argocd" >> "$RESOURCE_FILE"
    echo "      ✅Service Accounts: enterprise-rag-service-account, external-secrets" >> "$RESOURCE_FILE"
    echo "      ✅Service: enterprise-rag-service" >> "$RESOURCE_FILE"
    echo "      ✅Pod-Identity-Association: ESOServiceRole<->external-secrets account" >> "$RESOURCE_FILE"
    echo "      ✅Pod-Identity-Association: RetrievalServiceRole<->enterprise-rag-service-account" >> "$RESOURCE_FILE"   
    echo "      ✅Deployment: enterprise-rag-deployment" >> "$RESOURCE_FILE"
    next_step
}
## end ##

## installs argocd and eso ##
install_argocd_eso(){

    CONTEXT_NAME=$(kubectl config get-contexts -o name | grep enterprise-rag)
    echo "kubectl context name is $CONTEXT_NAME"
    kubectl config use-context "$CONTEXT_NAME"
    next_step
    
    echo "creating namespace and service account"
    kubectl apply -f ./k8s-manifests/serviceacc-namespace.yaml
    
    if [ $? -ne 0 ]; then
        echo "❌ Error: Creating Service Account and Namespace failed."
        exit 1
    else
        echo "✅ Service Account and Namespace created successfully."        
    fi 

    echo "Installing ArgoCD..."
    kubectl create namespace argocd

    kubectl apply --server-side -n argocd \
        -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

    if [ $? -ne 0 ]; then
        echo "❌ Error: Installation of ArgoCD failed."
        exit 1
    else
        echo "✅ ArgoCD installed successfully."    
    fi 

    next_step

    echo "Installing External Secrets Operator (ESO)..."
    
    helm repo add external-secrets https://charts.external-secrets.io 
    helm repo update

    helm install external-secrets \
        external-secrets/external-secrets \
        -n external-secrets \
        --create-namespace \
        --set installCRDs=true

    if [ $? -ne 0 ]; then
        echo "❌ Error: Installation of ESO failed."
        exit 1
    else
        echo "✅ ESO installed successfully."    
    fi 
    #ESO_PODS=$(kubectl get pods -n external-secrets)
    #ESO_CRD=$(kubectl get crd | grep external-secrets)
    #echo "ESO_PODS are:"
    #echo "$ESO_PODS"
    #echo "ESO_CRD are:"
    #echo "$ESO_CRD"
    
    next_step

    ESOROLE_ARN=$(get_value "cfn-infra-stack" "cfn-infra-stack-ESOServiceRoleArn")
    echo "create-pod-identity-association for ESOServiceRole..."
    
    aws eks create-pod-identity-association \
        --region $AWS_REGION \
        --cluster-name "enterprise-rag" \
        --namespace external-secrets \
        --service-account external-secrets \
        --role-arn "$ESOROLE_ARN"
    
    if [ $? -ne 0 ]; then
        echo "❌ Error: create-pod-identity-association for ESOServiceRole failed."
        exit 1
    else
        echo "✅ create-pod-identity-association for ESOServiceRole completed."        
    fi 

    echo "DEL_ESO_ROLE_ASSOCIATION=true" >> "$CHECKPOINT_LOGGER"
    next_step    
}
## end ##
##### high-level functions ends #####
############# functions end ###################

################### deployment process ########################
INTERACTIVE=false
echo "*️⃣ *️⃣  Welcome to Enterprise-Rag deployment utility... *️⃣ *️⃣"
echo "ℹ️  Script will use enterprise-rag docker image and AWS Credentials to deploy the application on AWS..."
echo "ℹ️  Make sure you have build the image and AWS credentials are configured before proceeding..."
echo "Choose option to proceed:"
echo "      1. Interactive mode: script will ask to proceed after each step."
echo "      2. Non-interactive mode: all resources will be created without interruption."
echo "      3. Exit."
while true; do
    echo "Enter 1, 2 or 3..."
    read INPUT
    if [ "$INPUT" = "1" ]; then
        INTERACTIVE=true
        break
    elif [ "$INPUT" = "2" ]; then
        break
    elif [ "$INPUT" = "3" ]; then
        echo "Deployment aborted."
        exit 0
    else
        continue        
    fi  
done

echo "▶️ Deploying enterprise-rag...🚌"

## upload container in ecr
upload_container

## Create cfn-s3-stack 
create_cfn_s3_stack

## upload lambda artifacts into bucket  
upload_lambda_artifacts

## create cfn-services-stack
create_cfn_services_stack

## create eks cluster 
create_eks_cluster 

## create cfn-infra-stack
create_cfn_infra_stack

## create .env parameters in parameter store
put_parameters

## install argocd, eso
install_argocd_eso

## create k8s resources
create_k8s_resources

## create cfn-integration-stack
create_cfn_integration_stack

echo "========================================" >> "$RESOURCE_FILE"
echo "ℹ️ Deployment process completed.🟢 "
cat $RESOURCE_FILE
echo "✅💯🆗enterprise-rag is successfully deployed.✅💯🆗"
