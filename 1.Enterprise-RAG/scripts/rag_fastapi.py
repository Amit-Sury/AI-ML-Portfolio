########## Import packages BEGIN ##########
from fastapi import FastAPI, Request, Response, HTTPException, status
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
from langchain_core.messages import HumanMessage, AIMessage
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

##### Fastapi handling BEGIN ##########

## Startup/shutdown handling ##
@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("ℹ️ Initiating FastAPI app (lifespan)")

    try:
    
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

        logger.info("✅ env configurations are ok.")

        logger.info("ℹ️ creating system resources...")
        assumed_session, db_client, graph, judge_llm = startup()
        logger.info("✅ system resources are created successfully.")

        app.state.config = {
            "cognito_domain_uri": cognito_domain_uri,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "assumed_session": assumed_session,
            "db_client": db_client,
            "graph": graph,
            "judge_llm": judge_llm,
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
            "redirect_uri": request.app.state.config['redirect_uri'],
            "code": code            
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        logger.info("post URL generated with following parameters...")
        logger.info(f"token_url={token_url}")
        logger.info(f"headers={headers}")

        logger.info("post request sent, waiting for response...")
        response = await client.post(token_url, data=data, headers=headers)
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
async def home(request: Request):

    logger.info(f"Root endpoint (GET /) invoked...")

    code = request.query_params.get("code")

    # No code present means User is unauthenticated. Redirect to Cognito.
    if not code:
       
       logger.info("Code not found in the request, redirecting to cognito for login")
       
       logger.info(f"Client id={request.app.state.config['client_id']}")
       logger.info(f"redirect_uri={request.app.state.config['redirect_uri']}")
       logger.info(f"cognito_domain_uri={request.app.state.config['cognito_domain_uri']}")

       params = urlencode({
           "client_id": request.app.state.config['client_id'],
           "response_type": "code",
           "redirect_uri": request.app.state.config['redirect_uri'],
        })
       
       login_url = f"{request.app.state.config['cognito_domain_uri']}/login?{params}"
       logger.info(f"Cognito URL={login_url}")
       
       return RedirectResponse(login_url)

    # When Code is present, means User is logged in. Obtaining JWT
    logger.info("Code is present in the request, user is logged in. Obtaining Jwt")
    access_token, id_token = await obtain_jwt(code, request)

    # getting user profile data from id_token
    decoded_id_token = jwt.decode(id_token, options={"verify_signature": False})
    
    cognito_username = decoded_id_token.get("cognito:username")
    user_email = decoded_id_token.get("email")
    #logger.info(f"User has logged in user is: {cognito_username} with email: {user_email}")
    logger.info(f"User has logged in successfully")

    # creating session
    session_id = access_token
    if session_id not in conversation_store:
        conversation_store[session_id] = []

    #getting the layout
    html_content = ui_login(user_email)

    response = HTMLResponse(content=html_content)

    # Storing the token in a secure HTTP-only cookie here so subsequent API Gateway calls
    # from the browser can automatically attach it. Using cookies instead of the Authorization
    # header completely eliminates Cross-Site Scripting (XSS) risks. To handle Cross-Site Request
    # Forgery (CSRF) vulnerabilities, adding samesite="strict"
	#https://stackoverflow.com/questions/27067251/where-to-store-jwt-in-browser-how-to-protect-against-csrf
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        #secure=False,
        samesite="strict"
    )

    return response
## end ##

# userquery endpoint
@app.post("/userquery")
async def user_query(query: UserQuery, request: Request):

    user_prompt = query.text
    
    logger.info(f"'/userquery' (POST /userquery) endpoint invoked.")
    logger.info("ℹ️ Received user query. Creating retrieval service...")
    logger.info(f"Cookies received:::: {request.cookies}")

    #getting optional headers, api gateway adds these
    #user_email = request.headers.get("X-Cognito-Email")
    #user_roles = request.headers.get("X-Cognito-Groups")
    access_token = request.cookies.get("access_token")
    user_id = request.headers.get("X-Cognito-Sub")
    
    # checking user_id received in header ensures that request actually came through API Gateway
    # if not present then redirecting to access-denied page with logout and asks for login
    if not user_id:
        logger.error("User_id is not present, the request directly landed to app instead of via apigateway.")
        logger.error("Redirecting to access denied page")
        return RedirectResponse(
            url="/access-denied?reason=invalid_accesspoint",
            status_code=302
        )

    #create retrieval service    
    db_client = request.app.state.config['db_client']
    graph = request.app.state.config['graph']
    judge_llm = request.app.state.config['judge_llm']
    assumed_session = request.app.state.config['assumed_session']

    # session conversation handling
    session_id = access_token
    if session_id not in conversation_store:
        conversation_store[session_id] = []

    conversation_store[session_id].append(HumanMessage(content=user_prompt))

    service = RetrievalService(db_client, graph, judge_llm)
    logger.info("ℹ️ Retrieval service created. Executing the service...")
    response = service.retrieve(assumed_session, user_prompt)
    logger.info("ℹ️ Execution of Retrieval service completed. Returning the response to user")

    conversation_store[session_id].append(AIMessage(content=response["answer"]))
    
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
async def logged_out_page():

    logger.info(f"'/logged-out' (GET /logged-out) endpoint invoked.")

    html_content = ui_logout()

    logger.info(f"User has successfully logged out.")
    logger.info(f"Returing logout response to the user.")
    return HTMLResponse(content=html_content)

# access-denied endpoint
@app.get("/access-denied")
async def access_denied(request: Request):

    reason = request.query_params.get("reason")

    logger.info(f"'/access-denied' (GET /access-denied) endpoint invoked.")
    logger.info("handling access-denied process...")

    html_content = ui_access_denied(reason)

    logger.info(f"User will be auto redirect to logout page.")
    return HTMLResponse(content=html_content)
    

    

#### Main BEGIN  ####
if __name__ == "__main__":

    uvicorn.run(
        "rag_fastapi:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
#### END ####
