####################### Import Packages #########################
#AWS 
import boto3 

#Langchain LLMs 
from langchain_aws import ChatBedrockConverse
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from langchain_core import tools

#OS
import os

#my packages
from tools import LOG
######################## END  ##################################

####################### Init LLM BEGIN #########################
def get_llm(tools):
    
    llmtype = int(os.environ["LLM_TYPE"])
    model_id = os.environ["LLM_MODEL_ID"]
    base_url = os.environ["BASE_URL"]
    aws_region = os.environ["AWS_REGION"]

    if not (1 <= llmtype <= 3):
        LOG("❌Invalid LLM_TYPE in .env, it must be 1-3")
        return -1
    
    if not model_id.strip(): 
        LOG("❌LLM_MODEL_ID is not found .env.")
        return -1

    LOG(f"LLM type={llmtype}, model_id={model_id}")

    if llmtype == 1: #Use ollama llm
        try:
            LOG("Initializing Ollama LLM...")
            if not base_url.strip(): 
                LOG("❌BASE_URL for Ollama not found in .env file")
                LOG("💡For direct script use: http://localhost:11434")
                LOG("💡For docker use: http://host.docker.internal:11434")                
                return -1
            llm = ChatOllama(model = model_id, base_url=base_url).bind_tools(tools=tools) 
            llm.invoke("hi")
            LOG(f"✅Ollama LLM {model_id} initialization Succeeded!")
            return llm
        except Exception as e:
            LOG(f"❌ Ollama error: {e}")
            LOG("Make sure Ollama is running: `ollama serve`")
            LOG("And the model is downloaded")
            return -1

    elif llmtype == 2: #Use AWS bedrock llm
        try:
            if not aws_region.strip(): 
                LOG("❌AWS_REGION is not found in .env file")                
                return -1 
            LOG(f"Initializing AWS Bedrock LLM for region {aws_region}...")
            bedrock_agent = boto3.client("bedrock-runtime", region_name = aws_region)
            llm_create = ChatBedrockConverse(
                model=model_id,
                temperature=0,
                max_tokens=None,
                client=bedrock_agent,
            )
            llm = llm_create.bind_tools(tools=tools)
            llm.invoke("hi")
            LOG("✅AWS Bedrock LLM Initialization Succeeded!")
            return llm
        
        except Exception as e:
            LOG(f"❌ AWS Bedrock error: {e}")
            LOG("Make sure AWS related env configuration are set")
            LOG("And you have the access to bedrock model")
            return -1   

    elif llmtype == 3: #Use OpenAI
        try: 
            LOG("Initializing OpenAI model...")
            llm = ChatOpenAI(model=model_id, temperature=0).bind_tools(tools=tools)
            llm.invoke("hi")
            LOG("✅ GPT model Initialization Succeeded!")
            return llm
        
        except Exception as e:
            LOG(f"❌ OpenAI LLM error: {e}")
            LOG(f"Make sure you've access to OpenAI LLM and access_key is configured in .env")            
            return -1

      
######################## END  ###################################