from pydantic import BaseModel, Field, ConfigDict
from typing import List
from dataclasses import dataclass
from enum import Enum

#### Class definition BEGIN ####

## LangChain structured output, defined as Pydantic Base model
## pydantic lib will ensure that data stored matches with the 
## types and constraints defined in the class.
## Pydantic model will teach the LLM that response should be in the format class ClaimsStatus
## LangChain 

## Info:
    #Supported Claim defintion
    # specifies that one supported claim should contain a claim, and evidence field.
    # for e.g a supported claim shall look like:
    #  {
    #    "claim": "Paris is the capital of France",
    #    "evidence": "The context states that Paris is the capital city of France."
    #  }
    # "Field: Field(description=...) is just metadata. It tells the LLM what each field means."
class SupportedClaim(BaseModel):
    claim: str = Field(description="Claim supported by the context")
    evidence: str = Field(description="Supporting evidence from the context")

## Info:
    #UnSupported Claim defintion
    # specifies that one usupported claim should contain a claim, and reason field.
    # for e.g an unsupported claim shall look like:
    #  {
    #    "claim": "Paris is the capital of France",
    #    "reason": "Population is not mentioned in the context."
    #  }
class UnsupportedClaim(BaseModel):
    claim: str = Field(description="Claim not supported by the context")
    reason: str = Field(description="Why the claim is unsupported")

##Claim status class, consisting of list of SupportedClaim & UnsupportedClaim as defined above
#Claim status return by llm would look like below
#{
#    "supported_claims": [
#        {
#            "claim": "...",
#            "evidence": "..."
#        }
#    ],
#    "unsupported_claims": [
#        {
#            "claim": "...",
#            "reason": "..."
#        }
#    ]
#}
class ClaimsStatus(BaseModel):
    # this will alow any extra information added by llm. Such extra info will be logged.
    model_config = ConfigDict(extra="allow")

    supported_claims: List[SupportedClaim] = Field(
        description="Claims supported by the provided context"
    )
    unsupported_claims: List[UnsupportedClaim] = Field(
        description="Claims not supported by the provided context"
    )	

## validation result Enum with three possibilities. Used in GuardrailResult
class ValidationResult(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REGENERATE = "REGENERATE"

#Guardrail result
@dataclass
class GuardrailResult:
    status: ValidationResult
    response: str
    score: float
    #reason: str | None = None

#### Data Class definition END ####