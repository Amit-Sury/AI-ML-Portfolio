########## Import packages BEGIN ##########
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import httpx
import jwt
from urllib.parse import urlencode
from pydantic import BaseModel
import uvicorn
from contextlib import asynccontextmanager
from startup import startup
from retrieval_service import RetrievalService
from ui_layout import ui_login, ui_logout, ui_access_denied
from dotenv import load_dotenv
import os
import logging
########## Import packages END ##########

## logger initialization
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s",
    force=True
)
logger = logging.getLogger(__name__)
## end ##

## load .env file
load_dotenv()

## conversation_store
conversation_store = {}
## end ##

#### Class Definition ####
# Request model, used for fastapi
class UserQuery(BaseModel):
    text: str
#### END ####

## check env params
def check_env():

    logger.info("ℹ️ Checking required env configurations...")

    ## check vector db hostname
    VECTOR_DB_HOSTNAME = os.getenv("VECTOR_DB_HOSTNAME")
    if not VECTOR_DB_HOSTNAME:
        raise RuntimeError("VECTOR_DB_HOSTNAME is not configured")
    
    ## check cognito related parameters
    cognito_domain_uri = os.getenv("COGNITO_DOMAIN_URI")
    if not cognito_domain_uri:
        raise RuntimeError("COGNITO_DOMAIN_URI is not configured")
    
    client_id = os.getenv("CLIENT_ID")
    if not client_id:
        raise RuntimeError("CLIENT_ID is not configured")
    
    client_secret = os.getenv("CLIENT_SECRET")
    if not client_secret:
        raise RuntimeError("CLIENT_SECRET is not configured")
    
    redirect_uri = os.getenv("REDIRECT_URI")
    if not redirect_uri:
        raise RuntimeError("REDIRECT_URI is not configured")
    
    if int(os.getenv("ENABLE_GUARDRAILS","0")):
        
        guardrail_id = os.getenv("AWS_GUARDRAIL_ID")
        if not guardrail_id:
            raise RuntimeError("AWS_GUARDRAIL_ID is not configured")

        guardrail_version = os.getenv("AWS_GUARDRAIL_VERSION")
        if not guardrail_version:
            raise RuntimeError("AWS_GUARDRAIL_VERSION is not configured")
    
    if int(os.getenv("CACHE_TYPE","0")) == 1:
        
        redis_host = os.getenv("REDIS_HOST")
        if not redis_host:
            raise RuntimeError("REDIS_HOST is not configured")

        redis_port = os.getenv("REDIS_PORT")
        if not redis_port:
            raise RuntimeError("REDIS_PORT is not configured")

    logger.info("✅ env configurations are ok.")
    return cognito_domain_uri, client_id, client_secret, redirect_uri

## end ##

##### Fastapi handling BEGIN ##########

## Startup/shutdown handling ##
@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("ℹ️ Initiating FastAPI app (lifespan)")

    try:

        #check env configurations
        (
            cognito_domain_uri,
            client_id,
            client_secret,
            redirect_uri,
        ) = check_env()
    
        # create system resources
        logger.info("ℹ️ creating system resources...")
        (
            bedrock_client,
            db_client,
            graph,
            judge_llm,
            cache,
        ) = startup()

        logger.info("✅ system resources are created successfully.")

        app.state.config = {
            "cognito_domain_uri": cognito_domain_uri,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "bedrock_client": bedrock_client,
            "db_client": db_client,
            "graph": graph,
            "judge_llm": judge_llm,
            "cache": cache,
        }

        logger.info("✅ Application startup successful")

        yield

    except Exception as e:
        logger.exception("❌Application startup failed")
        # App will terminate
        raise RuntimeError("⛔ Critical startup failure")

    finally:
        logger.info("🛑 Shutting down resources...")
## end ##

#Since aws API Gateway appends a stage prefix (e.g., /production) to URL string
#need to adjust the root path to ensure fast api serves api like /production/userquery
app = FastAPI(lifespan=lifespan, root_path=os.getenv("API_ROOT_PATH", ""))

