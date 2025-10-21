################ Import packages ################################
from dotenv import load_dotenv
import os

#my packages
from tools import LOG 
######################## END  ###################################

def loadenvfile(user_id):
    """This function load the .env file"""

    load_dotenv()  
        
    #make directories if not already exists
    #os.makedirs(os.path.dirname(os.environ["HISTORY_PATH"]), exist_ok=True)
    #os.makedirs(os.path.dirname(os.environ["LOG_PATH"]), exist_ok=True)
    os.makedirs(os.environ["HISTORY_PATH"], exist_ok=True)
    os.makedirs(os.environ["LOG_PATH"], exist_ok=True)
    
    #initializing user_id for logs
    os.environ["user_id"] = user_id

    LOG("Log process started, required directories are set.")
    LOG(f"Log path:{os.environ["LOG_PATH"]} History path:{os.environ["HISTORY_PATH"]}")
    
    
    LOG("Reading github configurations from .env...")
    
    app_id = os.environ["GITHUB_APP_ID"]
    repo_name = os.environ["GITHUB_REPOSITORY"]
    LOG(f"AppID:{app_id}, Repo:{repo_name}")       

    #Update private key
    key_path = os.getenv("GITHUB_APP_PRIVATE_KEY")  # path from .env
        
    #streamlit rerun() causes issue if GITHUB_APP_PRIVATE_KEY is already inflated
    #and code attempts to open the key_path. Below check makes it safe
    if key_path and os.path.isfile(key_path): 
        with open(key_path, "r") as f:
            private_key = f.read()
        
        os.environ["GITHUB_APP_PRIVATE_KEY"] = private_key
        LOG("✅Reading github private key completed")
        
    
    return 1