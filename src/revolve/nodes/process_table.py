
from datetime import datetime

from pydantic_core import ValidationError
from revolve.data_types import Resource, Table
from revolve.functions import log, read_python_code_template, save_python_code
from src.revolve.llm import invoke_llm


def process_table(table_state:Table):
    table_name = table_state["table_name"]
    log("process_table", f"Processing table: {table_name}")
    columns = table_state["columns"]

    code_template = read_python_code_template("service.py")
    utils_template = read_python_code_template("utils.py")

    system_prompt = f"""Generate resource code according to the user request.
    Make sure that you write production quality code that can be maintained by developers.
    Include a /<resource>/schema endpoint to get the schema of the resource so that we can auto generate ui forms.
    We are using falcon 4.02 for http - so only use parameters available from that version 
    Requests should be trackable with logs in INFO mode. Double check the imports.
    when using default values to sanitize input pl used `default` keyword in the method req.get_param('order',default='asc').lower()
    Make sure that you check whether data is serializable and convert data when needed.
    Guard against SQL injection attacks. Always sanitize inputs before sending it to database.
    While creating List functionality, provide functionality to sort, order by and filter based on
    key columns as well as skip , limit and total for pagination support. If the search filter is a date field, provide functionality to match greater than,
    less than and equal to date. Filter may not be specified - handle those cases as well.
    There could be multiple endpoints for the same resource.
    Use methods from utils if needed. Here is the utils.py file:
    {utils_template}
    Here are the templates for the generation:
    for the example api route 'app.add_route("/hello_db", HelloDBResource())'
    output should be like this:
    uri: /hello_db
    resource_object: HelloDBResource()
    resource_file_name: hellodb.py
    resouce_code : {code_template} 
"""
    
    schemas = str(columns)

    # add schemas and individual prompt to the user prompt
    user_prompt = f"""
    Task : {table_state["individual_prompt"]}
    Table Name : {table_name}
    Schema : {schemas}
    """

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]

    structured_resource_response = invoke_llm(messages, max_attempts=3, validation_class=Resource, method="function_calling")


    log("process_table", f"Resource generated for  {table_name}")
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
