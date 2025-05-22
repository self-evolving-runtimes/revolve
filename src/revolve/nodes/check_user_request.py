from revolve.prompts import get_simple_prompt, get_classification_prompt
from revolve.functions import get_schemas_from_db, log
from revolve.data_types import DBSchema, State, ClassifyUserRequest
from datetime import datetime

from revolve.llm import invoke_llm



def check_user_request(state: State):
    send  = state.get("send")
    log("check_user_request", "Started", send)
    last_message_content = state["messages"][-1].content

    messages = get_classification_prompt(last_message_content)

    structured_db_response = invoke_llm(messages, max_attempts=3, validation_class=ClassifyUserRequest, method="function_calling")

    new_trace = {
        "node_name": "check_user_request",
        "node_type": "classify_user_request",
        "node_input": last_message_content,
        "node_output": "place_holder",
        "trace_timestamp": datetime.now(),
        "description": structured_db_response["message"],
    }

    log("check_user_request", "Completed", send)

    return {
        "classification": structured_db_response["classification"],
        "trace": [new_trace],
    }
