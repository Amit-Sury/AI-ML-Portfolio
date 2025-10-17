################ Import packages ################################
from dotenv import load_dotenv
import os

#my packages
from tools import LOG 
######################## END  ###################################

def loadenvfile(st):
    """This function load the .env file"""

    load_dotenv(dotenv_path="D:/OneDrive/Documents/Amit/Code Repo/AI/app/.env")

    #make directories if not already exists
    os.makedirs(os.path.dirname(os.environ["HISTORY_PATH"]), exist_ok=True)
    os.makedirs(os.path.dirname(os.environ["LOG_PATH"]), exist_ok=True)
        
    LOG("Loading .env file...")
    
    #Update private key
    key_path = os.getenv("GITHUB_APP_PRIVATE_KEY")  # path from .env
    
    #streamlit rerun() causes issue if GITHUB_APP_PRIVATE_KEY is already inflated
    #and code attempts to open the key_path. Below check makes it safe
    if key_path and os.path.isfile(key_path): 
        with open(key_path, "r") as f:
            private_key = f.read()

        os.environ["GITHUB_APP_PRIVATE_KEY"] = private_key
        LOG("✅Loading .env file completed")