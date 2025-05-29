from revolve.prompts import get_user_intent_prompt
from revolve.functions import log
from revolve.data_types import State, ClassifyUserRequest
from datetime import datetime

from revolve.llm import invoke_llm



def check_user_request(state: State):
    send  = state.get("send")
    log("Started", send)
    
    #understand user intent
    last_message_content = state["messages"][-1]["content"]

    messages = get_user_intent_prompt(state["messages"])
    structured_db_response = invoke_llm(messages, max_attempts=3, validation_class=ClassifyUserRequest, method="function_calling", manual_validation=True)
    description = "Prompt classifed as a task. Task is in progress." if structured_db_response.classification not in ["respond_back"] else structured_db_response.message

    last_message_content = state["messages"][-1]["content"]
    new_trace = {
        "node_name": "check_user_request",
        "node_type": "classify_user_request",
        "node_input": last_message_content,
        "node_output": "place_holder",
        "trace_timestamp": datetime.now(),
        "description": description,
    }

    if structured_db_response.classification in ["respond_back"]:
        log(description, send=send, level="workflow")

    return {
        "classification": structured_db_response.classification,
        "trace": [new_trace],
        
    }
