import os
import json

from revolve.db import get_adapter
from revolve.prompts import get_table_schema_extractor_prompt, get_table_schema_extractor_prompt_ft
from revolve.utils import create_ft_data, log
from revolve.data_types import DBSchema, State
from datetime import datetime
from revolve.external import get_db_type
from revolve.llm import invoke_llm

def generate_prompt_for_code_generation(state: State):
    send  = state.get("send")
    log("Started", send)
    last_message_content = state["messages"][-1]["content"]
    adapter = get_adapter(get_db_type())
    schemas = str(adapter.get_schemas_from_db())
    messages = get_table_schema_extractor_prompt(last_message_content, schemas)
    

    structured_db_response = invoke_llm(messages, max_attempts=3, validation_class=DBSchema, method="function_calling", manual_validation=False)

    new_trace = {
        "node_name": "generate_prompt_for_code_generation",
        "node_type": "db",
        "node_input": last_message_content,
        "node_output": "place_holder",
        "trace_timestamp": datetime.now(),
        "description": "Table schemas extracted from the database and prompts generated for each table."
    }

    if os.environ.get("FT_SAVE_MODE","false") == "true":
        messages_ft = get_table_schema_extractor_prompt_ft(last_message_content, schemas)
        messages_ft.append({
            "role": "assistant",
            "content": json.dumps(structured_db_response, indent=2)
        })
        temp_state = {"custom_ft_data":[messages_ft]}
        create_ft_data(temp_state) 

    log("Completed", send)

    return {
        "DBSchema": structured_db_response,
        "trace": [new_trace],
    }
