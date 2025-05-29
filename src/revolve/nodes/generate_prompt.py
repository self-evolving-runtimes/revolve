from revolve.db import get_adapter
from revolve.prompts import get_simple_prompt
from revolve.utils import log
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

    messages = [
        {
            "role": "system",
            "content": get_simple_prompt("table_schema_extractor")
        },
        {
            "role": "user",
            "content": last_message_content + "\n\nHere are the full schema of the database:\n" + schemas
        }
    ]


    structured_db_response = invoke_llm(messages, max_attempts=3, validation_class=DBSchema, method="function_calling")

    new_trace = {
        "node_name": "generate_prompt_for_code_generation",
        "node_type": "db",
        "node_input": last_message_content,
        "node_output": "place_holder",
        "trace_timestamp": datetime.now(),
        "description": "Table schemas extracted from the database and prompts generated for each table."
    }

    log("Completed", send)

    return {
        "DBSchema": structured_db_response,
        "trace": [new_trace],
    }
