import os

from pydantic_core import ValidationError
from revolve.data_types import *
from langchain_openai import ChatOpenAI

def invoke_llm(messages, max_attempts=3, validation_class=None, method="function_calling", logger=None, manual_validation=False):
    llm_provider = os.environ.get("LLM_PROVIDER", "openai").lower()
    if llm_provider == "openai":
        return _invoke_openai_llm(messages, max_attempts, validation_class, method, logger, manual_validation)
    elif llm_provider == "opensource":
        return _invoke_opensource_llm(messages, max_attempts, validation_class, method, logger, manual_validation)
    else:
        raise ValueError(f"Unsupported LLM provider: {llm_provider}")

def _invoke_opensource_llm(messages, max_attempts=3, validation_class=None, method="function_calling", logger=None, manual_validation=False):
    pass

def _invoke_openai_llm(messages, max_attempts=3, validation_class=None, method="function_calling", logger=None, manual_validation=False):
    llm  = ChatOpenAI(model=os.getenv("MODEL_NAME", "gpt-4.1"), temperature=0.2, max_tokens=16000)
   
    if validation_class:
        llm = llm.with_structured_output(validation_class, method=method)


    for i in range(max_attempts):
        try:
            response = llm.invoke(messages)
            if manual_validation and isinstance(response, validation_class):
                return response
            elif response and (not validation_class or validation_class(**response)):
                return response
        except ValidationError:
            if logger:
                logger("Regenerating on ValidationError.")
    return None
