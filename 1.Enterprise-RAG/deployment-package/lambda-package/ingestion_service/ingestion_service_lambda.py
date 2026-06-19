#import packages
from io import BytesIO      # To load s3 file content locally
import urllib.parse
import boto3
import json
import uuid
import os
from pathlib import Path
from dataclasses import dataclass
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

try: 
    import PyPDF2               # For reading PDF documents
    from docx import Document   # For reading Word documents
    from opensearchpy import OpenSearch, RequestsHttpConnection
    from requests_aws4auth import AWS4Auth    
    import_success = True
    logger.info("✅Required packages are loaded.")
except ImportError as e:
    logger.error(f"❌ FAILURE: Missing package -> {e}")
    import_success = False

########### class definition ######
@dataclass
class VectorDBInfo:
    os_host: str
    index_name: str
## end ##    

########### Ingestion service definition #################
class KnowledgeIngestionService:
    def doc_ingestion(
            self,
            bucket_name,
            object_key,
            db_info: VectorDBInfo 
        ) -> None :
        
        try:

            #get aws session
            assumed_session = boto3.Session()
            logger.info("✅boto3.Session created")
            #get vector db client
            db_client = get_opensearch_client(assumed_session, db_info.os_host)
            #read doc content
            (
                file_processed,
                doc,
                doc_id,
                filename            
            ) = read_s3_docs(
                assumed_session,
                bucket_name,
                object_key
            )
            
            if not file_processed:
                raise ValueError(f"Unsupported file: {object_key}")
            
            if doc.strip():
                #chunking
                chunks = chunk_text(doc, chunk_size = 500, overlap = 40)
                logger.info("Generating embedding and loading doc to db")
                for i, chunk in enumerate(chunks):
                    #embedding
                    emb = generate_embedding(assumed_session, chunk)
                    chunk_id = f"{doc_id}_chunk_{i}"
                    #store document
                    load_doc_to_db(
                        chunk_id,
                        chunk,
                        emb,
                        filename,
                        db_client,
                        db_info.index_name
                    )
            
            logger.info(f"✅Processing document completed. Total {i+1} documents are added to opensearch Index")

        except Exception as e:
            logger.info(f"❌Ingestion failed for {object_key}: {str(e)}")
            raise            
############### Service Definition END #############

########### Functions block BEGIN ###################

# read document from s3 bucket
def read_s3_docs(assumed_session, bucket_name, object_key):

    logger.info("Reading S3 doc")
    #get s3 client 
    s3 = assumed_session.client("s3")
    logger.info("S3 client created")    
    # Read file from S3 into memory
    doc_content = s3.get_object(Bucket=bucket_name, Key=object_key)
    file_bytes = doc_content["Body"].read()
    filename = Path(object_key).name
    filename_lower = filename.lower()
    logger.info(f"Reading contents of file={filename_lower}, file_bytes={len(file_bytes)}")

    doc_id = str(uuid.uuid4())
    text = ""
    # Pass bytes stream to fileReader
    file_processed = False
    with BytesIO(file_bytes) as f:

        # Handle PDF documents 
        if filename_lower.endswith(".pdf"):
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            file_processed = True
        # Handle word documents 
        elif filename_lower.endswith(".docx"):
            doc = Document(f)
            text = "\n".join([p.text for p in doc.paragraphs if p.text.strip() != ""])
            file_processed = True       
        else:
            file_processed = False                    

    logger.info(f"File processed={file_processed}")
    return file_processed, text, doc_id, filename
###### END #####

#chunking
def chunk_text(text, chunk_size=500, overlap=50):

    logger.info("Creating chunks...")
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks
###### END #####

#Generate embeddings
def generate_embedding(assumed_session, chunk):
    
    # Create Bedrock Runtime client
    bedrock = assumed_session.client("bedrock-runtime")

    # Titan Embeddings V2 request body
    request_body = {
        "inputText": chunk, 
        "dimensions": 512
        }
    
    # Invoke Titan embedding model
    response = bedrock.invoke_model(
        modelId=os.getenv("EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0"),
        body=json.dumps(request_body),
        contentType="application/json",
        accept="application/json"
        )
    
    # Read response
    response_body = json.loads(response["body"].read())

    embedding = response_body["embedding"]
    logger.info("Embedding generated for chunk")
    
    return embedding
###### END #####

#load docs to vector db
def load_doc_to_db(
        chunk_id,       #chunk id
        chunk,          #chunk
        emb,            #generated embedding
        filename,       #filename
        db_client,      #db client 
        index_name      #index name 
    ):

    # create document with chunk, embedding
    document = {
        "doc_id": chunk_id,
        "text": chunk,
        "source": filename,
        "embedding": emb
    }
    
    # insert document
    response = db_client.index(index=index_name,body=document)
    logger.info(f"Chunk={chunk_id} stored in db")
######### End #########

#create opensearch client
def get_opensearch_client(assumed_session, os_host):
    
    service = "aoss" #service name for serverless opensearch collections
    credentials = assumed_session.get_credentials() #get credentials from temporary assumed session
    
    region = os.environ["AWS_REGION"]

    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        region,
        service,
        session_token=credentials.token
    )

    # -------- CREATE OPENSEARCH CLIENT --------
    try:
        logger.info("Creating Opensearch session...")
        logger.info(f"Hostname={os_host}")
        client = OpenSearch(
            hosts=[{"host": os_host, "port": 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )
        logger.info("✅Opensearch client created.")
    except Exception as e:
        logger.error(f"❌ FAILURE: Creating OS client failed -> {e}")
        raise      

    return client
#### END #######

# lambda handler
def lambda_handler(event, context):
    
    if not import_success:
       raise Exception("Deployment package is missing required dependencies.")
    
    logger.info("Lambda started")
        
    # Get bucket name and file key from S3 event
    record = event["Records"][0]

    bucket_name = record["s3"]["bucket"]["name"]
    object_key = urllib.parse.unquote_plus(
        record["s3"]["object"]["key"]
    )
    logger.info(f"Bucket name: {bucket_name}, Object key: {object_key}")

    db_info = VectorDBInfo(
        os_host=os.environ["VECTOR_DB_HOSTNAME"].replace("https://", ""),
        index_name=os.getenv("INDEX_NAME", "enterprise-rag-index")
    )

    #create ingestion service
    service = KnowledgeIngestionService()
    #execute the service
    service.doc_ingestion(bucket_name, object_key, db_info)
## end ##

########### Functions block End ###################        

