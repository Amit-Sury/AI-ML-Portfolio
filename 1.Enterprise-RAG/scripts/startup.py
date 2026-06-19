import os
import boto3
from aws_utilities import get_opensearch_client
from aws_utilities import AwsCredentials, get_tempSession_assumeRole
from init_llm import init_llm
from graph import create_graph
from create_index import create_index
from guardrails_classes import ClaimsStatus
from cache import Cache, CacheType, RedisCache, LocalCache
import logging
logger = logging.getLogger(__name__)

########## Function definition BEGIN ##########

## startup resource creation, initializes opensearch serverless db client, graph, llms
def startup():
    
    db_client = None
    llm = None
    app = None
    judge_llm = None

    '''
    aws_creds = AwsCredentials(
        access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name=os.environ["AWS_REGION_NAME"]
    )
    '''
    

    #create aws session
    #assumed_session = get_tempSession_assumeRole(aws_creds)
    assumed_session = boto3.Session()
    logger.info("✅boto3.Session created")

    
    #get vector db client
    logger.info("Creating Opensearch serverless client...")
    db_client = get_opensearch_client(assumed_session, os.environ["VECTOR_DB_HOSTNAME"].replace("https://", ""))
    logger.info("Opensearch serverless client created.")

    #create index
    create_index(db_client)

    #get llm
    llm = init_llm(assumed_session, os.getenv("LLM_MODEL_ID", "openai.gpt-oss-120b-1:0"))

    #create graph
    logger.info("Creating langgraph graph...")
    app = create_graph(llm)
    logger.info("Creating langgraph graph completed.")
    
    #initialize llm_as_judge
    if (int(os.getenv("ENABLE_GUARDRAILS", "0")) > 0):
        logger.info("Guardrails are enabled")
        judge_llm = init_llm(assumed_session, os.getenv("LLM_AS_JUDGE_MODEL_ID", "qwen.qwen3-32b-v1:0"))
        judge_llm = judge_llm.with_structured_output(ClaimsStatus)
        logger.info("LLM_AS_JUDGE initialized.")

    bedrock_client = assumed_session.client("bedrock-runtime")

    # initialize cache
    cache_type = CacheType(os.getenv("CACHE_TYPE", "0"))
    
    if cache_type == CacheType.REDIS:
        logger.info("Redis cache is enabled, initializing cache...")
        host = os.environ["REDIS_HOST"]
        port = int(os.getenv("REDIS_PORT", "6379")) 
        cache: Cache = RedisCache(host, port)
        logger.info("Redis initialized.")
        
    elif cache_type == CacheType.LOCAL:
        cache: Cache = LocalCache()
        logger.info("Local cache initialized.")
    else: 
        cache = None
        logger.info("Cache is disabled")

    return bedrock_client, db_client, app, judge_llm, cache
########## END ##########
