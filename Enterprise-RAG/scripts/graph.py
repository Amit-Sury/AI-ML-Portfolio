################ Import required pacakges #######################
#langgraph packages
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
#langchain packages
from langchain_core.messages import BaseMessage, SystemMessage
#Annotations
from typing import Annotated, TypedDict, Sequence
import logging
logger = logging.getLogger(__name__)
####################### END  ###################################

################ Langgraph Code BEGIN ###########################

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    system_prompt: str

#Call LLM
def call_llm(state: AgentState, llm):    
    """This function call AWS LLM"""    
    
    response = llm.invoke([SystemMessage(state['system_prompt'])] + state['messages'] )
    
    return {"messages" : [response]}

#Define graph
def create_graph(llm):    

    graph = StateGraph(AgentState)
    graph.add_node("llm_node", lambda state: call_llm(state,llm))
    graph.add_edge(START, "llm_node") #Add start edge
    graph.add_edge("llm_node", END) #Add end edge
    app = graph.compile()    
    return app


#Execute graph
def execute_graph(app, session, system_prompt):
    """This function execute the graph"""

    logger.info("Executing graph...")
    
    response = app.invoke({"messages": session, "system_prompt" : system_prompt})
    last_message = response["messages"] [-1]  # This is usually an AIMessage

    logger.info("Graph execution completed.")
    
    return last_message.content

######################## END  ###################################





