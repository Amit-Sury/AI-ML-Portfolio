#! /bin/bash

############## Variables Block  ###################

#aws parameters
AWS_REGION="ap-south-1" #Default region
EKS_K8S_VERSION="1.36"

#default service port
SERVICE_PORT="8000" #if default value is changed then remember to change in service.yaml too

#env parameters
API_ROOT_PATH="/production" #should be same as API Gateway stage name without trailing /
LLM_MODEL_ID="qwen.qwen3-32b-v1:0"
EMBEDDING_MODEL_ID="amazon.titan-embed-text-v2:0"
INDEX_NAME="enterprise-rag-index"
VECTOR_TOP_K="10"
RE_RANKED_TOP_K="5"
ENABLE_GUARDRAILS="3"
LLM_AS_JUDGE_MODEL_ID="qwen.qwen3-32b-v1:0"
FAITHFULNESS_THRESHOLD="0.9"
CACHE_TYPE=1

#Following resources are created by stack
#VECTOR_DB_HOSTNAME : Will be assigned dynamically after Opensearch collection creation
#COGNITO_DOMAIN_URI: Will be assigned dynamically after Cognito User pool creation
#CLIENT_ID: Will be assigned dynamically after Cognito User pool creation
#CLIENT_SECRET: Will be assigned dynamically after Cognito User pool creation
#REDIRECT_URI: Will be assigned dynamically after api gateway creation
#AWS_GUARDRAIL_ID: Will be assigned dynamically after guardrail creation
#AWS_GUARDRAIL_VERSION: Will be assigned dynamically after guardrail creation
#REDIS_HOST: Will be assigned dynamically after cache creation
#REDIS_PORT: Will be assigned dynamically after cache creation

############## END  ###################

############## low-level functions  ###################

# enable interactive mode 
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
## end ##

#initialize output files
init_output_files(){

    OUTPUT_DIR="./output"
    
    RESOURCE_FILE="$OUTPUT_DIR/resource_tracker.txt"
    ## delete tracker
    DEL_CHECKPOINT_LOGGER="$OUTPUT_DIR/deletion_checkpoint.log"

    mkdir -p "$OUTPUT_DIR"

    if [ "$RESUME" = false ]; then
        # clear old output file
        > "$RESOURCE_FILE"
        echo "ℹ️ Following resources are created in region: $AWS_REGION " >> "$RESOURCE_FILE"
        echo "========================================" >> "$RESOURCE_FILE"

        # clear old checkpiont file
        > "$DEL_CHECKPOINT_LOGGER"
        source "$DEL_CHECKPOINT_LOGGER"        
    else
        if [ -f "$DEL_CHECKPOINT_LOGGER" ]; then
            source "$DEL_CHECKPOINT_LOGGER"
        else
            echo "deletion_checkpoint.log file not found, do a clean installation."
            exit 0
        fi
    fi
}
## end ##

