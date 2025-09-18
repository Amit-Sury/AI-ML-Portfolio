
# Import packages
import streamlit as st
import boto3
import json

############################ AWS Code BEGIN ############################

# AWS Bedrock knowledge base client runtime
rag_agent = boto3.client(service_name="bedrock-agent-runtime",region_name="us-east-1") # Change the region as per usecase

# AWS Bedrock LLM agent runtime
llm_agent = boto3.client("bedrock-runtime", region_name="us-east-1") # Change the region as per usecase

# Knowledge Base ID
kb_id = "xxxxxxxx" #replace with your knowledge base id 

# Model Id and Model ARN, change as per your model
model_id = "anthropic.claude-3-haiku-20240307-v1:0"
model_arn = f"arn:aws:bedrock:us-east-1::foundation-model/{model_id}"

# Function to call Bedrock Knowledge Base’s RetrieveAndGenerate API
def ask_bedrock(prompt: str):
    
    # First try searching in knowledge base
    kb_response = rag_agent.retrieve_and_generate(
        input={"text": prompt},
        retrieveAndGenerateConfiguration={
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": kb_id,
                "modelArn": model_arn
            },
            "type": "KNOWLEDGE_BASE"
        }
    )

    answer = kb_response["output"]["text"]
    citations = kb_response.get("citations", [])

    s3_uris = []
    found_response = False
    for citation in citations:
        for ref in citation.get("retrievedReferences", []):
            location = ref.get("location", {})
            s3_loc = location.get("s3Location", {})
            if "uri" in s3_loc:
                s3_uris.append(s3_loc["uri"])
                found_response = True


    # If found answer in knowledge base then return it
    if answer.strip() and found_response:
        s3_output = "\n".join(s3_uris)
        return f"Source Docs: {s3_output} \n\n {answer}"

    # If no response from kb then get response from general LLM
    response_from_llm = llm_agent.invoke_model(
        modelId=model_id,  
        body=json.dumps({
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": prompt}]}
            ],
            "max_tokens": 300,
            "anthropic_version": "bedrock-2023-05-31"
        }),
        accept="application/json",
        contentType="application/json"
    )

    result = json.loads(response_from_llm["body"].read().decode())
    # Claude 3 puts text here
    content = result.get("content", [])
    if content and len(content) > 0 and "text" in content[0]:
        return f"Response from LLM: {content[0]["text"]}"

    return "⚠️ No response"
    

############################ AWS Code END ############################

######################### Streamlit UI Code BEGIN #########################

st.set_page_config(page_title="RAG Chatbot", page_icon="\U0001F916") #\U0001F916 is unicode () for 🤖

st.title("\U0001F916 I'm RAG Bot")

#st.write("Ask me anything from your knowledge base!")

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

    # Call Bedrock
    with st.spinner("Thinking..."):
        answer = ask_bedrock(prompt)
    # Show bot message
    st.chat_message("assistant").write(answer)
    st.session_state["messages"].append(("assistant", answer))

######################### Streamlit UI Code END #########################