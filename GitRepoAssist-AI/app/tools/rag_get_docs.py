# Import packages
import chromadb
import ollama
import os
from langchain.tools import tool
import json

#import my packages
from tools import LOG

# Function to retrieve business requirements using RAG approach
@tool
def GetContext(query: str):
    """This function returns the context of business requirement. 

    Args:
        query (str): Text containing brief requirement detail or requirement ID

    Returns:
        dict: A dictionary containing business requirement details such as:
            - Context (str): Brief description of the requirement
            - Citations (str): Source documents of the requirement            
    """

    #Get the DB path
    if not os.getenv("CHROMA_DB_PATH"):
        LOG("Error finding chroma db. Path is not found in .env")
        return json.dumps({
            "fatal_error": True,
            "message": "Error in getting context, this task will not be completed."
            })
    
    #If path is configured then continue
    path=os.environ["CHROMA_DB_PATH"]
    LOG(f"Chroma db path is: {path}")
    crdb_client = chromadb.PersistentClient(path)

    #Get embedding model
    if not os.getenv("RAG_EMBEDDING_MODEL"):
        LOG("Error finding embedding model in .env")
        return json.dumps({
            "fatal_error": True,
            "message": "Error in processing the request, this task will not be completed."
            })
    
    #If model is configured then get the embedding model
    embedding_model=os.environ["RAG_EMBEDDING_MODEL"]

    # Get the chromadb collection
    try:
        collection = crdb_client.get_collection("kb_collection")
    except Exception as e:
        LOG(f"❌ Collection 'kb_collection' not found: {e}")
        return json.dumps({
            "fatal_error": True,
            "message": "Error in getting context, this task will not be completed."
            })
    
    # Get embedding for the query
    LOG(f"Getting embedding for the query: {query}...")
    query_embedding = ollama.embed(model=embedding_model, input=query)['embeddings'][0]
    LOG("✅Getting embedding for the query is successful.")

    LOG("Finding context for the query...")
    # Retrieve top-2 relevant documents from Chroma DB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=2,
        include=['documents', 'distances', 'metadatas']
    )

    #similarity_threshold=0.7 # Max distance to consider a chunk's relevance
    
    # Extract documents, distances and metadata from the results
    documents = results.get('documents')
    distances = results.get('distances')
    metadatas = results.get('metadatas')
    
    context = []
    source_docs = []
    # check if documents is not None i.e. the query on chromadb has returned some results
    # and documents[0] exists i.e. the first query’s results are non-empty
    if documents and documents[0]:
        LOG("✅Documents found for the query")
        LOG("Building context based on similarity search...")
        for doc, dist, meta in zip(documents[0], distances[0], metadatas[0]):
            #Build the context by selecting only those documents that are similar enough to the user's query.
            #This avoids passing irrelevant chunks to LLM.
            LOG(f"distance of doc {meta.get('source', 'N/A')} is {dist}")
            #if dist <= similarity_threshold:
            #    LOG("Distance less than threshold, adding the doc in context")
            context.append(doc)
            source_docs.append(meta.get('source', 'N/A'))
    
    # Join sources into a single string (if any found)
    if source_docs:
        source_docs = ",".join(source_docs)
        LOG("✅Context is built successfully.")
        # return context with source citations if context is found
        return f"Operation Successful, Context:{context}, Citations:{source_docs}"
    else:
        LOG("❌Context is not found.")
        return json.dumps({
            "fatal_error": True,
            "message": "No such requirements found, this task will not be completed."
            })
    
    
    








