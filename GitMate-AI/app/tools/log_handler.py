####################### Import packages #########################
import os 
from datetime import datetime
import inspect
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
import json
######################## END  ###################################

def LOG(content:str):
    """This function writes logs"""
    
    log_switch = int(os.environ["DEBUG_LOG"])

    if log_switch == 1:
        
        path = os.environ["LOG_PATH"]
        user_id = os.environ["user_id"]
                        
        #get time in format yyyymmddhhmm, per minute one log file
        now = datetime.now()
        current_time = now.strftime("%Y%m%d%H")
        #filepath = os.path.join(path, f"debug_{st.session_state.user_id}_{current_time}.log")
        filepath = os.path.join(path, f"debug_{user_id}_{current_time}.log")
        
        #get call function name
        func_name = inspect.currentframe().f_back.f_code.co_name  # caller function

        with open(filepath, "a", encoding="utf-8") as f:
            # Timestamp inside log file in format as yyyymmddhhmmss.FFF (with millisecond)
            timestamp = now.strftime("%Y%m%d%H%M%S") + f".{int(now.microsecond / 1000):03d}"
            f.write(f"[{timestamp}]::[func:{func_name}]--------[{content}]\n")
            
        
################## Store last AI response to file BEGIN  ##################

#converting langchain message to dicts
def message_to_dict(msg):
    """Convert LangChain messages into dicts for pretty printing."""
    if isinstance(msg, (HumanMessage, AIMessage, ToolMessage, SystemMessage)):
        return {
            "type": msg.__class__.__name__,
            "content": msg.content,
            "additional_kwargs": getattr(msg, "additional_kwargs", {}),
            "response_metadata": getattr(msg, "response_metadata", {}),
            "id": getattr(msg, "id", None),
            "tool_calls": getattr(msg, "tool_calls", None),
            "usage_metadata": getattr(msg, "usage_metadata", None),
            "name": getattr(msg, "name", None),
            "tool_call_id": getattr(msg, "tool_call_id", None),
        }
    elif isinstance(msg, dict):  # already a dict
        return msg
    else:
        return str(msg)

#pretty printing messages to a file
def pretty_print_messages(messages,user_id):
    """Pretty print a list of LangChain messages."""
    
    write_langchain_msg = int(os.environ["WRITE_LANGCHAIN_MSGS"])

    if write_langchain_msg == 1:
        data = [message_to_dict(m) for m in messages]

        path = os.environ["LOG_PATH"]
        filepath = os.path.join(path, f"full_llm_response_{user_id}.json")
        message_filepath = os.path.join(path, f"msg_exchange_{user_id}.log")
        
        # Save llm response to JSON
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data,f,indent=2,ensure_ascii=False)

        now = datetime.now()
        with open(message_filepath, "a", encoding="utf-8") as file:
            for message in data: 
                content = []
                for key, value in message.items():                
                    if key in ("type", "content", "tool_calls"):
                        content.append(f"[{key}]===[{value}]") 
                timestamp = now.strftime("%Y%m%d%H%M%S") + f".{int(now.microsecond / 1000):03d}"
                file.write(f"[{timestamp}]::{content}\n")
            

######################## END  ###################################