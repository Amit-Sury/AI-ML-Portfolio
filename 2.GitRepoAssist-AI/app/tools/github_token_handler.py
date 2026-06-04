#import pygithub packages
from github import Github, GithubIntegration

#import time and os
from time import time
import os

#my log package
from tools import LOG

class GitTokenHandler:
    """This is singleton class to hold github access token.
    Pass Github appid & private key to get the access token
    """
    _instance = None 

    #Although we're passing required parameters but we'll initialize token in __init__ function
    #we could have done it here also but for clear understanding we'll initialize token in init
    #using __new__ only for memory allocation
    def __new__(cls, app_id, private_key): 
        if cls._instance is None: 
            cls._instance = super().__new__(cls) 
            cls._instance.initialize = False            
        return cls._instance
    
    #this will get called automatically after __new__
    def __init__(self, app_id, private_key):

        if not self.initialize:
            LOG("Creating new access token...")
            self.app_id = app_id
            self.privatekey = private_key
            
            integration =   GithubIntegration(self.app_id, self.privatekey)
            LOG("Getting integration is successful")

            # List installations
            installations = integration.get_installations()
            LOG("Getting installations is successful")
            for inst in installations:
                LOG(f"Installation Id:{inst.id}, Account: {inst.account.login}")
            
            #get one installation id
            inst_id = installations[0].id

            #get installation access token
            self.access_token = integration.get_access_token(installation_id=inst_id).token
            self.creation_time = time()
            LOG("Access token created successfully")
            self.initialize = True


    def get_token(self):
        
        LOG(f"token creation time:{self.creation_time}, current time:{time()}")

        if ((time() - self.creation_time) > 3000):
            
            LOG("Access token is expired, refreshing token")

            integration =   GithubIntegration(self.app_id, self.privatekey)
            LOG("Getting integration is successful")

            # List installations
            installations = integration.get_installations()
            LOG("Getting installations is successful")
            for inst in installations:
                LOG(f"Installation Id:{inst.id}, Account: {inst.account.login}")
            
            #get one installation id
            inst_id = installations[0].id

            #get installation access token
            self.access_token = integration.get_access_token(installation_id=inst_id).token
            self.creation_time = time()
            LOG(f"Refreshing token successful.")
            return self.access_token
        else:
            LOG("Access token is not expired, returning existing token")            
            return self.access_token







