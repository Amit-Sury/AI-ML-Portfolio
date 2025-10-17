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
    if llmtype < 3: #Use ollama llm
        try:
            LOG("Initializing Ollama LLM")
            if llmtype == 1:
                model_id = 'hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF'
            else:
                model_id = 'hf.co/bartowski/Llama-3.2-3B-Instruct-GGUF:Q4_K_M'                                
            llm = ChatOllama(model = model_id).bind_tools(tools=tools) 
            llm.invoke("hi")
            LOG(f"✅Ollama LLM {model_id} initialization Succeeded!")
            return llm
        except Exception as e:
            LOG(f"❌ Ollama error: {e}")
            LOG("Make sure Ollama is running: `ollama serve`")
            LOG("And you have the model: `ollama pull llama2`")
            exit(1)

    elif llmtype == 3: #Use AWS bedrock llm
        try: 
            LOG("Initializing AWS Bedrock LLM...")
            model_id = "anthropic.claude-3-haiku-20240307-v1:0"
            bedrock_agent = boto3.client("bedrock-runtime", region_name ="us-east-1")
            llm_create = ChatBedrockConverse(
                model=model_id,
                temperature=0,
                max_tokens=None,
                client=bedrock_agent,
            )
            llm = llm_create.bind_tools(tools=tools)
            LOG("✅AWS Bedrock LLM Initialization Succeeded!")
            return llm
        
        except Exception as e:
            print(f"❌ AWS Bedrock error: {e}")
            print("Make sure AWS related env configuration are set")
            print("And you have the access to bedrock model")
            exit(1)   

    elif llmtype == 4: #Use OpenAI
        try: 
            LOG("Initializing OpenAI GPT gpt-5-nano model...")
            model_id = "gpt-5-nano"
            llm = ChatOpenAI(model=model_id, temperature=0).bind_tools(tools=tools)
            #llm = llm_create.bind_tools(tools=tools)
            LOG("✅ gpt-5-nano model Initialization Succeeded!")
            return llm
        
        except Exception as e:
            print(f"❌ OpenAI LLM error: {e}")            
            exit(1)

    else:
        LOG("Invalid choice!")        
        exit(1)     
######################## END  ###################################