import json
import os
import logging
logger = logging.getLogger(__name__)

#Generate embeddings
def generate_embedding(assumed_session, chunk):
    
    # Create Bedrock Runtime client
    logger.info("ℹ️ Creating bedrock client...")
    bedrock = assumed_session.client("bedrock-runtime")

    # Titan Embeddings V2 request body
    request_body = {
        "inputText": chunk, 
        "dimensions": 512
        }
    
    # Invoke Titan embedding model
    logger.info("ℹ️ Generating query embedding by using bedrock model.")

    response = bedrock.invoke_model(
            modelId=os.getenv("EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0"),
            body=json.dumps(request_body),
            contentType="application/json",
            accept="application/json"
            )
        
    # Read response
    response_body = json.loads(response["body"].read())

    embedding = response_body["embedding"]
    logger.info("✅ Query embedding generated successfully.")
    return embedding
###### END #####