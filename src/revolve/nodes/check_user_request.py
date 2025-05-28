from prompts import get_user_intent_prompt
from revolve.prompts import get_classification_prompt
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
    # structured_user_response = invoke_llm(messages, max_attempts=3, validation_class=ClassifyUserRequest, method="function_calling", manual_validation=True)
    # if not structured_user_response.intent_valid:
    #     description = "User intent is not valid. Please try again."
    #     log(description, send, level="workflow")
    #     new_trace = {
    #         "node_name": "check_user_request",
    #         "node_type": "classify_user_request",
    #         "node_input": last_message_content,
    #         "node_output": "place_holder",
    #         "trace_timestamp": datetime.now(),
    #         "description": "User intent is not valid. Please try again.",
    #     }
    #     return {
    #         "classification": "__end__",
    #         "trace": [new_trace],
    #     }


    messages = get_classification_prompt(state["messages"])

    structured_db_response = invoke_llm(messages, max_attempts=3, validation_class=ClassifyUserRequest, method="function_calling", manual_validation=True)
    description = "Prompt classifed as a task. Task is in progress." if structured_db_response.classification not in ["__end__", "response_back"] else structured_db_response.message

    last_message_content = state["messages"][-1]["content"]
    new_trace = {
        "node_name": "check_user_request",
        "node_type": "classify_user_request",
        "node_input": last_message_content,
        "node_output": "place_holder",
        "trace_timestamp": datetime.now(),
        "description": description,
    }

    if structured_db_response.classification in ["__end__", "response_back"]:
        log(description, send=send, level="workflow")

    return {
        "classification": structured_db_response.classification,
        "trace": [new_trace],
        
    }
