import logging
from langchain_core.messages import SystemMessage, HumanMessage
from guardrails_classes import ClaimsStatus, GuardrailResult, ValidationResult
import os

logger = logging.getLogger(__name__)

#### Guardrail service definition BEGIN ####
class GuardrailService:
    
    def __init__(self, guardrail_type, judge_llm, bedrock_client):
        self.guardrail_type = guardrail_type
        self.judge_llm = judge_llm
        self.bedrock_client = bedrock_client
        self.guardrail_enabled = int(os.getenv("ENABLE_GUARDRAILS", "0"))
        

    def apply(
            self,
            candidate_text: str,
            context: str | None = None,
            session: list | None = None,
        ) ->GuardrailResult:
        
        #guardrail is disabled
        if self.guardrail_enabled == 0 :
            logger.info("ENABLE_GUARDRAILS is disabled in .env, returning text without checks")
            return GuardrailResult(
                status=ValidationResult.PASS,
                score=1.0,
                response = candidate_text                    
            )
            
            
        match self.guardrail_type:

            case "INPUT": #apply input guardrails

                if self.guardrail_enabled == 2: #input guardrails are disabled
                    logger.info("Input Guardrails are disabled, returning text without checks")
                    return GuardrailResult(
                        status=ValidationResult.PASS,
                        score=1.0,
                        response = candidate_text
                    ) 
                
                #input guardrails are enabled
                logger.info("Applying input guardrails...")
                verdict = input_guardrails(candidate_text, self.bedrock_client, self.judge_llm)                

            case "OUTPUT": #apply output guardrails

                if self.guardrail_enabled == 1: #output guardrails are disabled
                    logger.info("Output Guardrails are disabled, returning text without checks")
                    return GuardrailResult(
                        status=ValidationResult.PASS,
                        score=1.0,
                        response = candidate_text
                    ) 
                
                #output guardrails are enabled
                logger.info("Applying output guardrails...")
                claims_status = get_claims_status(
                    judge_llm = self.judge_llm,
                    generated_answer=candidate_text,
                    context = context,
                    session = session
                    )
                faithfulness_score = get_faithfulness(claims_status)
                verdict = hallucination_check(faithfulness_score, candidate_text)                
        
        return verdict
#### Guardrail service definition End ####

########## Functions BEGIN ##########

## input_guardrails ##
def input_guardrails(candidate_text, bedrock_client, judge_llm) -> GuardrailResult:
    
    GUARDRAIL_ID = os.getenv("AWS_GUARDRAIL_ID", "0")
    GUARDRAIL_VERSION = os.getenv("AWS_GUARDRAIL_VERSION", "1")

    try:
        # Evaluate the input text standalone
        response = bedrock_client.apply_guardrail(
            guardrailIdentifier=GUARDRAIL_ID,
            guardrailVersion=GUARDRAIL_VERSION,
            source="INPUT",  # Specify "INPUT" for prompts or "OUTPUT" for LLM responses
            content=[
                {
                    "text": {
                        "text": candidate_text
                    }
                }
            ]
        )

        # check the action determined by guardrails
        action = response.get("action")  # Will be 'NONE' or 'GUARDRAIL_INTERVENED'

        if action == "GUARDRAIL_INTERVENED":
            logger.error("🛑 Guardrail result: GUARDRAIL_INTERVENED")
            
            # get the message returned by guardrails
            updated_text = response["outputs"][0]["text"]

            # analyze which specific policy triggered the block
            assessments = response.get("assessments", [])

            if is_blocked(assessments):
                
                logger.error("⛔ User query is blocked by guardrail")
                return GuardrailResult(
                    status=ValidationResult.FAIL,
                    response=updated_text
                )
            else:
                logger.error("⚠️ User query is redacted by guardrail")
                return GuardrailResult(
                    status=ValidationResult.CONTINUE,
                    response=updated_text
                )

        else:
            logger.info("🟢 Guardrail result: NONE. Proceeding to safe LLM invocation...")
            return GuardrailResult(
                    status=ValidationResult.PASS,
                    response=candidate_text
                )

    except Exception as e:
        logger.error(f"❌ Error! Guardrail execution failed: {str(e)}")
        raise RuntimeError("Guardrail execution failed")

    

## check the assessment returned by guardrail 
def is_blocked(assessments):

    # format of assessments is like below:
    #[
    #    {
    #        "contentPolicy": {
    #        "filters": [
    #            {
    #            "type": "PROMPT_ATTACK",
    #            "confidence": "HIGH",
    #            "filterStrength": "HIGH",
    #            "action": "BLOCKED",
    #            "detected": true
    #            }
    #        ]
    #        },
    #        ....
    #    }
    #]

    for assessment in assessments:
        for f in assessment.get("contentPolicy", {}).get("filters", []):
            if f.get("detected") and f.get("action") == "BLOCKED":
                return True

    return False
## end ##

## get supported/unsupported claims
def get_claims_status(judge_llm, generated_answer, context, session) -> ClaimsStatus:

    # select only user-provided facts, filter out AIMessage
    # this is done to avoid LLM-as-a-Judge to consider even AIMessage as ground truth
    filtered_session = [
        message.content
        for message in session
        if isinstance(message, HumanMessage)
    ]

    session_text = "\n".join(filtered_session)

    messages = [
        SystemMessage(
            content="""
            You are a faithfulness evaluator.

            Task:
            Determine whether the answer is fully supported by the provided context.

            Rules:
            - Use ONLY the supplied context and session.
            - Do NOT use outside knowledge.
            - The session contains only user-provided messages.
            - Never treat the answer itself as evidence.
            - Never treat prior assistant responses as evidence or ground truth.
            - A claim is supported only if the context or session explicitly states it or directly implies it.
            - If a claim cannot be verified from the context or session, mark it unsupported.
            - Be strict and conservative.
            - Extract all factual claims from the answer.
            - For every supported claim, provide supporting evidence from the context or session.
            """
        ),
        HumanMessage(
            content=f"""
            Session:
                {session_text}

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
    
    if result and result.model_extra:
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
    ## currently not handling regeneration so returning generated response to the user
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
########## Functions END ##########