#! /bin/bash

#VARIABLES BLOCK, update as per your setup

#AWS Parameters
AWS_ACCOUNT_ID="**********" #Your AWS Account ID
AWS_REGION="ap-south-1" #Default region
VPC_CIDR="10.0.1.0/26" #VPC CIDR block
SUBNET1_CIDR="10.0.1.0/27" #Subnet 1 CIDR block
SUBNET2_CIDR="10.0.1.32/27" #Subnet 2 CIDR block
SUBNET1_AZ="${AWS_REGION}a" #Subnet 1 Availability Zone
SUBNET2_AZ="${AWS_REGION}b" #Subnet 2 Availability Zone
INSTANCE_TYPE="t3.micro" #EC2 Instance Type
INSTANCE_AMI="ami-03695d52f0d883f65" #Amazon Linux 2 AMI, free-tier eligible
KEY_PAIR="GitMateKeyPair" #Existing Key Pair name for EC2 instance
EC2_IAM_PROFILE="GitMateAI-EC2InstanceProfile" #Existing IAM Instance Profile name
#AWS Parameters END

#GitMate-AI Parameters
GITHUB_APP_ID="********" #GitHub App ID
GITHUB_REPOSITORY="UserName/RepoName" #GitHub Repository name
GITHUB_APP_PRIVATEKEY_PATH="./github.private-key.pem" #Path to GitHub App Private Key file
OPENAI_API_KEY_PATH="./openai.key" #Path to OpenAI API Key file
LLM_TYPE="3" #LLM Type # 1: Ollama, # 2: AWS Bedrock Claude Haiku, # 3: GPT
LLM_MODEL_ID="gpt-5-nano" #LLM Model ID # AWS: anthropic.claude-3-haiku-20240307-v1:0 # GPT: gpt-5-nano
AWS_BEDROCK_REGION=${AWS_REGION} #AWS Region for Bedrock LLM #Example regions: us-east-1, us-west-2, eu-west-1, ap-south-1
OLLAMA_BASE_URL="http://host.docker.internal:11434" #Ollama base URL #local use: http://localhost:11434 #For docker: http://host.docker.internal:11434
HISTORY_PATH="./history/" #Path to save conversation history
LOG_PATH="./logs/" #Path to save logs
DEBUG_LOG="1" #Toggle log generation 1:enable 0:disable
WRITE_LANGCHAIN_MSGS="1" #Toggle LLM message conversation generation 1:enable 0:disable
LANGCHAIN_TRACING_V2="false" #langsmith env variables
LANGCHAIN_API_KEY="privatekey" #langsmith env variables
LANGCHAIN_PROJECT="my-sample-project" #langsmith env variables
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com" #langsmith env variables
#GitMate-AI Parameters END
#VARIABLES BLOCK END

echo "Welcome to GitMate-AI deployment utility..."
echo "Sript will use GitMate-AI docker image and your AWS Credentials to deploy the application on AWS..."
echo "Make sure you have build the image and AWS credentials are configured before proceeding..."
echo "Do you want to continue? (y/n): "
read CONTINUE
if [[ "$CONTINUE" != "y" && "$CONTINUE" != "Y" ]]; then
    echo "Deployment aborted."
    exit 0
fi  

echo "Starting deployment with following parameters. Kindly check these are upto date:"
echo "AWS Account ID: $AWS_ACCOUNT_ID"    
echo "AWS Region: $AWS_REGION"
echo "VPC CIDR: $VPC_CIDR"
echo "Subnet 1 CIDR: $SUBNET1_CIDR"
echo "Subnet 2 CIDR: $SUBNET2_CIDR"
echo "Subnet 1 AZ: $SUBNET1_AZ"
echo "Subnet 2 AZ: $SUBNET2_AZ"
echo "EC2 Instance Type: $INSTANCE_TYPE"
echo "EC2 Instance AMI: $INSTANCE_AMI"
echo "EC2 Key Pair: $KEY_PAIR"
echo "EC2 IAM Instance Profile: $EC2_IAM_PROFILE"   

echo "Do you want to proceed with deployment? (y/n): "
read PROCEED
if [[ "$PROCEED" != "y" && "$PROCEED" != "Y" ]]; then
    echo "Deployment aborted."
    exit 0
