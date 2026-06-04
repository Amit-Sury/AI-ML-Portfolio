#! /bin/bash

#VARIABLES BLOCK, update as per your setup
AWS_REGION="ap-south-1" #Default region
#VARIABLES BLOCK END

echo "This script will delete gitrepoassist-ai related resources from AWS."
echo "Do you want to continue? (y/n): "
read CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo "Operation aborted."
    exit 0
fi

echo "Starting deletion process..."
echo "Delete env parameters from the parameter store..."

aws ssm delete-parameters --region $AWS_REGION --names \
    " /gitrepoassist-ai/GITHUB_APP_ID" \
    " /gitrepoassist-ai/GITHUB_APP_PRIVATE_KEY" \
    " /gitrepoassist-ai/GITHUB_REPOSITORY" \
    " /gitrepoassist-ai/OPENAI_API_KEY" \
    " /gitrepoassist-ai/LLM_TYPE" \
    " /gitrepoassist-ai/LLM_MODEL_ID" \
    " /gitrepoassist-ai/AWS_REGION" \
    " /gitrepoassist-ai/BASE_URL" > /dev/null 2>&1

aws ssm delete-parameters --region $AWS_REGION --names \
    " /gitrepoassist-ai/HISTORY_PATH" \
    " /gitrepoassist-ai/LOG_PATH" \
    " /gitrepoassist-ai/DEBUG_LOG" \
    " /gitrepoassist-ai/WRITE_LANGCHAIN_MSGS" \
    " /gitrepoassist-ai/LANGCHAIN_TRACING_V2" \
    " /gitrepoassist-ai/LANGCHAIN_API_KEY" \
    " /gitrepoassist-ai/LANGCHAIN_PROJECT" \
    " /gitrepoassist-ai/LANGCHAIN_ENDPOINT" > /dev/null 2>&1


echo "✅ All env parameters are deleted successfully."

echo "Deleting gitrepoassist-ai repo in ecr."
aws ecr delete-repository --repository-name gitrepoassist-ai --region $AWS_REGION --force > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to delete repo from ECR. Kindly try deleting from console."    
else
    echo "✅ ECR Repo is deleted successfully."
fi

echo "Deletion cloudformation stack..."
aws cloudformation delete-stack --stack-name gitrepoassist-ai --region $AWS_REGION > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to delete CloudFormation stack. Kindly try deleting from console."    
else
    echo "✅ CloudFormation stack deletion initiated successfully."
fi

echo "Deletion process completed."