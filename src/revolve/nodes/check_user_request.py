from revolve.prompts import get_user_intent_prompt, get_user_intent_prompt_ft
from revolve.functions import log
from revolve.llm import invoke_llm
from revolve.data_types import State, ClassifyUserRequest
from revolve.utils import create_ft_data

from datetime import datetime
import json
import os

from revolve.utils_git import init_or_attach_git_repo, create_branch_with_timestamp



def check_user_request(state: State):
    send  = state.get("send")
    log("Started", send)
    
    message_history = state["messages"]
    if len(message_history) == 2:
        init_or_attach_git_repo()
        branch_name = create_branch_with_timestamp()
        log(f"Branch created: {branch_name}", send)


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

    if os.environ.get("FT_SAVE_MODE","false") == "true":
        messages_ft = get_user_intent_prompt_ft(state["messages"])
        messages_ft.append({
            "role": "assistant",
            "content": structured_db_response.model_dump_json(),
        })
        temp_state = {"custom_ft_data":[messages_ft]}
        create_ft_data(temp_state) 

    if structured_db_response.classification in ["respond_back"]:
        log(description, send=send, level="workflow")

    return {
        "classification": structured_db_response.classification,
        "trace": [new_trace],
    }
