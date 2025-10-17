################ Import required pacakges #######################
#langgraph packages
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

#langchain packages
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, ToolMessage, SystemMessage
from langchain_core import tools

#Annotations
from typing import Annotated, TypedDict, Sequence

#os, json
import os
import json

#my package
from tools import LOG, pretty_print_messages
####################### END  ###################################

################ Langgraph Code BEGIN ###########################

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

#Call LLM
def call_llm(state: AgentState, llm):    
    """This function call AWS LLM"""    
    
    system_prompt = """ You are an AI assistant with access to various tools. Follow these rules:
    1. For general knowledge and conversation, use your own capabilities appropriately
    2. ONLY use tools when you're asked to do something on github, youtube, or addition of numbers
    3. Use the most specific tool for the task:
    - To get overview of existing files in Main branch: use FileOverview
	- To fetch a list of the repository's issues: use GetIssues
    - To fetch a list of all files in a specified directory: Use GtflsfrmDrctry  
	- To search for code in the repository: Use SearchCode
	- To read the contents of a file in pr: use github_fileoverview_tool 	
	- To add comment on Issue: Use github_issuecomment_tool
    - To get all the open pull requests on repo: use github_allpullreqs_tool
    - To get details/summary of a specific PR: use github_detailpr_tool
    - To get overview of files included in PR: use github_filesinpr_tool
    - To get list of PR creators: use github_listprauthors_tool
    - To get list of all the comments in PR: use github_prcomments_tool
    - For YouTube: Use YouTubeSearchTool    
	
	Think step by step before using tools.	
    """
    LOG("Invoking LLM...")
    response = llm.invoke([SystemMessage(system_prompt)] + state['messages'] )
    return {"messages" : [response]}

#Define graph
def create_graph(llm, tools):    

    LOG("Create graph...")
    graph = StateGraph(AgentState)
    
    graph.add_node("llm_node", lambda state: call_llm(state,llm))
    
    #Get a ToolNode
    tool_node = ToolNode(tools=tools)
    graph.add_node ("tool_node", tool_node)

    #Add start edge
    graph.add_edge(START, "llm_node")
    
    #add conditional edge
    graph.add_conditional_edges(
        "llm_node", #current node
        should_continue, #action
        {
            "continue" : "tool_node",
            "end" : END
        }
    )

    #Add a link from tool_node back to llm_node
    graph.add_edge("tool_node", "llm_node")
    LOG("✅Graph created successfully.")

    #compile graph
    LOG("Compiling Graph...")
    app = graph.compile()
    LOG("✅Graph compiled successfully.")

    return app


#Decide next step 
def should_continue(state: AgentState):
    """This function decide where graph should end or continue"""     

    #get the last message from the state
    last_message = state['messages'][-1]

    #check if last message is a tools message
    if last_message.tool_calls:
        return "continue"
    else:
        return "end"

#Execute graph
def execute_graph(app,conversation_history,user_id):
    """This function execute the graph"""

    LOG("Executing graph...")
    response = app.invoke({"messages": conversation_history})
    pretty_print_messages(response["messages"],user_id)
    last_message = response["messages"] [-1]  # This is usually an AIMessage
    LOG(f"Graph executed, LLM's response:'{last_message.content[:25]}...'")
    return last_message.content

######################## END  ###################################