## create cloudformation stack ##
create_stack() {
    
    local stack_name=$1

    if [ "$stack_name" = "cfn-infra-stack" ]; then
        aws cloudformation deploy --stack-name "$stack_name" \
        --region "$AWS_REGION" --template-file "./stacks/${stack_name}.yaml" \
        --capabilities CAPABILITY_NAMED_IAM \
        --parameter-overrides VPCId=$2 PrivateSubnetIds=$3 EksNodeSecurityGroup=$4
    elif [ "$stack_name" = "cfn-integration-stack" ]; then
        aws cloudformation deploy --stack-name "$stack_name" \
        --region "$AWS_REGION" --template-file "./stacks/${stack_name}.yaml" \
        --parameter-overrides APIGatewayHttpApi=$2 VpcLink=$3 NLBListenerArn=$4 ApiJwtAuthorizer=$5 
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

## get network loadbalancer's listener's ARN from DNS name which is created by k8s service
get_nlb_listener_arn() {
    
    local namespace=$1
    local service_name=$2

    echo "ℹ️ Fetching NLB DNS name..." >&2

    nlb_dns=$(kubectl get svc "$service_name" \
        -n "$namespace" \
        -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

    if [ -z "$nlb_dns" ]; then
        echo "❌ Error: Unable to fetch NLB DNS name."
        return 1
    fi

    echo "✅ Obtained value of nlb_dns is: $nlb_dns" >&2

    echo "ℹ️ Fetching NLB ARN..." >&2
    
    nlb_arn=$(aws elbv2 describe-load-balancers --region "$AWS_REGION" \
        --query "LoadBalancers[?DNSName=='$nlb_dns'].LoadBalancerArn" \
        --output text)
    
    if [ -z "$nlb_arn" ]; then
        echo "❌ Error: Unable to fetch NLB ARN."
        return 1
    fi
    
    echo "✅ Obtained value of nlb_arn is: $nlb_arn" >&2

    echo "ℹ️ Fetching NLB Listener's ARN..." >&2

    query="Listeners[?Port==\`${SERVICE_PORT}\`].ListenerArn"

    nlb_listener_arn=$(aws elbv2 describe-listeners --region "$AWS_REGION" \
        --query "$query" \
        --output text \
        --load-balancer-arn "$nlb_arn")
    
    if [ -z "$nlb_listener_arn" ]; then
        echo "❌ Error: Unable to fetch NLB Listener's ARN."
        return 1
    fi
    
    echo "Obtained value of nlb_listener's arn is: $nlb_listener_arn" >&2
    echo "$nlb_listener_arn"   
    
}

################### low-level functions end ###################

################### high-level functions ###################
## Create parameters in parameter store 
put_parameters(){

    if [ "$resume" = "false" ] || [ -z "${DEL_PARAMETERS:-}" ]; then
        
        echo "Creating .env parameters in AWS Systems Manager Parameter Store..."
        
        ## API_ROOT_PATH ##
        MSYS_NO_PATHCONV=1 aws ssm put-parameter --region $AWS_REGION  --name " /enterprise-rag/API_ROOT_PATH" --value $API_ROOT_PATH \
        --type "String" --description "API Gateway stage root path" --overwrite > /dev/null 2>&1

        if [ $? -ne 0 ]; then
            echo "❌ Error: Failed to create parameter in Parameter Store." \
                "Please ensure AWS credentials have necessary permissions."
            exit 1
        else
            echo "✅ /enterprise-rag/API_ROOT_PATH created."        
            echo "Parameter Store objects:" >> "$RESOURCE_FILE"
            echo "      ✅/enterprise-rag/API_ROOT_PATH" >> "$RESOURCE_FILE"
        fi

        ## EMBEDDING_MODEL_ID ##
        aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/EMBEDDING_MODEL_ID" \
            --value "$EMBEDDING_MODEL_ID" --type "String" --description "embedding model id" --overwrite > /dev/null 2>&1
        echo "✅ /enterprise-rag/EMBEDDING_MODEL_ID created."
        echo "      ✅/enterprise-rag/EMBEDDING_MODEL_ID" >> "$RESOURCE_FILE"

        ## INDEX_NAME ##
        aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/INDEX_NAME" \
            --description "Opensearch collection index name" --value $INDEX_NAME \
            --type "String" --overwrite > /dev/null 2>&1
        echo "✅ /enterprise-rag/INDEX_NAME created."
        echo "      ✅/enterprise-rag/INDEX_NAME" >> "$RESOURCE_FILE"

        ## VECTOR_TOP_K ##
        aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/VECTOR_TOP_K" \
            --description "Top_k matches to be retrieved from vector db" \
            --value "$VECTOR_TOP_K" --type "String" --overwrite > /dev/null 2>&1
        echo "✅ /enterprise-rag/VECTOR_TOP_K created."
        echo "      ✅/enterprise-rag/VECTOR_TOP_K" >> "$RESOURCE_FILE"

        ## RE_RANKED_TOP_K ##
        aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/RE_RANKED_TOP_K" \
            --value $RE_RANKED_TOP_K --type "String" \
            --description "Top-k after re-ranking" --overwrite > /dev/null 2>&1
        echo "✅ /enterprise-rag/RE_RANKED_TOP_K created."
        echo "      ✅/enterprise-rag/RE_RANKED_TOP_K" >> "$RESOURCE_FILE"

        ## LLM_MODEL_ID ##
        aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/LLM_MODEL_ID" \
            --value $LLM_MODEL_ID --type "String" \
            --description "LLM Model ID in bedrock" --overwrite > /dev/null 2>&1
        echo "✅ /enterprise-rag/LLM_MODEL_ID created."
        echo "      ✅/enterprise-rag/LLM_MODEL_ID" >> "$RESOURCE_FILE"

        ## VECTOR_DB_HOSTNAME ##
        VECTOR_DB_HOSTNAME=$(get_value "cfn-services-stack" "cfn-services-stack-OpenSearchCollection")
        aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/VECTOR_DB_HOSTNAME" \
            --value $VECTOR_DB_HOSTNAME --type "String" \
            --description "Opensearch serverless collection name" --overwrite > /dev/null 2>&1
        echo "✅ /enterprise-rag/VECTOR_DB_HOSTNAME created."
        echo "      ✅/enterprise-rag/VECTOR_DB_HOSTNAME" >> "$RESOURCE_FILE"

        ## ENABLE_GUARDRAILS ##
        aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/ENABLE_GUARDRAILS" \
            --value $ENABLE_GUARDRAILS --type "String" \
            --description "Enable input, output guardrails. 0:disable, 1: input guardrail, 2: output guardrail, 3: both" \
            --overwrite > /dev/null 2>&1
        echo "✅ /enterprise-rag/ENABLE_GUARDRAILS created."
        echo "      ✅/enterprise-rag/ENABLE_GUARDRAILS" >> "$RESOURCE_FILE"

        ## AWS_GUARDRAIL_ID ##
        AWS_GUARDRAIL_ID=$(get_value "cfn-services-stack" "cfn-services-stack-GuardrailID")
        aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/AWS_GUARDRAIL_ID" \
            --value $AWS_GUARDRAIL_ID --type "String" \
            --description "Gaurdrail id" --overwrite > /dev/null 2>&1
        echo "✅ /enterprise-rag/AWS_GUARDRAIL_ID created."
        echo "      ✅/enterprise-rag/AWS_GUARDRAIL_ID" >> "$RESOURCE_FILE"

        ## AWS_GUARDRAIL_VERSION ##
        AWS_GUARDRAIL_VERSION=$(get_value "cfn-services-stack" "cfn-services-stack-GuardrailVersion")
        aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/AWS_GUARDRAIL_VERSION" \
            --value $AWS_GUARDRAIL_VERSION --type "String" \
            --description "Gaurdrail version" --overwrite > /dev/null 2>&1
        echo "✅ /enterprise-rag/AWS_GUARDRAIL_VERSION created."
        echo "      ✅/enterprise-rag/AWS_GUARDRAIL_VERSION" >> "$RESOURCE_FILE"

        ## LLM_AS_JUDGE_MODEL_ID ##
        aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/LLM_AS_JUDGE_MODEL_ID" \
            --value $LLM_AS_JUDGE_MODEL_ID --type "String" \
            --description "Model Id for LLM-as-Judge. Use for guardrails" --overwrite > /dev/null 2>&1
        echo "✅ /enterprise-rag/LLM_AS_JUDGE_MODEL_ID created."
        echo "      ✅/enterprise-rag/LLM_AS_JUDGE_MODEL_ID" >> "$RESOURCE_FILE"

        ## FAITHFULNESS_THRESHOLD ##
        aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/FAITHFULNESS_THRESHOLD" \
            --value $FAITHFULNESS_THRESHOLD --type "String" \
            --description "Faithfulness threshold, use to determine hallucination" --overwrite > /dev/null 2>&1
        echo "✅ /enterprise-rag/FAITHFULNESS_THRESHOLD created."
        echo "      ✅/enterprise-rag/FAITHFULNESS_THRESHOLD" >> "$RESOURCE_FILE"

        ## COGNITO_DOMAIN_URI ##
        COGNITO_DOMAIN_URI="https://enterprise-rag.auth.${AWS_REGION}.amazoncognito.com"

        aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/COGNITO_DOMAIN_URI" \
            --value $COGNITO_DOMAIN_URI --type "String" \
            --description "Cognito Domain URI" --overwrite > /dev/null 2>&1
        echo "✅ /enterprise-rag/COGNITO_DOMAIN_URI created."
        echo "      ✅/enterprise-rag/COGNITO_DOMAIN_URI" >> "$RESOURCE_FILE"

        ## CLIENT_ID ##
        CLIENT_ID=$(get_value "cfn-infra-stack" "cfn-infra-stack-CognitoUserpoolClientID")

        aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/CLIENT_ID" \
            --value $CLIENT_ID --type "String" \
            --description "Cognito App client id" --overwrite > /dev/null 2>&1
        echo "✅ /enterprise-rag/CLIENT_ID created."
        echo "      ✅/enterprise-rag/CLIENT_ID" >> "$RESOURCE_FILE"

        
        ## USERPOOL_ID ##
        USERPOOL_ID=$(get_value "cfn-infra-stack" "cfn-infra-stack-CognitoUserpoolID")
        
        CLIENT_SECRET=$(aws cognito-idp describe-user-pool-client \
            --user-pool-id "$USERPOOL_ID" \
            --client-id "$CLIENT_ID" \
            --query "UserPoolClient.ClientSecret" \
            --region "$AWS_REGION" \
            --output text)
        
        if [ $? -ne 0 ]; then
            echo "❌ Error: Failed to get cognito client secret."
            exit 1
        else
            echo "✅ Cognito client secret obtained successfully."        
        fi

        ## CLIENT_SECRET ##
        aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/CLIENT_SECRET" \
            --value $CLIENT_SECRET --type "SecureString" \
            --description "Cognito App client secret" --overwrite > /dev/null 2>&1
        echo "✅ /enterprise-rag/CLIENT_SECRET created."
        echo "      ✅/enterprise-rag/CLIENT_SECRET" >> "$RESOURCE_FILE"

        ## REDIRECT_URI ##
        REDIRECT_URI=$(get_value "cfn-infra-stack" "cfn-infra-stack-APIGatewayUrl")

        aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/REDIRECT_URI" \
            --value "${REDIRECT_URI}" --type "String" \
            --description "Redirect URI for the app, this will be api gateway uri" --overwrite > /dev/null 2>&1
        echo "✅ /enterprise-rag/REDIRECT_URI created."
        echo "      ✅/enterprise-rag/REDIRECT_URI" >> "$RESOURCE_FILE"

        ## Cache Type ##
        aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/CACHE_TYPE" \
            --value "${CACHE_TYPE}" --type "String" \
            --description "Cache settings, 0: disable , 1: redis, 2: local" --overwrite > /dev/null 2>&1
        echo "✅ /enterprise-rag/CACHE_TYPE created."
        echo "      ✅/enterprise-rag/CACHE_TYPE" >> "$RESOURCE_FILE"

        ## Valkey Cache ID ##
        REDIS_HOST=$(get_value "cfn-infra-stack" "cfn-infra-stack-ValkeyEndpoint")

        aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/REDIS_HOST" \
            --value "${REDIS_HOST}" --type "String" \
            --description "Redis hostname" --overwrite > /dev/null 2>&1
        echo "✅ /enterprise-rag/REDIS_HOST created."
        echo "      ✅/enterprise-rag/REDIS_HOST" >> "$RESOURCE_FILE"

        ## Valkey Cache port ##
        REDIS_PORT=$(get_value "cfn-infra-stack" "cfn-infra-stack-ValkeyPort")

        aws ssm put-parameter --region $AWS_REGION --name " /enterprise-rag/REDIS_PORT" \
            --value "${REDIS_PORT}" --type "String" \
            --description "Redis port" --overwrite > /dev/null 2>&1
        echo "✅ /enterprise-rag/REDIS_PORT created."
        echo "      ✅/enterprise-rag/REDIS_PORT" >> "$RESOURCE_FILE"

        echo "----------------------------------" >> "$RESOURCE_FILE"
        echo >> "$RESOURCE_FILE"
        echo "DEL_PARAMETERS=true" >> "$DEL_CHECKPOINT_LOGGER"
        next_step
    else
        echo "ℹ️ skipping parameters creation..."
    fi
}
## end ##

## upload container in ecr ##
upload_container(){

    if [ "$resume" = "false" ] ||  [ -z "${DEL_ECR_REPO:-}" ]; then
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

        echo "DEL_ECR_REPO=true" >> "$DEL_CHECKPOINT_LOGGER"    
        echo "----------------------------------" >> "$RESOURCE_FILE"
        echo >> "$RESOURCE_FILE"
        next_step
    else
        echo "ℹ️ skipping repo creation and container upload..."
    fi        

}
## end ##

## create cfn_s3_stack ##
create_cfn_s3_stack(){

    if [ "$resume" = "false" ] ||  [ -z "${DEL_S3_STACK:-}" ]; then
        echo "Creating cfn-s3-stack..."
        create_stack "cfn-s3-stack"
        echo "cfn-s3-stack:" >> "$RESOURCE_FILE"
        echo "      ✅Bucket: enterprise-rag-lambda-artifacts" >> "$RESOURCE_FILE"
        echo "----------------------------------" >> "$RESOURCE_FILE"
        echo >> "$RESOURCE_FILE"
        echo "DEL_S3_STACK=true" >> "$DEL_CHECKPOINT_LOGGER"
        next_step
    else
        echo "ℹ️ skipping cfn-s3-stack creation..."
    fi
}
## end ##

## uploads lambda artifacts to bucket ##
upload_lambda_artifacts(){
    
    if [ "$resume" = "false" ] || [ -z "${DEL_UPLOADED_FILES:-}" ]; then
        ## upload lambda.zip into bucket  
        echo "Uploading lambda.zip..."
        upload_file lambda.zip
        
        ## upload lambda-layer.zip into bucket  
        echo "Uploading lambda-layer.zip..."
        upload_file lambda-layer.zip

        ## upload authorizer-lambda-layer.zip into bucket  
        echo "Uploading authorizer-lambda-layer.zip..."
        upload_file authorizer-lambda-layer.zip

        ## upload authorizer-lambda.zip into bucket  
        echo "Uploading authorizer-lambda.zip..."
        upload_file authorizer-lambda.zip

        echo "----------------------------------" >> "$RESOURCE_FILE"
        echo >> "$RESOURCE_FILE"
        echo "DEL_UPLOADED_FILES=true" >> "$DEL_CHECKPOINT_LOGGER"
        next_step
    else
        echo "ℹ️ skipping uploading lambda artifacts to artifact bucket..."
    fi
}
## end ## 

## creates cfn-services-stack ##
create_cfn_services_stack(){

    if [ "$resume" = "false" ] || [ -z "${DEL_SERVICES_STACK:-}" ]; then
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
        echo "      ✅Bedrock guardrail: enterprise-rag-guardrail" >> "$RESOURCE_FILE"
        echo "      ✅Bedrock guardrail (enterprise-rag-guardrail) version" >> "$RESOURCE_FILE"
        echo "----------------------------------" >> "$RESOURCE_FILE"
        echo >> "$RESOURCE_FILE"
        echo "DEL_SERVICES_STACK=true" >> "$DEL_CHECKPOINT_LOGGER"
        next_step
    else
        echo "ℹ️ skipping cfn-services-stack creation..." 
    fi
}
## end ##

## creates eks cluster ##
create_eks_cluster(){

    if [ "$resume" = "false" ] || [ -z "${DEL_EKS_CLUSTER:-}" ]; then
        
        echo "creating eks cluster (using eksctl)..."
        eksctl create cluster --name "enterprise-rag" --version "$EKS_K8S_VERSION" --nodegroup-name "eks-ng" \
        --region "$AWS_REGION" --node-type t3.medium --nodes 2
        if [ $? -ne 0 ]; then
            echo "❌ Error: Creating EKS cluster enterprise-rag failed."
            exit 1
        else
            echo "✅ EKS cluster enterprise-rag created successfully."
            echo "✅EKS cluster: enterprise-rag" >> "$RESOURCE_FILE"
            echo "DEL_EKS_CLUSTER=true" >> "$DEL_CHECKPOINT_LOGGER"
        fi 
        next_step
    else
        echo "ℹ️ skipping eks cluster creation..."
    fi

    if [ "$resume" = "false" ] || [ -z "${DEL_LOADBALANCER_CONTROLLER_POLICY:-}" ]; then

        #create IAM policy json for AWS Load Balancer Controller
        echo "ℹ️ creating IAM policy json for AWS Load Balancer Controller..."
        
        curl -o ./output/iam_load_balancer_policy.json \
        https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/install/iam_policy.json

        if [ $? -ne 0 ]; then
            echo "❌ Error: Creating iam_load_balancer_policy.json for AWS Load Balancer Controller failed."
            exit 1
        else
            echo "✅ iam_load_balancer_policy.json  for AWS Load Balancer Controller created successfully."                
        fi 

        #create IAM policy for AWS Load Balancer Controller
        echo "ℹ️ creating IAM policy for AWS Load Balancer Controller..."
        aws iam create-policy \
        --policy-name enterpirse-rag-AWSLoadBalancerControllerIAMPolicy \
        --policy-document file://./output/iam_load_balancer_policy.json

        if [ $? -ne 0 ]; then
            echo "❌ Error: Creating IAM policy for AWS Load Balancer Controller failed."
            exit 1
        else
            echo "✅ IAM policy for AWS Load Balancer Controller created successfully."        
            echo "✅ IAM policy: enterpirse-rag-AWSLoadBalancerControllerIAMPolicy" >> "$RESOURCE_FILE"
            echo "DEL_LOADBALANCER_CONTROLLER_POLICY=true" >> "$DEL_CHECKPOINT_LOGGER"
        fi 
        next_step
    else
        echo "ℹ️ skipping IAM policy json creation..."
    fi

    if [ "$resume" = "false" ] || [ -z "${DEL_IAM_OIDC_PROVIDER:-}" ]; then
        #create IAM OIDC provider
        echo "ℹ️ creating IAM OIDC provider..."
        eksctl utils associate-iam-oidc-provider --region ap-south-1 \
        --cluster enterprise-rag --approve

        if [ $? -ne 0 ]; then
            echo "❌ Error: Creating IAM OIDC provider failed."
            exit 1
        else
            echo "✅ IAM OIDC provider created successfully."
            echo "✅ IAM OIDC provider" >> "$RESOURCE_FILE"
            echo "DEL_IAM_OIDC_PROVIDER=true" >> "$DEL_CHECKPOINT_LOGGER"
        fi
    else
        echo "ℹ️ skipping creation of IAM OIDC provider in eks cluster..."
    fi

    if [ "$resume" = "false" ] || [ -z "${DEL_IAMSERVICEACCOUNT:-}" ]; then
        #create IAM Service Account for AWS Load Balancer Controller
        echo "ℹ️ creating IAM Service Account for AWS Load Balancer Controller..."
        
        eksctl create iamserviceaccount --cluster "enterprise-rag" \
        --namespace kube-system --name enterprise-rag-aws-load-balancer-controller \
        --role-name enterprise-rag-AmazonEKSLoadBalancerControllerRole \
        --region "$AWS_REGION" \
        --attach-policy-arn "arn:aws:iam::${AWS_ACCOUNT_ID}:policy/enterpirse-rag-AWSLoadBalancerControllerIAMPolicy" \
        --approve

        if [ $? -ne 0 ]; then
            echo "❌ Error: Creating IAM Service Account enterprise-rag-aws-load-balancer-controller failed."
            exit 1
        else
            echo "✅ IAM Service Account enterprise-rag-aws-load-balancer-controller created successfully."
            echo "✅ iamserviceaccount=enterprise-rag-aws-load-balancer-controller" >> "$RESOURCE_FILE"
            echo "DEL_IAMSERVICEACCOUNT=true" >> "$DEL_CHECKPOINT_LOGGER"
        fi 
        next_step
    else
        echo "ℹ️ skipping creation of IAM Service Account for AWS Load Balancer Controller..."
    fi
    
    if [ "$resume" = "false" ] || [ -z "${DEL_AWS_LOADBALANCER_CONTROLLER:-}" ]; then
        #install aws-load-balancer-controller
        echo "ℹ️ Installing AWS Load Balancer Controller..."
        
        helm repo add eks https://aws.github.io/eks-charts
        helm repo update

        helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
        -n kube-system \
        --set clusterName=enterprise-rag \
        --set serviceAccount.create=false \
        --set serviceAccount.name=enterprise-rag-aws-load-balancer-controller


        if [ $? -ne 0 ]; then
            echo "❌ Error: installing aws-load-balancer-controller eks/aws-load-balancer-controller failed."
            exit 1
        else
            echo "✅ aws-load-balancer-controller eks/aws-load-balancer-controller installed successfully."
            echo "✅ aws-load-balancer-controller eks/aws-load-balancer-controller" >> "$RESOURCE_FILE"
            echo "DEL_AWS_LOADBALANCER_CONTROLLER=true" >> "$DEL_CHECKPOINT_LOGGER"
        fi 
        next_step
    else
        echo "ℹ️ skipping creation of AWS Load Balancer Controller..."
    fi

    if [ "$resume" = "false" ] || [ -z "${DEL_POD_IDENTITY_ADDON:-}" ]; then
        #create addon eks-pod-identity-agent
        echo "ℹ️ Creating addon eks-pod-identity-agent"
        
        
        if aws eks create-addon --cluster-name enterprise-rag \
        --region "$AWS_REGION" --addon-name eks-pod-identity-agent; then

            echo "✅ addon eks-pod-identity-agent in enterprise-rag cluster is created successfully."        
            echo "✅ eks-pod-identity-agent addon" >> "$RESOURCE_FILE"
            echo "DEL_POD_IDENTITY_ADDON=true" >> "$DEL_CHECKPOINT_LOGGER"
            echo "----------------------------------" >> "$RESOURCE_FILE"
            echo >> "$RESOURCE_FILE"    
            next_step            
        else
            echo "❌ Error: Creating addon eks-pod-identity-agent in enterprise-rag cluster failed."
            exit 1            
        fi 
        
    else
        echo "ℹ️ skipping eks-pod-identity-agent addon creation..."
    fi
}
## end ##

## creates cfn-infra-stack ##
create_cfn_infra_stack(){

    if [ "$resume" = "false" ] || [ -z "${DEL_INFRA_STACK:-}" ]; then
        ## get vpcid from eksctl stack 
        VPC_ID=$(get_value "eksctl-enterprise-rag-cluster" "eksctl-enterprise-rag-cluster::VPC")

        ## get subnetids from eksctl stack 
        SUBNETS=$(get_value "eksctl-enterprise-rag-cluster" "eksctl-enterprise-rag-cluster::SubnetsPrivate")

        ## get security group id from eksctl stack 
        SECURITYGROUPID=$(get_value "eksctl-enterprise-rag-cluster" "eksctl-enterprise-rag-cluster::ClusterSecurityGroupId")

        echo "creating cfn-infra-stack..."
        create_stack "cfn-infra-stack" $VPC_ID $SUBNETS $SECURITYGROUPID
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
        echo "      ✅Valkey cache: enterprise-rag-valkey-cache" >> "$RESOURCE_FILE"
        echo "      ✅Valkey cache security group: enterprise-rag-cache-securitygrp" >> "$RESOURCE_FILE"
        echo "----------------------------------" >> "$RESOURCE_FILE"
        echo >> "$RESOURCE_FILE"
        echo "DEL_INFRA_STACK=true" >> "$DEL_CHECKPOINT_LOGGER"
        next_step
    else
        echo "ℹ️ skipping cfn-infra-stack creation..." 
    fi
}
## end ##

## creates cfn-integration-stack ##
create_cfn_integration_stack(){

    if [ "$resume" = "false" ] || [ -z "${DEL_INTEGRATION_STACK:-}" ]; then
        ## get nlb DNS name, ARN 
        K8S_NLB_LISTENER_ARN=$(get_nlb_listener_arn "enterprise-rag" "enterprise-rag-service")

        if [ $? -eq 0 ]; then
            APIGATEWAYHTTPAPI=$(get_value "cfn-infra-stack" "cfn-infra-stack-APIGatewayId")
            VPCLINK=$(get_value "cfn-infra-stack" "cfn-infra-stack-VpcLinkId")
            APIJWTAUTHORIZER=$(get_value "cfn-infra-stack" "cfn-infra-stack-ApiJwtAuthorizer")
            echo "APIJWTAUTHORIZER=$APIJWTAUTHORIZER"
            next_step
            echo "create cfn-integration-stack..." 
            create_stack "cfn-integration-stack" $APIGATEWAYHTTPAPI $VPCLINK $K8S_NLB_LISTENER_ARN $APIJWTAUTHORIZER 
        fi
        echo "cfn-integration-stack:">> "$RESOURCE_FILE"
        echo "      ✅NLB-APIgw-Integration: enterprise-rag-NLB-APIGw-integration">> "$RESOURCE_FILE"
        echo "      ✅API Gateway Private Routes: RouteKeys: POST /userquery">> "$RESOURCE_FILE"
        echo "      ✅API Gateway Public Route: RouteKeys: (ANY /{proxy+}),root (/)">> "$RESOURCE_FILE"
        echo "      ✅API Gateway Stage: \$default">> "$RESOURCE_FILE"
        echo "----------------------------------" >> "$RESOURCE_FILE"
        echo >> "$RESOURCE_FILE"
        echo "DEL_INTEGRATION_STACK=true" >> "$DEL_CHECKPOINT_LOGGER"
        next_step
    else
        echo "ℹ️ skipping cfn-integration-stack creation..."
    fi
}
## end ##

## creates k8s resources ##
create_k8s_resources(){

    #create enterprise-rag namespace and service account
    if [ "$resume" = "false" ] || [ -z "${DEL_ENTERPRISE_RAG_NAMESPACE:-}" ]; then

        echo "creating enterprise-rag namespace and service account"
        if kubectl apply -f ./k8s-manifests/serviceacc-namespace.yaml; then
            
            echo "✅ Service Account and Namespace created successfully."
            
            until kubectl get sa enterprise-rag-service-account -n enterprise-rag >/dev/null 2>&1
            do
                echo "⌛Waiting for enterprise-rag-service-account..."
                sleep 5
            done

            ## create eso resources
            echo "creating ESO manifests (ExternalSecret)..."
            if kubectl apply -f ./k8s-manifests/eso-manifests/eso-ExternalSecret.yaml; then
                echo "✅ ESO manifests (ExternalSecret) successfully created."
            else
                echo "❌ Error: ESO manifests (ExternalSecret) creation failed."
                exit 1
            fi

            ## create service
            echo "creating k8s manifests (service)..."
            if kubectl apply -f ./k8s-manifests/service.yaml; then
                echo "✅ k8s manifests (service) successfully created."
            else
                echo "❌ k8s manifests (service) creation failed."
                exit 1
            fi

            ROLE_ARN=$(get_value "cfn-infra-stack" "cfn-infra-stack-RetrievalServiceRoleArn")
            echo "create-pod-identity-association for RetrievalServiceRole..."

            if aws eks create-pod-identity-association \
                --region $AWS_REGION \
                --cluster-name "enterprise-rag" \
                --namespace "enterprise-rag" \
                --service-account "enterprise-rag-service-account" \
                --role-arn "$ROLE_ARN"; then

                echo "✅ create-pod-identity-association for RetrievalServiceRole successfully completed."                
                echo "DEL_RETRIEVAL_ROLE_ASSOCIATION=true" >> "$DEL_CHECKPOINT_LOGGER"
            else
                echo "❌ Error: create-pod-identity-association for RetrievalServiceRole failed."
                exit 1
            fi

            until aws eks list-pod-identity-associations \
                --region "$AWS_REGION" \
                --cluster-name enterprise-rag \
                --query "associations[?namespace=='enterprise-rag' && serviceAccount=='enterprise-rag-service-account'] | length(@)" \
                --output text | grep -q '^1$'
            do
                echo "Waiting for Pod Identity Association (enterprise-rag-service-account)..."
                sleep 5
            done

            echo "✅ Pod Identity Association(enterprise-rag-service-account) is available."

            if kubectl apply -f ./k8s-manifests/deployment.yaml;then
                echo "✅ k8s manifests (deployment) successfully created."  
            else
                echo "❌ Error: Creating k8s manifests (deployment) failed."
                exit 1
            fi

            echo "DEL_ENTERPRISE_RAG_NAMESPACE=true" >> "$DEL_CHECKPOINT_LOGGER"
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
        else

            echo "❌ Error: Creating enterprise-rag Service Account and Namespace failed."
            exit 1
        fi
    else
        echo "skipping enterprise-rag K8s manifest creation..."
    fi

}
## end ##

## installs argocd, eso, fluentbit ##
install_argocd_eso_fluentbit(){

    CONTEXT_NAME=$(kubectl config get-contexts -o name | grep enterprise-rag)
    echo "ℹ️ kubectl context name is $CONTEXT_NAME"
    kubectl config use-context "$CONTEXT_NAME"
    
    #install argocd
    if [ "$resume" = "false" ] || [ -z "${DEL_ARGOCD:-}" ]; then
        echo "Installing ArgoCD..."
        kubectl create namespace argocd

        if kubectl apply --server-side -n argocd \
            -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml; then

            echo "✅ ArgoCD installed successfully."    
            echo "DEL_ARGOCD=true" >> "$DEL_CHECKPOINT_LOGGER"
        else 
            echo "❌ Error: Installation of ArgoCD failed."
            exit 1
        fi 
        next_step
    else
        echo "ℹ️ skipping installation of argocd..."
    fi

    #install ESO (service account, namespace and daemonset)
    if [ "$resume" = "false" ] || [ -z "${DEL_ESO:-}" ]; then
        
        echo "Installing External Secrets Operator (ESO)..."
        
        helm repo add external-secrets https://charts.external-secrets.io 
        helm repo update

        if helm install external-secrets external-secrets/external-secrets \
            -n external-secrets --create-namespace --set installCRDs=true; then

            echo "✅ ESO installed successfully."
            echo "DEL_ESO=true" >> "$DEL_CHECKPOINT_LOGGER"

        else
            echo "❌ Error: Installation of ESO failed."
            exit 1                
        fi 
        
        next_step
    else
        echo "ℹ️ skipping installation of ESO..."
    fi

    #create eso servicerole pod-identity-association
    if [ "$resume" = "false" ] || [ -z "${DEL_ESO_ROLE_ASSOCIATION:-}" ]; then

        ESOROLE_ARN=$(get_value "cfn-infra-stack" "cfn-infra-stack-ESOServiceRoleArn")

        #waiting till namespace and service accounts are created. this avoids race condition
        until kubectl get sa external-secrets -n external-secrets >/dev/null 2>&1
        do
            echo "⌛Waiting for ESO service account..."
            sleep 5
        done
        
        echo "create-pod-identity-association for ESOServiceRole..."
        
        if aws eks create-pod-identity-association \
            --region $AWS_REGION \
            --cluster-name "enterprise-rag" \
            --namespace external-secrets \
            --service-account external-secrets \
            --role-arn "$ESOROLE_ARN"; then
        
            echo "✅ create-pod-identity-association for ESOServiceRole completed."                    
            echo "DEL_ESO_ROLE_ASSOCIATION=true" >> "$DEL_CHECKPOINT_LOGGER"
        else
            echo "❌ Error: create-pod-identity-association for ESOServiceRole failed."
            exit 1
        fi 
        next_step   
    else 
        echo "ℹ️ skipping create-pod-identity-association for ESOServiceRole..."
    fi

    #install fluentbit (service account, namespace, daemonset)
    if [ "$resume" = "false" ] || [ -z "${DEL_FLUENTBIT:-}" ]; then
        
        echo "Installing Fluentbit..."
        
        helm repo add eks https://aws.github.io/eks-charts
        helm repo update

        if helm upgrade --install fluent-bit eks/aws-for-fluent-bit \
            --namespace amazon-cloudwatch --create-namespace \
            -f ./k8s-manifests/fluentbit-manifests/fluentbit-values.yaml; then

            echo "✅ Fluentbit installed successfully."
            echo "DEL_FLUENTBIT=true" >> "$DEL_CHECKPOINT_LOGGER"

        else
            echo "❌ Error: Installation of Fluentbit failed."
            exit 1                
        fi 
        
        next_step
    else
        echo "ℹ️ skipping installation of Fluentbit..."
    fi

    #create fluentbit servicerole pod-identity-association
    if [ "$resume" = "false" ] || [ -z "${DEL_FLUENTBIT_ROLE_ASSOCIATION:-}" ]; then

        FLUENTBITROLE_ARN=$(get_value "cfn-infra-stack" "cfn-infra-stack-FluentbitServiceRoleArn")

        #waiting till namespace and service accounts are created. this avoids race condition
        until kubectl get sa fluent-bit -n amazon-cloudwatch >/dev/null 2>&1
        do
            echo "⌛Waiting for Fluentbit service account..."
            sleep 5
        done
        
        echo "create-pod-identity-association for FluentbitServiceRole..."
        
        if aws eks create-pod-identity-association \
            --region $AWS_REGION \
            --cluster-name "enterprise-rag" \
            --namespace amazon-cloudwatch \
            --service-account fluent-bit \
            --role-arn "$FLUENTBITROLE_ARN"; then
        
            echo "✅ create-pod-identity-association for FluentbitServiceRole completed."                    
            echo "DEL_FLUENTBIT_ROLE_ASSOCIATION=true" >> "$DEL_CHECKPOINT_LOGGER"

            #restarting the fluentbit pods after pod-identity association to ensure pods use latest
            #role instead of default
            kubectl rollout restart daemonset/fluent-bit-aws-for-fluent-bit -n amazon-cloudwatch
        else
            echo "❌ Error: create-pod-identity-association for FluentbitServiceRole failed."
            exit 1
        fi 
        next_step   
    else 
        echo "ℹ️ skipping create-pod-identity-association for FluentbitServiceRole..."
    fi
    
    #create ESO CRD
    if [ "$resume" = "false" ] || [ -z "${DEL_ESO_ClusterSecretStore:-}" ]; then
        
        # Wait for CRD
        until kubectl get crd clustersecretstores.external-secrets.io >/dev/null 2>&1
        do
            echo "Waiting for ESO CRDs..."
            sleep 5
        done

        # Wait for ESO webhook deployment
        until kubectl rollout status deployment/external-secrets-webhook \
        -n external-secrets --timeout=10s >/dev/null 2>&1
        do
            echo "Waiting for ESO webhook deployment..."
            sleep 5
        done

        echo "creating ESO manifests (ClusterSecretStore)..."
        
        if kubectl apply -f ./k8s-manifests/eso-manifests/eso-ClusterSecretStores.yaml; then    

            echo "✅ ESO manifests (ClusterSecretStore) successfully created."  
            echo "DEL_ESO_ClusterSecretStore=true" >> "$DEL_CHECKPOINT_LOGGER"    
        else
            echo "❌ Error: ESO manifests (ClusterSecretStore) creation failed."
            exit 1  
        fi

    else
        echo "ℹ️ skipping ESO ClusterSecretStore creation..."
    fi

}
## end ##
##### high-level functions ends #####
############# functions end ###################

################### deployment process ########################
INTERACTIVE=false
RESUME=false
echo ""
echo "*️⃣ *️⃣  Welcome to Enterprise-Rag deployment utility... *️⃣ *️⃣"
echo ""
echo "ℹ️  Script will use enterprise-rag docker image and AWS Credentials to deploy the application on AWS..."
echo "ℹ️  Make sure following prerequisites are done:"
echo "      # Docker engine is running and enterprise-rag image is built."
echo "      # AWS credentials are configured locally in ~/.aws/credentials."
echo "      # AWS_REGION is updated in this script"
echo "      # aws_account_id is updated with actual AWS Account ID in ./k8s-manifests/deployment.yaml."
echo "------------------------------------------------------------------------" 
echo ""
echo "Choose option to proceed:"
echo "      1. Clean installation. (deletion should be done otherwise installation may fail)"
echo "      2. Resume."
echo "      3. Exit."
while true; do
    echo "Enter 1, 2 or 3..."
    read INPUT
    if [ "$INPUT" = "1" ]; then
        break
    elif [ "$INPUT" = "2" ]; then
        RESUME=true
        break
    elif [ "$INPUT" = "3" ]; then
        echo "Deployment aborted."
        exit 0
    else
        continue        
    fi  
done
echo ""
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

echo "▶️ Deploying enterprise-rag...⌛"

echo "ℹ️ getting AWS Account ID from sts get-caller-identity..."

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

if [[ -z "$AWS_ACCOUNT_ID" || "$AWS_ACCOUNT_ID" == "None" ]]; then
        echo "❌ Error: Obtaining AWS_ACCOUNT_ID failed."
        echo "ℹ️ Configure the AWS credentials using aws configure command."
        echo "🛑 Deployment aborted."
        exit 0
fi

START_TIME=$(date +%s)

## init output files
init_output_files

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
install_argocd_eso_fluentbit

## create k8s resources
create_k8s_resources

## create cfn-integration-stack
create_cfn_integration_stack

echo "========================================" >> "$RESOURCE_FILE"
echo "ℹ️ Deployment process completed.🟢 "
cat $RESOURCE_FILE

echo "✅💯🆗enterprise-rag is successfully deployed.✅💯🆗"

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

printf "⏱️ Total time taken in deployment = %02d:%02d (mm:ss)\n" $((ELAPSED/60)) $((ELAPSED%60))    

URL=$(get_value "cfn-infra-stack" "cfn-infra-stack-APIGatewayUrl")

echo "💡 Use this URL to access enterprise-rag system"
echo "$URL/"

