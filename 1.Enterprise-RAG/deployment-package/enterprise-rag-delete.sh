#! /bin/bash


AWS_REGION="ap-south-1" #Default region

############## function definitions  ###################

SUCCESS=true
RESOURCES=()

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
        local key=$2
        sed -i "/^${key}=true$/d" "$CHECKPOINT_LOGGER"      
    fi    

}
## end ##

## delete bucket contents
empty_bucket_contents() {

    local BUCKET=$1
    echo "ℹ️ Deleting objects from $BUCKET bucket..."
    
    #check if bucket exists
    if aws s3api head-bucket --bucket "$BUCKET" >/dev/null 2>&1; then
    
        if aws s3 rm s3://$BUCKET --recursive; then 
            echo "✅ Objects from $BUCKET bucket are deleted successfully."
        else
            echo "❌ Error: Deleting objects from $BUCKET bucket failed."
            RESOURCES+=("$BUCKET")
            SUCCESS=false        
        fi  

    fi

}

delete_parameter(){
    
    echo "ℹ️ Deleting env parameters from the aws parameter store..."
    aws ssm delete-parameters --region $AWS_REGION --names \
        " /enterprise-rag/API_ROOT_PATH" \
        " /enterprise-rag/EMBEDDING_MODEL_ID" \
        " /enterprise-rag/INDEX_NAME" \
        " /enterprise-rag/VECTOR_TOP_K" \
        " /enterprise-rag/RE_RANKED_TOP_K" \
        " /enterprise-rag/LLM_MODEL_ID" \
        " /enterprise-rag/VECTOR_DB_HOSTNAME" \
        " /enterprise-rag/ENABLE_GUARDRAILS" \
        " /enterprise-rag/AWS_GUARDRAIL_ID" \
        " /enterprise-rag/AWS_GUARDRAIL_VERSION" > /dev/null 2>&1
        
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
        " /enterprise-rag/REDIRECT_URI" \
        " /enterprise-rag/CACHE_TYPE" \
        " /enterprise-rag/REDIS_HOST" \
        " /enterprise-rag/REDIS_PORT" > /dev/null 2>&1

        if [ $? -ne 0 ]; then
            echo "❌ Error: Deleting env parameters from parameter store failed."
            RESOURCES+=("env parameters from Parameter Store")
            SUCCESS=false
        else
            echo "✅ All env parameters are deleted successfully from parameter store."
            local key=$1
            sed -i "/^${key}=true$/d" "$CHECKPOINT_LOGGER"
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

    if aws eks delete-pod-identity-association \
      --cluster-name "enterprise-rag" \
      --region $AWS_REGION \
      --association-id "$ASSOCIATION_ID"; then

      echo "✅ Association $ASSOCIATION_ID deleted successfully."
      local key=$3
      sed -i "/^${key}=true$/d" "$CHECKPOINT_LOGGER"

    else
        echo "❌ Error: Deleting association $ASSOCIATION_ID failed."   
        RESOURCES+=("Pod-identity-association-id:$ASSOCIATION_ID")
        SUCCESS=false 
    fi

}
## end ##

## delete k8s manifest
delete_manifest(){

    ## delete all K8s and ESO resources
    echo "ℹ️ Deleting all resources present in cluster namespace enterprise-rag..."
    
    if kubectl delete namespace "enterprise-rag"; then
        echo "✅ K8s manifests in enterprise-rag namespace are deleted successfully."
        local key=$1
        sed -i "/^${key}=true$/d" "$CHECKPOINT_LOGGER"
    else
        echo "❌ Error: Deleting K8s manifests in namespace enterprise-rag"
        RESOURCES+=("K8s manifests")
        SUCCESS=false    
    fi 
}
## end ##

## delete iamserviceaccount for aws-load-balancer controller
delete_iamserviceaccount(){

    #delete iamserviceaccount
    if eksctl delete iamserviceaccount --cluster enterprise-rag \
    --namespace kube-system --name enterprise-rag-aws-load-balancer-controller \
    --region "$AWS_REGION"; then

        echo "✅ iamserviceaccount enterprise-rag-aws-load-balancer-controller deleted successfully."
        local key=$1
        sed -i "/^${key}=true$/d" "$CHECKPOINT_LOGGER"
    else
        
        echo "❌ Error: Deleting iamserviceaccount enterprise-rag-aws-load-balancer-controller failed."   
        RESOURCES+=("iamserviceaccount enterprise-rag-aws-load-balancer-controller")
        SUCCESS=false 
    fi 
    
}
## end ##

## delete iam policy
delete_iampolicy(){

    if aws iam delete-policy \
    --policy-arn "arn:aws:iam::${AWS_ACCOUNT_ID}:policy/enterpirse-rag-AWSLoadBalancerControllerIAMPolicy"; then 
    
        echo "✅ IAM policy enterpirse-rag-AWSLoadBalancerControllerIAMPolicy deleted successfully."
        local key=$1
        sed -i "/^${key}=true$/d" "$CHECKPOINT_LOGGER"
    else
        
        echo "❌ Error: Deleting iam policy enterpirse-rag-AWSLoadBalancerControllerIAMPolicy failed."   
        RESOURCES+=("IAM policy enterpirse-rag-AWSLoadBalancerControllerIAMPolicy")
        SUCCESS=false 
    fi

}    
## end ##

