import os

from pydantic_core import ValidationError
from revolve.data_types import *
from langchain_openai import ChatOpenAI

def invoke_llm(messages, max_attempts=3, validation_class=None, method="function_calling", logger=None, manual_validation=False):
    llm  = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4.1"), temperature=0.2, max_tokens=16000)
   
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


### GOOGLE - GEMINI
### -------------------------- 
# llm  = ChatOpenAI(model="gemini-2.5-pro-preview-05-06", temperature=0.2, max_tokens=16000, api_key=os.getenv("GEMINI_KEY"), base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
# parse_method = "function_calling"
# parallel = True
### --------------------------


### LLM - RUNPOD
### -------------------------- ###
# llm  = ChatOpenAI(model="Qwen/Qwen3-30B-A3B", temperature=0.1, max_tokens=16000, base_url="http://localhost:8000/v1/", api_key="no_needed")
# parse_method = "function_calling"
# parallel = False
### -------------------------- ###


### LLM - Local Ollama
# --------------------------
# llm  = ChatOpenAI(model="qwen3:30b-a3b", temperature=0.1, max_tokens=7000, base_url="http://localhost:11434/v1/", api_key="ollama")
# parallel = False
# --------------------------

### Previous LLMs
# llm_router = llm.with_structured_output(NextNode, method=parse_method)
# llm_table_extractor = llm.with_structured_output(DBSchema, method=parse_method)
# llm_resource_generator = llm.with_structured_output(Resource, method=parse_method)
# llm_test_generator = llm.with_structured_output(GeneratedCode, method=parse_method)
# llm_test_and_code_reviser = llm.with_structured_output(CodeHistoryMessage, method=parse_method)
# llm_readme_generator = llm.with_structured_output(Readme, method=parse_method)