# This script builds the knowledge store from documents by generating embeddings from it using EMBEDDING_MODEL.
# Generated embeddings are stored in persistent Chroma DB which will act as vector store for RAG information retrieval. 
# Make sure to run this script once before running the Streamlit UI script.
# Required packages: chromadb, ollama, python-docx, PyPDF2

import chromadb     #Chroma DB for vector store
import ollama       # Ollama client for embeddings
import os           # For file handling
import PyPDF2      # For reading PDF documents
from docx import Document # For reading Word documents

# Function to load all word (.docx) and pdfs (.pdf) from a folder
# Enhance this function to load documents from other sources like databases, Sharepoint, web etc.
def load_documents(folder_path):

    docs = []
    doc_ids = []
    filenames = []

    # iterate through all files in the folder
    for i, filename in enumerate(os.listdir(folder_path)):
        file_path = os.path.join(folder_path, filename)
        text = ""
        # Handle word documents with .docx extension
        if filename.endswith(".docx"):
            print(f"Processing word doc: \"{filename}\"")
            doc = Document(file_path)
            text = "\n".join([p.text for p in doc.paragraphs if p.text.strip() != ""])
        # Handle PDF documents with .pdf extension    
        elif filename.endswith(".pdf"):
            print(f"Processing PDF file: \"{filename}\"")
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        else:
            print(f"Skipping unsupported file: {filename}") 
            continue  # skip unsupported file types

        if text.strip():  # only add if there's content
            docs.append(text)
            doc_ids.append(str(i))
            filenames.append(filename)
    
    print("Reading documents completed!")
    return docs, doc_ids, filenames

# add a chunking mechanism if documents are large
def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

# Function to generate embeddings and add to Chroma
def add_docs_to_chroma(docs, doc_ids, filenames, collection, embedding_model):

    chunk_size=100
    overlap=40
    for doc, doc_id, filename in zip(docs, doc_ids, filenames):
        # Chunk the document if it's too large
        chunks = chunk_text(doc, chunk_size, overlap)
        for i, chunk in enumerate(chunks):
            emb = ollama.embed(model=embedding_model, input=chunk)["embeddings"][0]
            chunk_id = f"{doc_id}_chunk_{i}"
            collection.add(
                documents=[chunk],
                embeddings=[emb],
                ids=[chunk_id],
                metadatas=[{"source": filename}]  # for citations
            )
        print(f"Added document ID {doc_id} from file \"{filename}\".")

######################### Knowledge Store Handling BEGIN ###############

# Get folder from where the knowledge store shall be build
print("\n\nStarting the process to build the Knowledge Store...")
folder_path = input("\nEnter the path of the folder to pickup the documents from (e.g. D:\\Docs): ")
path = input("\nEnter New Folder path where knowldege store shall be created (e.g. D:\\knowledge-store): ")

# Load documents
print(f"\nReading documents (.docx, .pdf) from folder: {folder_path}...")
docs, doc_ids, filenames = load_documents(folder_path)

# Persistent Chroma DB client
print(f"\nCreating Persistent Chromdb at location: {path}...")
crdb_client = chromadb.PersistentClient(path)

# Create or get collection. Collections are where your embeddings, documents, and metadata will be stored
#  'get_or_create_collection` avoids creating a new collection every time
collection = crdb_client.get_or_create_collection("kb_collection", metadata={"hnsw:space": "cosine"})

# Embedding model
embedding_model = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'

# Add documents to Chroma DB
print("\nGenerating embeddings and loading them to Chroma DB...")
add_docs_to_chroma(docs, doc_ids, filenames, collection, embedding_model)

# Persist the Chroma DB to disk
print(f"Persistent Chroma DB ready. All documents are added to ChromaDB at location: {path}")
print("Process Successfully completed!")