## delete eks cluster
delete_ekscluster(){

    if eksctl delete cluster --name "enterprise-rag" --region "$AWS_REGION"; then 
        echo "✅ eks cluster deleted successfully."
        local key=$1
        sed -i "/^${key}=true$/d" "$CHECKPOINT_LOGGER"
    else
        echo "❌ Error: Deleting eks cluster failed."   
        RESOURCES+=("EKS Cluster enterprise-rag")
        SUCCESS=false 
    fi 

}    
## end ##

## delete iam oidc provider ##
delete_eks_oidc_provider() {
    
    local CLUSTER_NAME="enterprise-rag"
    local REGION="ap-south-1"

    local ISSUER_URL
    ISSUER_URL=$(aws eks describe-cluster \
        --name "$CLUSTER_NAME" \
        --region "$REGION" \
        --query 'cluster.identity.oidc.issuer' \
        --output text)

    if [[ -z "$ISSUER_URL" || "$ISSUER_URL" == "None" ]]; then
        echo "No OIDC issuer found for cluster: $CLUSTER_NAME"
        echo "❌ Error: Deleting iam oidc provider failed."   
        RESOURCES+=("iam oidc provider")
        SUCCESS=false 
        return 1
    fi

    local PROVIDER_URL=${ISSUER_URL#https://}
    
    local OIDC_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/${PROVIDER_URL}"

    echo "Deleting OIDC provider:"
    echo "  $OIDC_ARN"

    if aws iam delete-open-id-connect-provider \
        --open-id-connect-provider-arn "$OIDC_ARN"; then

        echo "✅ OIDC provider deleted successfully."
        local key=$1
        sed -i "/^${key}=true$/d" "$CHECKPOINT_LOGGER"
    else
        echo "❌ Error: Deleting iam oidc provider failed."   
        RESOURCES+=("iam oidc provider")
        SUCCESS=false 
        return 1
    fi
}
## end ##

## delete aws loadbalancer controller
delete_awsloadbalancer_controller(){

    if helm uninstall aws-load-balancer-controller -n kube-system; then
        echo "✅ aws loadbalancer controller deleted successfully."
        local key=$1
        sed -i "/^${key}=true$/d" "$CHECKPOINT_LOGGER"
    else
        echo "❌ Error: Deleting aws loadbalancer controller failed."   
        RESOURCES+=("aws loadbalancer controller")
        SUCCESS=false 
        return 1
    fi
}
## end ##

## delete pod identity addon
delete_pod_identity_addon(){
    
    if aws eks delete-addon --cluster-name enterprise-rag \
        --region ap-south-1 --addon-name eks-pod-identity-agent; then
        echo "✅ eks-pod-identity-agent is delete successfully."
        local key=$1
        sed -i "/^${key}=true$/d" "$CHECKPOINT_LOGGER"
    else
        echo "❌ Error: Deleting eks-pod-identity-agent failed."   
        RESOURCES+=("eks-pod-identity-agent")
        SUCCESS=false 
        return 1
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

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

if [[ -z "$AWS_ACCOUNT_ID" || "$AWS_ACCOUNT_ID" == "None" ]]; then
        echo "❌ Error: Obtaining AWS_ACCOUNT_ID failed."
        echo "ℹ️ Configure the AWS credentials using aws configure command."
        echo "🛑 Deletion aborted."
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

CONTEXT_NAME=$(kubectl config get-contexts -o name | grep enterprise-rag)

echo "ℹ️ enterprise-rag kubectl context name is $CONTEXT_NAME"
echo "ℹ️ setting kubectl current context to $CONTEXT_NAME"
kubectl config use-context "$CONTEXT_NAME"

## delete cfn-integration-stack
if [ -n "$DEL_INTEGRATION_STACK" ]; then
    delete_stack "cfn-integration-stack" "DEL_INTEGRATION_STACK"
fi

#delete K8s manifests
if [ -n "$DEL_ENTERPRISE_RAG_NAMESPACE" ]; then
    delete_manifest "DEL_ENTERPRISE_RAG_NAMESPACE"
fi

## delete pod-identity-association for RetrievalServiceRole
if [ -n "$DEL_RETRIEVAL_ROLE_ASSOCIATION" ]; then
    delete_pod_identity_association "enterprise-rag" "enterprise-rag-service-account" "DEL_RETRIEVAL_ROLE_ASSOCIATION"
fi

if [ -n "$DEL_ESO_ClusterSecretStore" ]; then
    
    if kubectl delete -f ./k8s-manifests/eso-manifests/eso-ClusterSecretStores.yaml; then
        echo "✅eso-ClusterSecretStores deleted successfully"
        sed -i "/^DEL_ESO_ClusterSecretStore=true$/d" "$CHECKPOINT_LOGGER"
    else 
        echo "❌ eso-ClusterSecretStores deleted failed"
    fi
fi


## delete pod-identity-association for FluentbitRole
if [ -n "$DEL_FLUENTBIT_ROLE_ASSOCIATION" ]; then
    delete_pod_identity_association "amazon-cloudwatch" "fluent-bit" "DEL_FLUENTBIT_ROLE_ASSOCIATION"
fi

## delete fluentbit 
if [ -n "$DEL_FLUENTBIT" ]; then

    if helm uninstall fluent-bit -n amazon-cloudwatch; then
        echo "✅Fluentbit is uninstalled successfully"
        
        if kubectl delete namespace amazon-cloudwatch; then
            echo "✅amazon-cloudwatch namespace deleted successfully"
            sed -i "/^DEL_FLUENTBIT=true$/d" "$CHECKPOINT_LOGGER"
        else 
            echo "❌ amazon-cloudwatch namespace deleted failed"
        fi
    else
        echo "❌ Fluentbit uninstallation failed"
    fi
fi


## delete pod-identity-association for ESORole
if [ -n "$DEL_ESO_ROLE_ASSOCIATION" ]; then
    delete_pod_identity_association "external-secrets" "external-secrets" "DEL_ESO_ROLE_ASSOCIATION"
fi

## delete eso 
if [ -n "$DEL_ESO" ]; then

    if helm uninstall external-secrets -n external-secrets; then
        echo "✅ESO is uninstalled successfully"
        if kubectl delete namespace external-secrets; then
            echo "✅external-secrets namespace deleted successfully"
            sed -i "/^DEL_ESO=true$/d" "$CHECKPOINT_LOGGER"
        else 
            echo "❌ external-secrets namespace deleted failed"
        fi
    else
        echo "❌ ESO uninstallation failed"
    fi
fi

## delete argocd
if [ -n "$DEL_ARGOCD" ]; then
    if kubectl delete namespace argocd; then
        echo "argocd namespace deleted successfully"
        sed -i "/^DEL_ARGOCD=true$/d" "$CHECKPOINT_LOGGER"
    else 
        echo "❌ argocd namespace deleted failed"
    fi
fi


## delete parameters from parameter store
if [ -n "$DEL_PARAMETERS" ]; then
    delete_parameter "DEL_PARAMETERS"
fi

## delete "cfn-infra-stack"
if [ -n "$DEL_INFRA_STACK" ]; then
    delete_stack "cfn-infra-stack" "DEL_INFRA_STACK"
fi

## delete pod-identity-addon
if [ -n "$DEL_POD_IDENTITY_ADDON" ]; then
    delete_pod_identity_addon "DEL_POD_IDENTITY_ADDON"
fi

## uninstall aws-load-balancer-controller
if [ -n "$DEL_AWS_LOADBALANCER_CONTROLLER" ]; then
    delete_awsloadbalancer_controller "DEL_AWS_LOADBALANCER_CONTROLLER"
fi

## delete iamservice account for aws-load-balancer-controller
if [ -n "$DEL_IAMSERVICEACCOUNT" ]; then
    delete_iamserviceaccount "DEL_IAMSERVICEACCOUNT"
fi

## delete iam oidc provider
if [ -n "$DEL_IAM_OIDC_PROVIDER" ]; then
    delete_eks_oidc_provider "DEL_IAM_OIDC_PROVIDER"
fi

## delete iam policy for aws-load-balancer-controller
if [ -n "$DEL_LOADBALANCER_CONTROLLER_POLICY" ]; then
    delete_iampolicy "DEL_LOADBALANCER_CONTROLLER_POLICY"
fi

## delete eks cluster
if [ -n "$DEL_EKS_CLUSTER" ]; then
    delete_ekscluster "DEL_EKS_CLUSTER"
fi

## delete cfn-services-stack 
if [ -n "$DEL_SERVICES_STACK" ]; then
    empty_bucket_contents "enterprise-rag-knowledge-docs"
    delete_stack "cfn-services-stack" "DEL_SERVICES_STACK"
fi

## delete lambda artifact contents 
if [ -n "$DEL_UPLOADED_FILES" ]; then
    empty_bucket_contents "enterprise-rag-lambda-artifacts" 
    sed -i "/^DEL_UPLOADED_FILES=true$/d" "$CHECKPOINT_LOGGER"
fi

#delete cfn-s3-stack
if [ -n "$DEL_S3_STACK" ]; then
    delete_stack "cfn-s3-stack" "DEL_S3_STACK"
fi

#delete ecr
if [ -n "$DEL_ECR_REPO" ]; then

    echo "ℹ️ Deleting enterprise-rag repo in ecr."
    if aws ecr delete-repository --repository-name enterprise-rag --region $AWS_REGION --force ; then 
            echo "✅ ECR Repo(enterprise-rag) is deleted successfully."
            sed -i "/^DEL_ECR_REPO=true$/d" "$CHECKPOINT_LOGGER"
    else
        echo "❌ Error: Failed to delete repo(enterprise-rag) from ECR."    
        RESOURCES+=("ECR Repo: enterprise-rag")
        SUCCESS=false
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


