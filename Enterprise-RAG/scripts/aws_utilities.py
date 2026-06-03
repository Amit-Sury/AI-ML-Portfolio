#import packages
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from dataclasses import dataclass
import os
import logging
logger = logging.getLogger(__name__)
########## Class definitions #################

#used to set aws credentials
@dataclass
class AwsCredentials:
    access_key_id: str
    secret_access_key: str
    region_name: str

@dataclass
class VectorDBInfo:
    os_host: str
    index_name: str
    
############### END ##########################

############ Function Definitions BEGIN ########################

#Get temporary session using sts temporary credentials by assuming a role
def get_tempSession_assumeRole(awsCreds: AwsCredentials):
    # Step 1: estabilishing base session by passing enterprise-rag-user IAM user credentials.  
    base_session = boto3.Session(
        aws_access_key_id=awsCreds.access_key_id,
        aws_secret_access_key=awsCreds.secret_access_key,
        region_name=awsCreds.region_name
    )

    #sts client
    sts_client = base_session.client("sts")

    # Step 2: Assume target role 
    response = sts_client.assume_role(
        RoleArn=os.environ["ROLE_ARN"],
        RoleSessionName="local-test-session"
    )

    creds = response["Credentials"]

    # Step 3: Create new session using temporary credentials 
    # for creating session from assumed role all 3 temporary creds are required
    # accesskey+secretkey+sessiontoken  
    assumed_session = boto3.Session(
        aws_access_key_id=creds["AccessKeyId"],         #temporary accesskey of assumed role issued by sts
        aws_secret_access_key=creds["SecretAccessKey"], #temporary secretkey of assumed role issued by sts
        aws_session_token=creds["SessionToken"],        #temporary SessionToken of assumed role issued by sts
        region_name=awsCreds.region_name
    )

    return assumed_session

#create opensearch client
def get_opensearch_client(assumed_session, os_host):
    
    service = "aoss" #service name for serverless opensearch collections
    
    # OpenSearch data APIs are HTTP REST calls (sends raw HTTP requests) 
    # Unlike boto3 clients, opensearch-py sends HTTP requests directly so
    # signing must be added explicitly. For that we use AWS4Auth package
    # AWS4Auth signs the HTTP request using SigV4 signature as proof. 
    # AWS4Auth applies SigV4 signing to those HTTP requests using your 
    # AWS credentials (including STS temporary creds).

    credentials = assumed_session.get_credentials() #get credentials from temporary assumed session
    
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        assumed_session.region_name,
        service,
        session_token=credentials.token
    )

    # -------- CREATE OPENSEARCH CLIENT --------
    client = OpenSearch(
        hosts=[{"host": os_host, "port": 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )

    return client
########### END #############




