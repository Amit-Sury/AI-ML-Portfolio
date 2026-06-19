from gen_embedding import generate_embedding
from guardrails_service import GuardrailService
from guardrails_classes import ValidationResult
from graph import execute_graph
from cache import Cache
from langchain_core.messages import HumanMessage, AIMessage
import os
import logging
import re


logger = logging.getLogger(__name__)

######## Service Definition ###################

#retrival service to handle user query
class RetrievalService:

    def __init__(self, db_client, app, llm, cache: Cache):
        self.db_client = db_client        
        self.graph = app
        self.judge_llm = llm
        self.cache = cache

    def retrieve(self, bedrock_client, query, user_session):
        
        index_name = os.getenv("INDEX_NAME", "enterprise-rag-index")
        vector_top_k = int(os.getenv("VECTOR_TOP_K", "10"))
        reranked_top_k = int(os.getenv("RE_RANKED_TOP_K", "5"))

        logger.info("ℹ️ Parameters for knowledge docs processing are following...")
        logger.info(f"Index_Name={index_name}, Vector_Top_K={vector_top_k}, Reranked_top_k={reranked_top_k} ")
        
        try:
            # check cache
            
        
            cache_response = self.cache.query_cache(query) if self.cache is not None else None
            if cache_response is not None:
                logger.info("Response found in response cache, skipping rest of the processing")
                return cache_response 

            # apply input guardrails
            input_guardrail = GuardrailService("INPUT", self.judge_llm, bedrock_client)
            result = input_guardrail.apply(candidate_text=query)
            if result.status == ValidationResult.FAIL:
                logger.info("Input guardrail has blocked the query")
                return gen_structured_resp(result.response)
            
            updated_query = result.response
            # generate embedding
            embedding = generate_embedding(bedrock_client, updated_query)
            
            # retrieve knowledge
            docs = retrieve_knowledge(self, embedding, index_name, vector_top_k)

            # build context
            context = context_builder(updated_query, docs, reranked_top_k)
            
            # prompt assembly
            system_prompt = prompt_assembly(context)
            
            #append the user query in session
            user_session.append(HumanMessage(content=updated_query))

            # call llm
            generated_response = call_llm(self, user_session, system_prompt)
            
            ## apply output guardrails
            output_guardrail = GuardrailService("OUTPUT", self.judge_llm, bedrock_client)
            result = output_guardrail.apply(
                candidate_text=generated_response,
                context=context,
                session=user_session
            )
            
            #append the AI response in session
            user_session.append(AIMessage(content=result.response))
            
            # generate structure response
            structure_resp = gen_structured_resp(result.response)

            # load response in cache for queries which are answered by a valid context
            if (result.status is not ValidationResult.FAIL 
                and len(structure_resp["sources"]) > 0
            ):
                self.cache.update_cache(updated_query, structure_resp)

            return structure_resp

        except Exception as e:
            logger.error(f"❌ Error! Retrieval Service Execution failed.")
            logger.error(f"❌ Exception: {e}")
            response = "Oops! An unexcepted error happened during response processing, please try later"
            return gen_structured_resp(response)

######## Retrieval Service Definition END ##########

########### Functions block BEGIN #################

# search vector db for similarity
def retrieve_knowledge(self, embedding, index_name, vector_top_k):

    search_query = {
        "size": vector_top_k,
        "query": {
            "knn": {
                "embedding": {
                    "vector": embedding,
                    "k": vector_top_k
                }
            }
        }
    }

    logger.info("Getting similarities from knowledge store...")
    response = self.db_client.search(body=search_query, index=index_name)
    logger.info("Search completed. Proceeding further...")
    return response
#### END #######

# build context from retrived knowledge 
def context_builder(query, docs, reranked_top_k):

    logger.info("Building context...")
    #currently reranking is not handled hence query is not used
    #reranked = rerank(query, hits)
    context = get_top_k(docs, reranked_top_k)
    logger.info("Context building completed. Proceeding further...")
    return context
#### END #######

#get top_k from the searched result
def get_top_k(docs, top_k):

    #getting the "hits" returned by opensearch response
    hits = docs["hits"]["hits"]

    #for hit in hits:
    #    score = hit["_score"]
    #    text = hit["_source"]["text"]

    # Sort by score descending (usually already sorted)
    sorted_hits = sorted(
        hits,
        key=lambda x: x["_score"], #takes one record from hits i.e. "for hit in hits" take hit["_score"]
        reverse=True
    )
    
    # Select top 5
    selected_chunks = sorted_hits[:top_k]

    # Extract text/context
    top_k_chunks = [
        {
            "text": chunk["_source"]["text"],
            "filename": chunk["_source"]["source"]
        }
        for chunk in selected_chunks
    ]
    
    return top_k_chunks
#### END #######    

#assembling system_prompt based on context
def prompt_assembly(context):
    
    context_text = ""
    logger.info("Assembling prompt...")
    for doc_id, chunk in enumerate(context, start=1):

        context_text += f"""
        Context {doc_id}:
        Source: {chunk['filename']}
        
        Content:
        {chunk['text']}

        """

    system_prompt = f"""
    You are a helpful assistant. Answer the user's question using ONLY the provided context..
    If the context is not enough then say enough information is not available and ask more 
    information from the user from the user.

    Context:
    {context_text}

    Response Guidelines:
    - Use clean markdown formatting
    - Keep responses concise but informative
    - Use short paragraphs
    - Use bullet points only when useful
    - Use headings only when the response is long
    - Use tables only for structured comparisons
    - Use code blocks only for technical/code content
    - Maintain a professional enterprise tone
    - If information is not present in the context, clearly say so
    - Do not hallucinate or invent information
    - In the response add source filename at the end when available for e.g "Citation: sample.pdf"

    When possible:
    - Start directly with the answer
    - Avoid unnecessary introductions
    - Optimize readability for enterprise users
    """

    logger.info("Prompt assembly completed. Proceeding further...")
    return system_prompt
#### END #######

#call llm by invoking graph
def call_llm(self, user_session, system_prompt):

    logger.info("Calling LLM to generate response...")
    answer = execute_graph(self.graph, user_session, system_prompt)
    logger.info("Response generation completed.")
    return answer 
#### END #######


#generated structured response
def gen_structured_resp(generated_answer):

    logger.info("Generating structured response...")
    
    if isinstance(generated_answer, list):
        generated_answer = "\n".join(map(str, generated_answer))
    elif generated_answer is None:
        generated_answer = ""
    else:
        generated_answer = str(generated_answer)

    response_json = {
        "answer": generated_answer.strip(),
        "sources": []
    }

    citation_match = re.search(
        #r'Citation:\s*(.*)',
        r'(Citation|Citations|Source|Sources)\s*:?\s*(.*)',
        generated_answer,
        re.IGNORECASE
    )

    if citation_match:

        #citations_text = citation_match.group(1)
        citations_text = citation_match.group(2)

        sources = re.split(r'[\n,]+', citations_text)

        sources = [
            s.strip()
            for s in sources
            if s.strip()
        ]

        answer = re.sub(
            #r'Citation:\s*.*',
            r'(Citation|Citations|Source|Sources)\s*:?\s*.*',
            '',
            generated_answer,
            flags=re.IGNORECASE
        ).strip()

        response_json = {
            "answer": answer,
            "sources": sources
        }

    logger.info("Structured response generation completed.")
    return response_json
### end ###

########### Functions block END ######################