fi

echo "Starting deployment..."

############### ECR creation START ########################   

echo "Checking if repo gitmate-ai already exists in AWS ECR..."

if aws ecr describe-repositories --repository-names gitmate-ai \
     --region "$AWS_REGION" >/dev/null 2>&1; then
  echo "ℹ️ Repo already exists. Proceeding with next steps..."
else
  echo "⚙️ Repo doesn't exists. Creating repo..."
  aws ecr create-repository --repository-name gitmate-ai --region $AWS_REGION 
fi

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to create repo in AWS ECR."
    exit 1
else
    echo "✅ Repo gitmate-ai created successfully."
fi  
############### ECR creation END ########################

############### Tag and push docker image ################

echo "Tagging and pushing docker image to ECR repository..."
ECR_REPO_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

docker tag gitmate-ai:latest ${ECR_REPO_URI}/gitmate-ai:latest
if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to tag docker image. Make sure the image 'gitmate-ai:latest' exists" \
     "locally and docker engine is running."
    exit 1
else
    echo "✅ Tagging docker image is successful."
fi  

echo "Docker image tagged: ${ECR_REPO_URI}/gitmate-ai:latest"
echo "Logging in to AWS ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin ${ECR_REPO_URI}

if [ $? -ne 0 ]; then
    echo "❌ Error: Docker login to ECR failed. Please check your AWS credentials and docker setup."
    exit 1
else
    echo "✅ Docker login to ECR successful."
fi

echo "Pushing docker image to ECR repository..."
docker push ${ECR_REPO_URI}/gitmate-ai:latest

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to push Docker image to ECR."
    exit 1
else
    echo "✅ Docker image pushed to ECR successfully."
fi

############### Tag and push docker image END ################

######### Creating parameters in parameter store ############
echo "Creating .env parameters in AWS Systems Manager Parameter Store..."

aws ssm put-parameter --region $AWS_REGION  --name " /gitmate-ai/GITHUB_APP_ID" --value $GITHUB_APP_ID \
 --type "String" --description "GITHUB APP ID" > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to create parameter in Parameter Store." \
        "Please ensure AWS credentials have necessary permissions."
    exit 1
else
    echo " /gitmate-ai/GITHUB_APP_ID created."
fi

VALUE=$(cat $GITHUB_APP_PRIVATEKEY_PATH)

aws ssm put-parameter --region $AWS_REGION --name " /gitmate-ai/GITHUB_APP_PRIVATE_KEY" --value "$VALUE" \
    --type "SecureString" --description "GITHUB APP Private key" > /dev/null 2>&1
echo " /gitmate-ai/GITHUB_APP_PRIVATE_KEY created."

aws ssm put-parameter --region $AWS_REGION --name " /gitmate-ai/GITHUB_REPOSITORY" \
    --description "GITHUB Repo name" --value $GITHUB_REPOSITORY --type "String" > /dev/null 2>&1
echo " /gitmate-ai/GITHUB_REPOSITORY created."

OPENAI_KEYVALUE=$(cat $OPENAI_API_KEY_PATH)

aws ssm put-parameter --region $AWS_REGION --name " /gitmate-ai/OPENAI_API_KEY" \
    --description "Open API private key" \
    --value "$OPENAI_KEYVALUE" --type "SecureString" > /dev/null 2>&1
echo " /gitmate-ai/OPENAI_API_KEY created."

aws ssm put-parameter --region $AWS_REGION --name " /gitmate-ai/LLM_TYPE" --value $LLM_TYPE --type "String" \
    --description "LLM Type # 1: Ollama, # 2: AWS Bedrock Claude Haiku, # 3: GPT" > /dev/null 2>&1
echo " /gitmate-ai/LLM_TYPE created."

aws ssm put-parameter --region $AWS_REGION --name " /gitmate-ai/LLM_MODEL_ID" --value $LLM_MODEL_ID \
    --type "String" \
    --description "LLM Model ID # AWS: anthropic.claude-3-haiku-20240307-v1:0 # GPT: gpt-5-nano" > /dev/null 2>&1
echo " /gitmate-ai/LLM_MODEL_ID created."