## obtain jwt from cognito by exchanging it with "code" received from cognito 
async def obtain_jwt(
        code: str,
        request: Request
    ):

    logger.info("generarting post request to obtain jwt")
    async with httpx.AsyncClient() as client:
        
        token_url = f"{request.app.state.config['cognito_domain_uri']}/oauth2/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": request.app.state.config['client_id'],
            "client_secret": request.app.state.config['client_secret'],
            "redirect_uri": f"{request.app.state.config['redirect_uri']}/",
            "code": code            
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        logger.info("post URL generated with following parameters...")
        logger.info(f"token_url={token_url}")
        logger.info(f"headers={headers}")

        logger.info("post request sent, waiting for response...")
        response = await client.post(token_url, data=data, headers=headers)

        if response.status_code != 200:
            logger.error(
                "Cognito token exchange failed: %s",
                response.text
            )
            raise Exception("Authentication failed")
        else:
            tokens = response.json()        
        
    # Extract the JWTs
    logger.info("response received from cognito, extracting jwt...")

    access_token = tokens.get("access_token")
    id_token = tokens.get("id_token")
    
    logger.info("✅ jwt succcessfuly obtained.")

    return access_token, id_token
## end ## 

# root endpoint (/)
@app.get("/", response_class=HTMLResponse)
async def login(request: Request):

    
    logger.info(f"Root endpoint (GET /) invoked...")   
    
    code = request.query_params.get("code")

    # No code present means User is unauthenticated. Redirect to Cognito.
    if not code:
       
       logger.info("Code not found in the request, redirecting to cognito for login")       
       
       params = urlencode({
           "client_id": request.app.state.config['client_id'],
           "response_type": "code",
           "redirect_uri": f"{request.app.state.config['redirect_uri']}/",
        })
       
       login_url = f"{request.app.state.config['cognito_domain_uri']}/login?{params}"
       logger.info(f"Cognito URL={login_url}")
       
       return RedirectResponse(login_url)

    # When Code is present, means User is logged in. Obtaining JWT
    logger.info("Code is present in the request, user is logged in. Obtaining Jwt")
    try:
        access_token, id_token = await obtain_jwt(code, request)
    
    except Exception:
        ##code validation is failed
        logger.error("Redirecting to access denied page")
        return RedirectResponse(
            url=f"{request.app.state.config['redirect_uri']}/access-denied?reason=invalid_session",
            status_code=302
        )

    logger.info(f"User has logged in successfully")
    
    response = RedirectResponse(
        url=f"{request.app.state.config['redirect_uri']}/home",
        status_code=302
    )

    #set the cookies, using secure HTTP-only cookie here so subsequent API Gateway calls
    #from the browser can automatically attach it. Using cookies instead of the Authorization
    # header completely eliminates Cross-Site Scripting (XSS) risks. To handle Cross-Site Request
    # Forgery (CSRF) vulnerabilities, adding samesite="strict"
	#https://stackoverflow.com/questions/27067251/where-to-store-jwt-in-browser-how-to-protect-against-csrf
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        #secure=False,
        samesite="lax",
        path="/"
    )

    response.set_cookie(
        key="id_token",
        value=id_token,
        httponly=True,
        secure=True,
        #secure=False,
        samesite="lax",
        path="/"
    )

    return response    
## end ##

# home endpoint (/)
@app.get("/home", response_class=HTMLResponse)
async def home(request: Request):

    
    logger.info(f"Home endpoint (GET /home) invoked...")   
    
    #check if token is present
    access_token = None
    access_token = request.cookies.get("access_token")

    #if token present then user has logged in
    if access_token:
        logger.info("access_token is present")
        # getting user profile data from id_token
        id_token = request.cookies.get("id_token")
        decoded_id_token = jwt.decode(id_token, options={"verify_signature": False})
        user_email = decoded_id_token.get("email")
    
        #getting the layout
        html_content = ui_login(user_email,request.app.state.config['redirect_uri'])
        response = HTMLResponse(content=html_content)
        return response
    else:
        logger.error("access_token is not present, user is not loggedin")
        logger.error("Redirecting to access denied page")
        return RedirectResponse(
            url=f"{request.app.state.config['redirect_uri']}/access-denied?reason=invalid-login-state",
            status_code=302
        )

