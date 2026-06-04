import re
import logging
from langchain_core.messages import SystemMessage, HumanMessage
from guardrails_classes import ClaimsStatus, GuardrailResult, ValidationResult
import os

logger = logging.getLogger(__name__)

#### Guardrail service definition BEGIN ####
class GuardrailService:
    
    def __init__(self, guardrail_type, judge_llm):
        self.guardrail_type = guardrail_type
        self.judge_llm = judge_llm
        self.guardrail_enabled = int(os.getenv("ENABLE_GUARDRAILS", "0"))
        

    def apply(
            self,
            candidate_text: str,
            context: str
        ) ->GuardrailResult:
        
        #guardrail is disabled
        if not self.guardrail_enabled:
            logger.info("ENABLE_GUARDRAILS is disabled in .env, returning text without checks")
            return GuardrailResult(
                status=ValidationResult.PASS,
                score=1.0,
                response = (
                    candidate_text
                    if self.guardrail_type == "INPUT"
                    else gen_structured_resp(candidate_text)
                )
            )
            
            
        match self.guardrail_type:

            case "INPUT": #apply input guardrails
                
                logger.info("Applying input guardrails...")
                verdict = input_guardrails(candidate_text, self.judge_llm)

            case "OUTPUT": #apply output guardrails
                
                logger.info("Applying output guardrails...")
                claims_status = get_claims_status(
                    judge_llm = self.judge_llm,
                    generated_answer=candidate_text,
                    context = context
                    )
                faithfulness_score = get_faithfulness(claims_status)
                verdict = hallucination_check(faithfulness_score, candidate_text)
                verdict.response = gen_structured_resp(verdict.response)
        
        return verdict
#### Guardrail service definition End ####

########## Functions BEGIN ##########

## input_guardrails ##
def input_guardrails(candidate_text, judge_llm) -> GuardrailResult:
    
    return GuardrailResult(
            status=ValidationResult.PASS,
            response=candidate_text
        )

## get supported/unsupported claims
def get_claims_status(judge_llm, generated_answer, context) -> ClaimsStatus:

    messages = [
        SystemMessage(
            content="""
            You are a faithfulness evaluator.

            Task:
            Determine whether the answer is fully supported by the provided context.

            Rules:
            - Use ONLY the supplied context.
            - Do NOT use outside knowledge.
            - A claim is supported only if the context explicitly states it or directly implies it.
            - If a claim cannot be verified from the context, mark it unsupported.
            - Be strict and conservative.
            - Extract all factual claims from the answer.
            - For every supported claim, provide supporting evidence from the context.
            """
        ),
        HumanMessage(
            content=f"""
            Context:
                {context}

            Answer: 
                {generated_answer}
            """
        )
    ]

    logger.info("Calling LLM_as_Judge to provide claims status...")
    result = judge_llm.invoke(messages)
    logger.info("Claims status is returned by LLM_as_Judge:")
    #logger.info(result)
    
    if result.model_extra:
        logger.info(f"LLM generated additional fields: {result.model_extra}")

    return result
#### End ####

#get faithfulness score
def get_faithfulness(claims_status: ClaimsStatus):

    logger.info("Processing claims...")
    total_supported_claims = len(claims_status.supported_claims)
    total_unsupported_claims = len(claims_status.unsupported_claims)
    total_claims = total_supported_claims + total_unsupported_claims

    logger.info(
        "total_claims=%s, supported_claims=%s, unsupported_claims=%s",
        total_claims,
        total_supported_claims,
        total_unsupported_claims,
    )

    logger.info("Calculating faithfulness score...")

    faithfulness_score = (
        total_supported_claims / total_claims
        if total_claims > 0
        else 1.0
    )
    logger.info(f"Faithfulness Score={faithfulness_score}")
        
    return faithfulness_score
### end ###

### check hallucination
def hallucination_check(faithfulness_score, candidate_text) -> GuardrailResult:
    
    logger.info("Generating final verdict based on faithfulness score...")

    threshold = float(os.getenv("FAITHFULNESS_THRESHOLD", "0.9"))
    logger.info(f"FAITHFULNESS_THRESHOLD={threshold}")

    ## No hallucination
    if faithfulness_score >= threshold:
        logger.info("Faithfulness score of generated answer is above threshold.")
        logger.info("No hallucination detected. Verdict=PASS")
        return GuardrailResult(
            status=ValidationResult.PASS,
            response=candidate_text,
            score=faithfulness_score
        )

    ## Partial hallucination, can regenerate the answer 
    if faithfulness_score >= (threshold * 0.6): #60% of faithfulness threshold
        logger.info("Faithfulness score of generated answer is lower than threhold but above 60%.")
        logger.info("Partial hallucination detected. Verdict=REGENERATE")
        return GuardrailResult(
            status=ValidationResult.REGENERATE,
            response=candidate_text,
            score=faithfulness_score
        )

    ## Hallucinated, do not have enough context
    logger.info("Faithfulness score of generated answer is lower than acceptable limit")
    logger.info("Complete hallucination detected. Verdict=FAIL")
    return GuardrailResult(
        status=ValidationResult.FAIL,
        response="Sorry, I do not have sufficient information to answer confidently. Please help to provide some additional details.",
        score=faithfulness_score        
    )
### end ###    

#generated structured response
def gen_structured_resp(generated_answer):

    logger.info("Generating structured response...")
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

########## Functions END ##########