aws ssm put-parameter --region $AWS_REGION --name " /gitmate-ai/AWS_REGION" --value $AWS_BEDROCK_REGION \
    --type "String" \
    --description "AWS Region for Bedrock LLM #Example regions: us-east-1, us-west-2, eu-west-1, ap-south-1" > /dev/null 2>&1
echo " /gitmate-ai/AWS_REGION created."

aws ssm put-parameter --region $AWS_REGION --name " /gitmate-ai/BASE_URL" --value $OLLAMA_BASE_URL \
    --type "String" \
    --description "Ollama base URL #local use: http://localhost:11434 #For docker: http://host.docker.internal:11434 http://host.docker.internal:11434" > /dev/null 2>&1
echo " /gitmate-ai/BASE_URL created."

aws ssm put-parameter --region $AWS_REGION --name " /gitmate-ai/HISTORY_PATH" --value $HISTORY_PATH \
    --type "String" --description "Path to save conversation history" > /dev/null 2>&1
echo " /gitmate-ai/HISTORY_PATH created."

aws ssm put-parameter --region $AWS_REGION --name " /gitmate-ai/LOG_PATH" --value $LOG_PATH \
    --type "String" --description "Path to save logs"> /dev/null 2>&1
echo " /gitmate-ai/LOG_PATH created."

aws ssm put-parameter --region $AWS_REGION --name " /gitmate-ai/DEBUG_LOG" --value $DEBUG_LOG \
    --type "String" --description "Toggle log generation 1:enable 0:disable" > /dev/null 2>&1
echo " /gitmate-ai/DEBUG_LOG created."

aws ssm put-parameter --region $AWS_REGION --name " /gitmate-ai/WRITE_LANGCHAIN_MSGS" --value $WRITE_LANGCHAIN_MSGS \
    --type "String" --description "Toggle LLM message conversation generation 1:enable 0:disable" > /dev/null 2>&1
echo " /gitmate-ai/WRITE_LANGCHAIN_MSGS created."

aws ssm put-parameter --region $AWS_REGION --name " /gitmate-ai/LANGCHAIN_TRACING_V2" --value $LANGCHAIN_TRACING_V2 \
    --type "String" --description "langsmith env variables" > /dev/null 2>&1
echo " /gitmate-ai/LANGCHAIN_TRACING_V2 created."

aws ssm put-parameter --region $AWS_REGION --name " /gitmate-ai/LANGCHAIN_API_KEY" --value $LANGCHAIN_API_KEY \
    --type "String" --description "langsmith env variables"> /dev/null 2>&1
echo " /gitmate-ai/LANGCHAIN_API_KEY created."

aws ssm put-parameter --region $AWS_REGION --name " /gitmate-ai/LANGCHAIN_PROJECT" --value $LANGCHAIN_PROJECT \
    --type "String" --description "langsmith env variables" > /dev/null 2>&1
echo " /gitmate-ai/LANGCHAIN_PROJECT created."

aws ssm put-parameter --region $AWS_REGION --name " /gitmate-ai/LANGCHAIN_ENDPOINT" \
    --value $LANGCHAIN_ENDPOINT --type "String" --description "langsmith env variables" > /dev/null 2>&1
echo " /gitmate-ai/LANGCHAIN_ENDPOINT created."

echo "✅ Creating all the env parameters completed."
######## Creating parameters in parameter store END ##########

echo "Deploying CloudFormation stack..."

#CloudFormation deploy command
aws cloudformation deploy \
--stack-name gitmate-ai \
--region $AWS_REGION \
--template-file gitmateai_deploy.yaml \
--parameter-overrides \
VPCCidr=$VPC_CIDR \
Subnet1Cidr=$SUBNET1_CIDR \
Subnet2Cidr=$SUBNET2_CIDR \
Subnet1AZ=$SUBNET1_AZ \
Subnet2AZ=$SUBNET2_AZ \
InstanceType=$INSTANCE_TYPE \
InstanceAMI=$INSTANCE_AMI \
Keypair=$KEY_PAIR \
InstanceIAMProfile=$EC2_IAM_PROFILE \
ECRRepositoryURL=$ECR_REPO_URI \
AWSRegion=$AWS_REGION 