# userquery endpoint
@app.post("/userquery")
async def user_query(query: UserQuery, request: Request):

    logger.info(f"'/userquery' (POST /userquery) endpoint invoked.")
    user_prompt = query.text
    
    logger.info("ℹ️ Received user query. Creating retrieval service...")
    
    #getting optional headers, api gateway adds these
    x_user_id = request.headers.get("X-User-Id")
    x_username = request.headers.get("X-Username")

    logger.info(f"from X-User-Id header={x_user_id}")
    logger.info(f"from X-Username header={x_username}")
    
    # checking user_id received in header ensures that request actually came through API Gateway
    # if not present then redirecting to access-denied page with logout and asks for login
    if not x_user_id:
        logger.error("User_id is not present, the request directly landed to app instead of via apigateway.")
        logger.error("Redirecting to access denied page")
        return RedirectResponse(
            url=f"{request.app.state.config['redirect_uri']}/access-denied?reason=unauthorized-access",
            status_code=302
        )

    #create retrieval service    
    db_client = request.app.state.config['db_client']
    graph = request.app.state.config['graph']
    judge_llm = request.app.state.config['judge_llm']
    bedrock_client = request.app.state.config['bedrock_client']
    cache = request.app.state.config['cache']

    # session conversation handling
    session_id = x_user_id
    if session_id not in conversation_store:
        conversation_store[session_id] = []

    service = RetrievalService(db_client, graph, judge_llm, cache)
    logger.info("ℹ️ Retrieval service created. Executing the service...")
    response = service.retrieve(bedrock_client, user_prompt, conversation_store[session_id])
    logger.info("ℹ️ Execution of Retrieval service completed. Returning the response to user")

    
    
    return response
## end ##

# logout endpoint
@app.get("/logout")
async def logout(request: Request):
    
    logger.info(f"'/logout' (GET /logout) endpoint invoked.")
    logger.info("starting logout process...")

    params = urlencode({
           "client_id": request.app.state.config['client_id'],
           "logout_uri": f"{request.app.state.config['redirect_uri']}/logged-out"
        })
       
    cognito_logout_url = f"{request.app.state.config['cognito_domain_uri']}/logout?{params}"
    logger.info(f"Cognito logout URL={cognito_logout_url}")
    
    response = RedirectResponse(url=cognito_logout_url)
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")

    logger.info("Redirecting to cognito to handle logout")
    return response

# logged-out page
@app.get("/logged-out", response_class=HTMLResponse)
async def logged_out_page(request: Request):

    logger.info(f"'/logged-out' (GET /logged-out) endpoint invoked.")

    html_content = ui_logout(request.app.state.config['redirect_uri'])

    logger.info(f"User has successfully logged out.")
    logger.info(f"Returing logout response to the user.")
    return HTMLResponse(content=html_content)

# access-denied endpoint
@app.get("/access-denied")
async def access_denied(request: Request):

    reason = request.query_params.get("reason")

    logger.info(f"'/access-denied' (GET /access-denied) endpoint invoked.")
    logger.info("handling access-denied process...")

    html_content = ui_access_denied(reason, request.app.state.config['redirect_uri'])

    logger.info(f"User will be auto redirect to logout page.")
    return HTMLResponse(content=html_content)
    

    

#### Main BEGIN  ####
if __name__ == "__main__":

    uvicorn.run(
        "rag_fastapi:app",
        host="0.0.0.0",
        port=8000,
        #reload=True
        reload=False
    )
#### END ####
