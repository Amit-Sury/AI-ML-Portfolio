#! /bin/bash

#set -e #immediately stop script if any command fails (non-zero exit code)

AWS_REGION="regionname" #Default region
SUCCESS=true
RESOURCES=()
############## function definitions  ###################

## delete cloudformation stack ##
delete_stack() {
    
    local stack_name=$1

    echo "ℹ️ Deleting $stack_name stack"

    aws cloudformation delete-stack --stack-name "$stack_name" \
    --region "$AWS_REGION" 

    aws cloudformation wait stack-delete-complete --stack-name "$stack_name" \
    --region "$AWS_REGION" 

    if [ $? -ne 0 ]; then
        echo "❌ Error: Deleting $stack_name failed."
        RESOURCES+=("$stack_name")
        SUCCESS=false
    else
        echo "✅ Stack $stack_name deleted successfully."
    fi    

}
## end ##

## delete bucket contents
empty_bucket_contents() {

    local BUCKET=$1
    echo "ℹ️ Deleting objects from $BUCKET bucket..."
    
    #check if bucket exists
    if aws s3api head-bucket --bucket "$BUCKET" >/dev/null 2>&1; then
    
        aws s3 rm s3://$BUCKET --recursive 
        if [ $? -ne 0 ]; then
            echo "❌ Error: Deleting objects from $BUCKET bucket failed."
            RESOURCES+=("$BUCKET")
            SUCCESS=false
        else
            echo "✅ Objects from $BUCKET bucket are deleted successfully."
        fi  

    fi

}

delete_parameter(){
    
    echo "ℹ️ Deleting env parameters from the aws parameter store..."
    aws ssm delete-parameters --region $AWS_REGION --names \
        " /enterprise-rag/API_ROOT_PATH" \
        " /enterprise-rag/LLM_MODEL_ID" \
        " /enterprise-rag/EMBEDDING_MODEL_ID" \
        " /enterprise-rag/INDEX_NAME" \
        " /enterprise-rag/VECTOR_TOP_K" \
        " /enterprise-rag/RE_RANKED_TOP_K" \
        " /enterprise-rag/ENABLE_GUARDRAILS" \
        " /enterprise-rag/VECTOR_DB_HOSTNAME" > /dev/null 2>&1

    if [ $? -ne 0 ]; then
        echo "❌ Error: Deleting env parameters from parameter store failed."
        RESOURCES+=("env parameters from Parameter Store")
        SUCCESS=false
    else
        aws ssm delete-parameters --region $AWS_REGION --names \
        " /enterprise-rag/LLM_AS_JUDGE_MODEL_ID" \
        " /enterprise-rag/FAITHFULNESS_THRESHOLD" \
        " /enterprise-rag/COGNITO_DOMAIN_URI" \
        " /enterprise-rag/CLIENT_ID" \
        " /enterprise-rag/CLIENT_SECRET" \
        " /enterprise-rag/REDIRECT_URI" > /dev/null 2>&1

        if [ $? -ne 0 ]; then
            echo "❌ Error: Deleting env parameters from parameter store failed."
            RESOURCES+=("env parameters from Parameter Store")
            SUCCESS=false
        else
            echo "✅ All env parameters are deleted successfully from parameter store."
        fi
    fi
    
}
## end ##

delete_pod_identity_association(){

    local NAMESPACE=$1
    local SERVICEACC=$2

    local ASSOCIATION_ID=$(aws eks list-pod-identity-associations \
            --cluster-name enterprise-rag \
            --namespace $NAMESPACE \
            --service-account $SERVICEACC \
            --region $AWS_REGION \
            --query "associations[0].associationId" \
            --output text)

    echo "ℹ️ Association ID for $SERVICEACC is $ASSOCIATION_ID"
    echo "ℹ️ Deleting $ASSOCIATION_ID"

    aws eks delete-pod-identity-association \
      --cluster-name "enterprise-rag" \
      --region $AWS_REGION \
      --association-id "$ASSOCIATION_ID"

    if [ $? -ne 0 ]; then
        echo "❌ Error: Deleting association $ASSOCIATION_ID failed."   
        RESOURCES+=("Pod-identity-association-id:$ASSOCIATION_ID")
        SUCCESS=false 
    else
        echo "✅ Association $ASSOCIATION_ID deleted successfully."
    fi

}
## end ##

