####################### Import Packages #########################
#Langchain LLMs 
from langchain_aws import ChatBedrockConverse
import logging

logger = logging.getLogger(__name__)
######################## END  ##################################

####################### Init LLM BEGIN #########################
def init_llm(assumed_session, model_id):
    
    logger.info(f"Initializing LLM {model_id}")

    try:
        bedrock_agent = assumed_session.client(
            "bedrock-runtime",
            region_name = assumed_session.region_name
        )
        
        llm = ChatBedrockConverse(
            model=model_id,
            temperature=0,
            max_tokens=None,
            client=bedrock_agent,
        )
        
        llm.invoke("hi")
        logger.info("Creating LLM succeeded")
        return llm
    
    except Exception as e:
        logger.error(f"Error creating llm: {e}")
        raise   
      
######################## END  ###################################