
from datetime import datetime

from revolve.data_types import Resource, Table
from revolve.utils import log, save_python_code, read_python_code_template
from revolve.prompts import get_process_table_prompt
from revolve.llm import invoke_llm


def process_table(table_state:Table):
    table_name = table_state["table_name"]
    log(f"Processing table: {table_name}")
    columns = table_state["columns"]

    code_template = read_python_code_template("service.py")
    utils_template = read_python_code_template("db_utils.py")
    individual_prompt = table_state["individual_prompt"]
    schemas = str(columns)

    messages = get_process_table_prompt(utils_template=utils_template, code_template=code_template, table_name=table_name, schemas=schemas, individual_prompt=individual_prompt)
    
    structured_resource_response = invoke_llm(messages, max_attempts=3, validation_class=Resource, method="function_calling")

    log(f"Resource generated for  {table_name}")
    save_python_code(
        structured_resource_response["resource_code"],
        structured_resource_response["resource_file_name"],

    )

    new_trace = {
        "node_name": "process_table",
        "node_type": "process",
        "node_input": table_state,
        "node_output": structured_resource_response,
        "trace_timestamp": datetime.now(),
        "description": f"Resource code generated for {table_name}."
    }

    return {
        "resources": [structured_resource_response],
        "trace": [new_trace]
    }