## delete k8s manifest
delete_manifest(){

    #set context to eks cluster
    CONTEXT_NAME=$(kubectl config get-contexts -o name | grep enterprise-rag)
    echo "ℹ️ kubectl context name is $CONTEXT_NAME"
    echo "ℹ️ Setting current context to $CONTEXT_NAME"
    kubectl config use-context "$CONTEXT_NAME"

    ## delete all K8s and ESO resources
    echo "ℹ️ Deleting all resources present in cluster namespace enterprise-rag..."
    kubectl delete namespace "enterprise-rag"
    if [ $? -ne 0 ]; then
        echo "❌ Error: Deleting K8s manifests in namespace enterprise-rag"
        RESOURCES+=("K8s manifests")
        SUCCESS=false    
    else
        echo "✅ K8s manifests in enterprise-rag namespace are deleted successfully."
    fi 
}
## end ##
################### functions  end ########################

################### delete process ########################

echo "ℹ️  This script will delete all the resources of enterprise-rag"
echo "⚠️  Note ⚠️"
echo "*After the deletion process completes, it is recommended to manually verify the following AWS services from the AWS Console."
echo "*(EKS, OpenSearch Serverless, EC2, S3, Lambda, API Gateway, Cloudformation)" 
echo "*This helps ensure that all resources have been deleted successfully and prevents any unintended AWS charges."

echo "ℹ️  Do you want to proceed with deletion? (y/n): "
read PROCEED
if [[ "$PROCEED" != "y" && "$PROCEED" != "Y" ]]; then
    echo "Deletion aborted."
    exit 0
fi

OUTPUT_DIR="output"
CHECKPOINT_LOGGER="$OUTPUT_DIR/deletion_checkpoint.log"

if [ -f "$CHECKPOINT_LOGGER" ]; then
    source "$CHECKPOINT_LOGGER"
else
    echo "Checkpoint file not found, delete resources manually."
    exit 0
fi

echo "ℹ️ Starting cleanup..."


## delete cfn-integration-stack
if [ -n "$DEL_INTEGRATION_STACK" ]; then
    delete_stack "cfn-integration-stack"
fi

## delete pod-identity-association for RetrievalServiceRole
if [ -n "$DEL_RETRIEVAL_ROLE_ASSOCIATION" ]; then
    delete_pod_identity_association "enterprise-rag" "enterprise-rag-service-account"   
fi

#delete K8s manifests
if [ -n "$DEL_MANIFESTS" ]; then
    delete_manifest    
fi

## delete pod-identity-association for ESORole
if [ -n "$DEL_ESO_ROLE_ASSOCIATION" ]; then
    delete_pod_identity_association "external-secrets" "external-secrets"
fi

## delete parameters from parameter store
if [ -n "$DEL_PARAMETERS" ]; then
    delete_parameter
fi

## delete "cfn-infra-stack"
if [ -n "$DEL_INFRA_STACK" ]; then
    delete_stack "cfn-infra-stack"
fi

## delete eks cluster
if [ -n "$DEL_EKS_CLUSTER" ]; then
    eksctl delete cluster --name "enterprise-rag" --region "$AWS_REGION" 
    if [ $? -ne 0 ]; then
        echo "❌ Error: Deleting eks cluster failed."   
        RESOURCES+=("EKS Cluster enterprise-rag")
        SUCCESS=false 
    else
        echo "✅ eks cluster deleted successfully."
    fi 
fi

## delete cfn-services-stack 
if [ -n "$DEL_SERVICES_STACK" ]; then
    empty_bucket_contents "enterprise-rag-knowledge-docs"
    delete_stack "cfn-services-stack"
fi

## delete lambda artifact contents 
if [ -n "$DEL_UPLOADED_FILES" ]; then
    empty_bucket_contents "enterprise-rag-lambda-artifacts"
fi

#delete cfn-s3-stack
if [ -n "$DEL_S3_STACK" ]; then
    delete_stack "cfn-s3-stack"
fi

#delete ecr
if [ -n "$DEL_ECR_REPO" ]; then

    echo "ℹ️ Deleting enterprise-rag repo in ecr."
    aws ecr delete-repository --repository-name enterprise-rag --region $AWS_REGION --force > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to delete repo(enterprise-rag) from ECR."    
        RESOURCES+=("ECR Repo: enterprise-rag")
        SUCCESS=false
    else
        echo "✅ ECR Repo(enterprise-rag) is deleted successfully."
    fi
fi

if [ "$SUCCESS" = true ]; then
    echo "✅💯🆗 All resources are successfully deleted. ✅💯🆗"    
else
    echo "🛑 Following resources could not be deleted. Try deleting from AWS console. 🛑"
    for resource in "${RESOURCES[@]}"; do
        echo "$resource"
    done
fi    


