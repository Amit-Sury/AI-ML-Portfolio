# This script use the knowledge store built from documents to answer user queries using RAG approach.
# It first tries to find the answer in the knowledge base and if not found, it falls back to general LLM.
# Make sure that you've built the knowledge store by executing the indexing script first.
# Required packages: chromadb, ollama, streamlit, subprocess

# Import packages
import chromadb
import ollama
import subprocess
import streamlit as st

# Function to retrieve answer using RAG approach
def retrieve_answer(query, embedding_model, llm_model, collection):
    # Get embedding for the query
    query_embedding = ollama.embed(model=embedding_model, input=query)['embeddings'][0]
    
    # Retrieve top-2 relevant documents from Chroma DB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=2,
        include=['documents', 'distances', 'metadatas']
    )

    similarity_threshold=0.7 # Max distance to consider a chunk's relevance
    
    # Extract documents, distances and metadata from the results
    documents = results.get('documents')
    distances = results.get('distances')
    metadatas = results.get('metadatas')
    
    context = []
    source_docs = []
    # check if documents is not None i.e. the query on chromadb has returned some results
    # and documents[0] exists i.e. the first query’s results are non-empty
    if documents and documents[0]:
        for doc, dist, meta in zip(documents[0], distances[0], metadatas[0]):
            #Build the context by selecting only those documents that are similar enough to the user's query.
            #This avoids passing irrelevant chunks to LLM.
            if dist <= similarity_threshold:
                context.append(doc)
                source_docs.append(meta.get('source', 'N/A'))
    
    # Join sources into a single string (if any found)
    if source_docs:
        source_docs = ",".join(source_docs)            
    
    #Above check ensure that if distance of the chunk from the knowledge store is greater
    # than the similarity_threshold then context will be empty
    answer = generate_answer(query, context, llm_model)
    
    # return answer with source citations if context is found
    return f"Source Docs: {source_docs} \n\n {answer}" if source_docs else answer

# Function to generate answer using LLM given context and question
def generate_answer(query, context, llm_model):
    
    # Prepare the instruction to be passed to LLM
    prompt = f"""Answer the question below naturally and directly. 
        Only use the context if it is helpful. Do not include extra explanation unless necessary.
    
    Context: {context}
    Question: {query}
    Answer:
    """
    
    #generate prompt using ollama
    result = subprocess.run(
        ["ollama", "run", llm_model, prompt],
        capture_output=True,
        text=True,
        encoding="utf-8",    # Force UTF-8 decoding
        errors="ignore"      # Optional: ignore any invalid characters
    )
    return result.stdout.strip()
   

######################### Initialize Chroma DB and models ###########
# Persistent Chroma DB client
path=r"D:\RAG\chroma_db"   #Absolute Path where ChromaDB is stored
crdb_client = chromadb.PersistentClient(path)

# Get the collection, make sure the collection name matches the one used in indexing script
try:
    collection = crdb_client.get_collection("kb_collection")
except Exception as e:
    st.error(f"❌ Collection 'kb_collection' not found: {e}")
    st.error("Please run the indexing script to create the knowledge store before using the chatbot.")
    st.error("Exiting Chatbot...")
    st.stop()  # Stop further execution if collection is not found

# Embedding model
embedding_model = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
#LLM model
llm_model = 'hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF'
######################### Init END #########################


######################### Streamlit UI Code BEGIN ###########

st.set_page_config(page_title="RAG Chatbot", page_icon="\U0001F916") #\U0001F916 is unicode () for 🤖
st.title("\U0001F916 I'm RAG Bot")

# Store chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Display history
for role, msg in st.session_state["messages"]:
    st.chat_message(role).write(msg)

# Chat input
if prompt := st.chat_input("Type your question..."):
    # Show user message
    st.chat_message("user").write(prompt)
    st.session_state["messages"].append(("user", prompt))

    bot_response = []
    with st.spinner("Thinking..."):
        answer = retrieve_answer(prompt, embedding_model, llm_model, collection)
        
    # Show bot message
    st.chat_message("assistant").write(answer)
    st.session_state["messages"].append(("assistant", answer))

######################### Streamlit UI Code END #########################


