######## contextvars utility code BEGIN ##########
#This utility uses contextvars to store user_id for LOG files
#ContextVar is more advanced than thread_local because it works
#with async tasks (different contexts inside same thread).
#a good fit for langgraph, tools function because tool execution looses 
#streamlit session 

from contextvars import ContextVar

#This will hold user_id for the current context 
_current_user_id: ContextVar[str | None] = ContextVar("hold_user_id_for_logging", default=None)

# _current_user_id: is the variable name
#ContextVar[str | None]: 
#Above statement tells that variable contains a ContextVar that stores a value of type str or None.
# = ContextVar("hold_user_id_for_logging", default=None)
#This creates the variable using the ContextVar constructor.
#"hold_user_id_for_logging" is just a label used by ContextVar, for: debugging, logging tracebacks

#Function to set the user_id to current context
def set_contextvar_userid(user_id: str):
    """This function sets the user_id to current context
       using contextvar package
    """
    _current_user_id.set(user_id) 

#Function to get the user_id from the current context
def get_contextvar_userid():
    """This function returns the user_id from the current context"""
    return _current_user_id.get()

############### END ##########################
