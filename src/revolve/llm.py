import os

from pydantic_core import ValidationError
from revolve.data_types import *
from langchain_openai import ChatOpenAI
os.environ["LITELLM_LOG"] = "ERROR"
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

import litellm


def invoke_llm(messages, max_attempts=3, validation_class=None, method="function_calling", logger=None, manual_validation=False):
    llm_provider = os.environ.get("LLM_PROVIDER", "openai").lower()
    if llm_provider == "openai":
        return _invoke_openai_llm(messages, max_attempts, validation_class, method, logger, manual_validation)
    elif llm_provider == "opensource":
        return _invoke_opensource_llm(messages, max_attempts, validation_class, method, logger, manual_validation)
    else:
        raise ValueError(f"Unsupported LLM provider: {llm_provider}")


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

def _invoke_opensource_llm(messages, max_attempts=5, validation_class=None, method="function_calling", logger=None, manual_validation=False):
    
    fixed_message_history = revise_message_history(messages, validation_class, manual_validation)
    
    for i in range(max_attempts):
        try:
            llm_response = litellm.completion(
                model=os.getenv("MODEL_NAME"),
                base_url=os.getenv("BASE_URL"),
                messages=fixed_message_history,
                api_key="vllm",
                temperature=0.1,
                max_tokens=20000,
                stop=["</s>"],
            )
            raw_response = llm_response["choices"][0]["message"]["content"]
            fixed_message_history.append(
                {
                    "role": "assistant",
                    "content": raw_response
                }
            )
            parsed_response = parse_llm_response(raw_response, validation_class, manual_validation)
            if parsed_response:
                return parsed_response
        except Exception as e:
            fixed_message_history.append(
                {
                    "role": "user",
                    "content": f"Ensure the response is a valid JSON and wrapped in <tool_call></tool_call> XML tags. Error: {str(e)}"
                })
            continue
        
            

def revise_message_history(messages, validation_class=None, manual_validation=False):
    """
    Fixes the message history by removing any assistant messages that appear after the system message which is not allowed by the LLM.
    Also revise system message to include needed schmema information.
    """
    fixed_messages = []
    last_role = None

    for message in messages:
        role = message.get("role")

        if role == "system" and not fixed_messages:
            fixed_messages.append(message)
            last_role = "system"
            continue

        if last_role == "system" and role == "assistant":
            continue

        if last_role in ("user", "assistant") and role == last_role:
            continue

        fixed_messages.append(message)
        last_role = role
    
    if manual_validation: 
        # that means it is a pydantic class
        raw_output_structure = validation_class.model_json_schema()
    else: 
        # that means it is a typed dict
        raw_output_structure = typed_dict_dump_schema_json(validation_class)
    
    output_structure = json.dumps(raw_output_structure, indent=2)
    fixed_messages[0]["content"]  = f"""{fixed_messages[0]['content']}
Return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{output_structure}
</tool_call>"""

    return fixed_messages

def parse_llm_response(response, validation_class=None, manual_validation=False):
    """
    Parses the LLM response and returns the result.
    """
    
    if "</tool_call>" in response:
        response = response.split("<tool_call>")[1].split("</tool_call>")[0].strip()
    

    if manual_validation:
        return validation_class.model_validate_json(response)
    else:
        _json_response = json.loads(response)
        if "properties" in _json_response:
            _json_response = _json_response["properties"]
        return _json_response

    


