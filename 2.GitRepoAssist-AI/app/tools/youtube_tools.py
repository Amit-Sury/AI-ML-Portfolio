################### Import packages BEGIN #######################

#langchain youtube search
from langchain_community.tools import YouTubeSearchTool

#my package
from tools import LOG

######################## END  ###################################


############## Get youtube search tool BEGIN ####################

def get_youtubesearch():

    LOG("Initializing Youtube Search tool...")
    tool = YouTubeSearchTool() 
    LOG("✅ Youtube Search tool Initialized.")
    
    return tool 

######################## END  ###################################