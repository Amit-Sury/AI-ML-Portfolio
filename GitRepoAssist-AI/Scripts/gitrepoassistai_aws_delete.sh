#! /bin/bash

#VARIABLES BLOCK, update as per your setup
AWS_REGION="ap-south-1" #Default region
#VARIABLES BLOCK END

echo "This script will delete Gitmate-AI related resources from AWS."
echo "Do you want to continue? (y/n): "
read CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo "Operation aborted."
    exit 0
fi

echo "Starting deletion process..."
echo "Delete env parameters from the parameter store..."

aws ssm delete-parameters --region $AWS_REGION --names \
    " /gitmate-ai/GITHUB_APP_ID" \
    " /gitmate-ai/GITHUB_APP_PRIVATE_KEY" \
    " /gitmate-ai/GITHUB_REPOSITORY" \
    " /gitmate-ai/OPENAI_API_KEY" \
    " /gitmate-ai/LLM_TYPE" \
    " /gitmate-ai/LLM_MODEL_ID" \
    " /gitmate-ai/AWS_REGION" \
    " /gitmate-ai/BASE_URL" > /dev/null 2>&1

aws ssm delete-parameters --region $AWS_REGION --names \
    " /gitmate-ai/HISTORY_PATH" \
    " /gitmate-ai/LOG_PATH" \
    " /gitmate-ai/DEBUG_LOG" \
    " /gitmate-ai/WRITE_LANGCHAIN_MSGS" \
    " /gitmate-ai/LANGCHAIN_TRACING_V2" \
    " /gitmate-ai/LANGCHAIN_API_KEY" \
    " /gitmate-ai/LANGCHAIN_PROJECT" \
    " /gitmate-ai/LANGCHAIN_ENDPOINT" > /dev/null 2>&1


echo "✅ All env parameters are deleted successfully."

echo "Deleting gitmate-ai repo in ecr."
aws ecr delete-repository --repository-name gitmate-ai --region $AWS_REGION --force > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to delete repo from ECR. Kindly try deleting from console."    
else
    echo "✅ ECR Repo is deleted successfully."
fi

echo "Deletion cloudformation stack..."
aws cloudformation delete-stack --stack-name gitmate-ai --region $AWS_REGION > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to delete CloudFormation stack. Kindly try deleting from console."    
else
    echo "✅ CloudFormation stack deletion initiated successfully."
fi

echo "Deletion process completed."
