#langgraph
from langchain_core.messages import AIMessage, HumanMessage

#my tools
from tools import LOG, loadenvfile, get_github_tools
from tools import get_youtubesearch, AddCmtOnIssue, GetPRFlsOverview, GetDrctryFlsCnt
from tools import GetAllOpenPR, GetPRDetail, PRFlsContent, GetFlsfromDirectory
from tools import ListPRAuthors, ListPRComments
from graph import get_llm, create_graph


#os, json for file handling
import os
import json


########### Helper functions BEGIN #################
#init .env, llm and graph
def initialize_app(st, user_id):
    """This function initialize .env, llm and graph"""

    if "app" not in st.session_state:
    
        #load env file
        if loadenvfile(user_id) == -1:
            LOG("❌Error loading .env file.")
            return -1
        
        
        LOG("✅Loading .env file is successfully completed")   
        #Get tools
        github_tools_list = get_github_tools()

        if github_tools_list == None:
            LOG("❌Getting langgraph github tools failed.")
            return -1
        
        LOG("Initializing all the tools...")
        tool_list = [
            *github_tools_list, #using * to unpack github tools returned by function
            AddCmtOnIssue, 
            get_youtubesearch(), 
            GetAllOpenPR,
            GetPRDetail,
            GetPRFlsOverview,
            PRFlsContent,
            ListPRAuthors,
            ListPRComments,
            GetFlsfromDirectory,
            GetDrctryFlsCnt
        ] 
        LOG("✅Tools initialization completed.")

        #Initialize llm
        LOG("Initializing LLM...")
        llm = get_llm(tool_list)
        if llm == -1:
            LOG("❌Initializing LLM failed.")
            return -1
        

        #create graph
        st.session_state["app"] = create_graph(llm, tool_list)

        #create chat and conversation history for llm, streamlit
        st.session_state["messages"] = []  #create conversation history for streamlit
        st.session_state["conversation_history"] = [] #create conversation history for LLM
        #Load history
        LOG("Loading conversation history...")
        st.session_state["conversation_history"], st.session_state["messages"]  = read_conversation(user_id)
        
        return 1
    
#write conversation to file
def write_convo(llm_conversation, user_id):
    """This function write streamlit and llm conversation into json file"""
    
    path = os.environ["HISTORY_PATH"]   

    filepath = os.path.join(path, f"chat_history_{user_id}.json")
    LOG(f"Writing conversation history to file: {filepath}")
    # Save llm conversation to JSON
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    "type": "user" if isinstance(msg, HumanMessage) else "assistant",
                    "content": msg.content,
                    "additional_kwargs": msg.additional_kwargs, #Currently code is not storing this in session
                    "response_metadata": msg.response_metadata, #Currently code is not storing this in session
                }
                for msg in llm_conversation
            ],
            f,
            indent=2,
            ensure_ascii=False
        )  
    LOG("Writing conversation history completed")          


#read conversation from file
def read_conversation(user_id):
    
    path = os.environ["HISTORY_PATH"]
    filepath = os.path.join(path, f"chat_history_{user_id}.json")
    
    llm_conversation = [] 
    streamlit_history = []
    
    # Load back from JSON
    if os.path.exists(filepath):
        LOG(f"Reading conversation history from {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        #loading conversation for llm
        llm_conversation = [        
            HumanMessage(
                content=item["content"],
                additional_kwargs=item["additional_kwargs"],
                response_metadata=item["response_metadata"]
            )
            if item["type"] == "user"
            else AIMessage(
                content=item["content"],
                additional_kwargs=item["additional_kwargs"],
                response_metadata=item["response_metadata"]
            )
            for item in data
        ]

        #loading conversation to display in streamlit UI
        streamlit_history = [        
            ("user", item["content"]) if item["type"] == "user" else ("assistant", item["content"])
            for item in data
        ]
        LOG(f"Reading conversation history completed")
    else:
        LOG(f"No previous conversation history found")


    return llm_conversation, streamlit_history

################### Helper functions END  ##################