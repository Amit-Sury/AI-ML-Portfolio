####################### Import Packages ##########################
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.pregel import Pregel


#streamlit for UI
import streamlit as st  

#json for saving conversation history
import json

#import my functions
from graph import execute_graph
from tools import LOG
from ui import write_convo, initialize_app


######################## END  ###################################

####################### Streamlit UI Block ######################

#markdown for displaying chat in streamlit chat window
#This hides default user, assistant icons of streamlit
#defines margins to align assistant's and user's messages to left, right respectively
def display_chat(st):
    """This function displays chat"""
    st.markdown("""
                <style>
                    /* Hide the avatar icons */
                    div[data-testid="stChatMessage"] > div:first-child {
                        display: none;
                    }
                    .chat-container {
						margin-bottom: 0.2rem !important;
					}
					.user-message {
						margin-left: auto;
						max-width: 80%;
                        margin-bottom: 0.3rem !important;  /* Added to reduce gap */
					}
					.assistant-message {
						margin-right: auto;
						max-width: 80%;
                        margin-bottom: 0.3rem !important;  /* Added to reduce gap */
					}
                    /* Reduce the gap between chat messages */
                    div[data-testid="stChatMessage"] {
                        margin-bottom: 0.2rem !important;
                        padding: 0.3rem !important;
                    }
                    
                    /* Reduce vertical block gaps */
                    div[data-testid="stVerticalBlock"] {
                        gap: 0.2rem !important;
                    }
                </style>
                """, unsafe_allow_html=True)
    for role, msg in st.session_state["messages"]:
        
        if role == "user":
            st.markdown('<div class="chat-container user-message">', unsafe_allow_html=True)
            col1, col2 = st.columns([2, 8])
            with col2:
                st.chat_message(role).write(msg)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="chat-container assistant-message">', unsafe_allow_html=True)
            col1, col2 = st.columns([8, 2])
            with col1:
                st.chat_message(role).write(msg)
            st.markdown('</div>', unsafe_allow_html=True) 

#UI starting point
def start_bot_ui():
    """This function defines streamlit UI""" 
    
    #streamlit UI page
    st.set_page_config(page_title="AI Chatbot", page_icon="\U0001F916", layout="wide") #\U0001F916 is unicode () for 🤖
    

    # Initialize session state
    if "user_id" not in st.session_state:
        st.session_state.user_id = None

    #Ask for user ID or email if not provided
    if st.session_state.user_id is None:
        
        st.title("\U0001F916 AI Chatbot")
        
        with st.form("user_form"):
            user_input = st.text_input("Enter your User ID or Email:")
            submit = st.form_submit_button("Submit")

        if submit:
            if user_input.strip():
                with st.spinner("Please wait, starting the session..."):
                    st.session_state.user_id = user_input.strip()
                    if initialize_app(st, user_input.strip()) == 1:
                        st.session_state.user_id = user_input.strip()
                        st.rerun()  # Reload page to show chatbot
                    else:
                        st.session_state.user_id = None
                        LOG("Session initialization failed.")
                        st.warning("Initialzing Session failed, please try again.")                
                
            else:
                st.warning("Please enter a valid User ID or Email.")
        st.stop()

    #Once user ID is provided, show chatbot UI
    with st.sidebar:
        st.success(f"Welcome!, \"{st.session_state.user_id}\"")
        st.markdown("<br>", unsafe_allow_html=True)

    #add stop button
    if st.sidebar.button("Save History?"):
        write_convo(st.session_state["conversation_history"], st.session_state.user_id)        
        st.toast("Conversation saved successfully!", icon="✅")
        
    #display chat history
    display_chat(st)    
    
    #take user input
    if prompt := st.chat_input("Type your question..."):        
        
        # Show user message
        st.markdown('<div class="chat-container user-message">', unsafe_allow_html=True)
        #columns to align assistant's, user's messages
        col1, col2 = st.columns([2, 8])
        with col2: #align user's mesages to right
            st.chat_message("user").write(prompt)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.session_state["messages"].append(("user", prompt))
        st.session_state["conversation_history"].append(HumanMessage(content=prompt))

        graph = st.session_state["app"]
        with st.spinner("Thinking..."):
            LOG(f"Calling LLM with user's prompt:'{prompt}'")
            answer = execute_graph(graph, st.session_state["conversation_history"],st.session_state.user_id)

        # Show bot message
        st.markdown('<div class="chat-container user-message">', unsafe_allow_html=True)
        col1, col2 = st.columns([8, 2])
        with col1: #align assistant's messages to left           
            st.chat_message("assistant").write(answer)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.session_state["messages"].append(("assistant", answer))
        st.session_state["conversation_history"].append(AIMessage(content=answer))        

######################## END  ###################################

