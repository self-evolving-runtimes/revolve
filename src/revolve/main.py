import ast
from langchain_core.messages import AnyMessage
from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, START, END
# from IPython.display import Image, display
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from pydantic_core import ValidationError

from src.revolve.data_types import State, DBSchema, Table, Resource, NextNode, GeneratedCode, CodeHistoryMessage, Readme
from langchain_openai import ChatOpenAI
from src.revolve.functions import run_query_on_db, read_python_code, read_python_code_template, save_python_code, log, save_state, retrieve_state, run_pytest, test_db, get_schemas_from_db, check_schema_if_has_foreign_key
from src.revolve.prompts import get_simple_prompt, get_test_generation_prompt, get_test_generation_prompt_ft, get_test_revising_prompt, get_test_revising_prompt_ft
from datetime import datetime
from langgraph.constants import Send
import pickle
from src.revolve.utils_git import *
from src.revolve.utils import create_ft_data, create_test_report, create_report_json



### OPENAI
### -------------------------- 
llm  = ChatOpenAI(model="gpt-4.1", temperature=0.2, max_tokens=16000)
parse_method = "function_calling"
parallel = True
### --------------------------

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

llm_router = llm.with_structured_output(NextNode, method=parse_method)
llm_table_extractor = llm.with_structured_output(DBSchema, method=parse_method)
llm_resource_generator = llm.with_structured_output(Resource, method=parse_method)
llm_test_generator = llm.with_structured_output(GeneratedCode, method=parse_method)
llm_test_and_code_reviser = llm.with_structured_output(CodeHistoryMessage, method=parse_method)
llm_readme_generator = llm.with_structured_output(Readme, method=parse_method)

def router_node(state: State):
    # ---------------------------------------
    # ROUTE with LLM Decisions like an Agent, we can use the LLM to decide the next step
    # messages = [
    #     {
    #         "role": "system",
    #         "content": "Based on user request select the next path to take. The options are: generate_prompt_for_code_generation, do_stuff, do_other_stuff. If none of these options are relevant, return __end__."
    #     },
    #     {
    #         "role": "user",
    #         "content": state["messages"][-1].content
    #     }
    # ] 

    # llm_router_response = llm_router.invoke(messages)
    # return {
    #     "next_node": llm_router_response.name
    # }
    # ---------------------------------------

    # Route placeholder
    next_node = state.get("next_node", None)
    test_status = state.get("test_status", None)
    resources = state.get("resources", None)
    dbSchema = state.get("DBSchema", None)

    send = state.get("send")

    if not next_node:

        init_or_attach_git_repo()
        branch_name = create_branch_with_timestamp()
        log("router_node", f"Branch created: {branch_name}",send)
        log("router_node", "defaulting to generate_prompt_for_code_generation", send)
        new_trace = {
            "node_name": "router_node",
            "node_type": "router",
            "node_input": None,
            "node_output": None,
            "trace_timestamp": datetime.now(),
            "description": "Routing to generate_prompt_for_code_generation"
        }
        return {
            "next_node": "generate_prompt_for_code_generation",
            "trace": [new_trace],
        }
    elif not test_status and resources and dbSchema:
        save_state(state, "after_generation")
        test_status = []
        dbSchema = state.get("DBSchema")
        for res, table_object in zip(resources,dbSchema.get("tables")):
            new_test = {}
            new_test["resource_file_name"] = res["resource_file_name"]
            new_test["resource_code"] = res["resource_code"]
            new_test["status"] = "in_progress"
            new_test["messages"] = []
            new_test["iteration_count"] = 0
            new_test["table"] = table_object
            test_status.append(new_test)
                    
        log("router_node", f"Routing to test_node", send)
        new_trace = {
            "node_name": "router_node",
            "node_type": "router",
            "node_input": None,
            "node_output": None,
            "trace_timestamp": datetime.now(),
            "description": "Routing to test_node"
        }
        return {
            "next_node": "test_node",
            "test_status": test_status,
            "trace": [new_trace],
        }
    elif next_node == "test_node":
        next_node = "report_node"
        log("router_node", f"Routing to report_node")
        new_trace = {
            "node_name": "router_node",
            "node_type": "router",
            "node_input": None,
            "node_output": None,
            "trace_timestamp": datetime.now(),
            "description": "Routing to report_node"
        }
        return {
            "next_node": next_node,
            "trace": [new_trace],
        }

    else:
        save_state(state, "after_test")
        log("router_node", "routing to END", send)
        return {
            "next_node": "__end__",
        }

def test_node(state: State):
    send = state.get("send")
    MAX_TEST_ITERATIONS = 3
    test_example = read_python_code_template("test_api.py")
    utils = read_python_code_template("utils.py")
    api_code = read_python_code("api.py")
    for test_item in state["test_status"]:
        is_foreign_key_exist = check_schema_if_has_foreign_key(test_item["table"]["columns"])
        if is_foreign_key_exist:
            log("test_node", f"Skipping test generation for {test_item['resource_file_name']} as it has foreign key", send)
            test_item["status"] = "skipped"
            continue
        resouce_file = read_python_code(test_item["resource_file_name"])
        test_file_name = "test_"+test_item["resource_file_name"]
        log("test_node", f"Creating and testing for {test_file_name}", send)
        table_name = test_item["table"]["table_name"]
        schema = str(test_item["table"]["columns"])
        
        messages = get_test_generation_prompt(
            test_example=test_example,
            api_code=api_code,
            table_name=table_name,
            schema=schema,
            utils=utils,
            resouce_file=resouce_file,
            resource_file_name = test_item["resource_file_name"]
        )
        messages_ft = get_test_generation_prompt_ft(
            test_example=test_example,
            api_code=api_code,
            table_name=table_name,
            schema=schema,
            utils=utils,
            resouce_file=resouce_file,
            resource_file_name = test_item["resource_file_name"]
        )

        # test_item["test_generation_input_prompt"] = messages_ft

        i = 0
        while i < 3:
            try:
                structured_test_response = llm_test_generator.invoke(messages)
                if structured_test_response:
                    # Validate if the response can be deserialized
                    GeneratedCode(**structured_test_response)
                    break
                i += 1
            except ValidationError:
                log("test_node", f"Regenerating {test_file_name}", send)
                i += 1



        full_test_code = structured_test_response["full_test_code"]

        assistan_response_ft = f"""
### ASSISTANT ###
#### Test Code ({test_file_name}) ####
{full_test_code}
"""

        messages_ft.append(
            {
                "role": "assistant",
                "content": assistan_response_ft
            }
        )


        test_item["test_code"] = structured_test_response["full_test_code"]
        test_item["test_file_name"] = test_file_name
        save_python_code(
            structured_test_response["full_test_code"],
            test_file_name
        )
        commit_and_push_changes(
            message=f"Test code generated for {test_item['resource_file_name']}"
        )
        pytest_response  = run_pytest(test_file_name)
        test_item["status"] = pytest_response["status"]

        test_item["code_history"] = test_item.get("code_history", [])
        code_history_item = {
            "history_type": "creation",
            "code": {
                "new_code": "N/A",
                "what_was_the_problem": "N/A",
                "what_is_fixed": "N/A",
                "code_type": "N/A"
            },
            "test_report_before_revising": None,
            "test_report_after_revising": pytest_response,
            "iteration_index": 0
        }
        test_item["code_history"].append(code_history_item)
        test_item["test_generation_input_prompt"] = messages_ft

        for i in range(MAX_TEST_ITERATIONS):

            #get the previous code history and add pytest_response to the test_report_after_revising
            if pytest_response["status"]!= "success":
                test_item["status"] = "failed"
        

                individual_prompt = test_item["table"]["individual_prompt"]
                source_code = read_python_code(test_item["resource_file_name"])
                test_code = read_python_code(test_file_name)
                example_resource_code = read_python_code_template("service.py")
                
                new_messages = get_test_revising_prompt(
                    individual_prompt=individual_prompt,
                    source_code=source_code,
                    example_resource_code=example_resource_code,
                    test_code=test_code,
                    api_code=api_code,
                    table_name=table_name,
                    schema=schema,
                    utils=utils,
                    pytest_response=pytest_response,
                    resource_file_name = test_item["resource_file_name"]
                )

                new_messages_ft  = get_test_revising_prompt_ft(
                    individual_prompt=individual_prompt,
                    source_code=source_code,
                    example_resource_code=example_resource_code,
                    test_code=test_code,
                    api_code=api_code,
                    table_name=table_name,
                    schema=schema,
                    utils=utils,
                    pytest_response=pytest_response,
                    resource_file_name = test_item["resource_file_name"]
                )


                
                test_item["iteration_count"] += 1
                i = 0
                while i < 3:
                    try:
                        new_test_code_response = llm_test_and_code_reviser.invoke(new_messages)
                        if new_test_code_response:
                            # Validate if the response can be deserialized
                            if isinstance(new_test_code_response, CodeHistoryMessage):
                                break
                            
                        i += 1
                    except ValidationError:
                        log("test_node", f"Regenerating test code", send)
                        i += 1


                # if "code_type" in new_test_code_response:
                if new_test_code_response.code_type == "resource":
                    file_name_to_revise = test_item["resource_file_name"]
                elif new_test_code_response.code_type == "test":
                    file_name_to_revise = test_file_name
                else:
                    file_name_to_revise = "api.py"

                save_python_code(
                    new_test_code_response.new_code,
                    file_name_to_revise
                )
                commit_description = f"""What was the problem: {new_test_code_response.what_was_the_problem}
What is fixed: {new_test_code_response.what_is_fixed}
"""
                new_messages_ft.append(
                    {
                        "role": "assistant",
                        "content": f"""
### ASSISTANT ###
#### New Code ({file_name_to_revise}) ####
{new_test_code_response.new_code}
"""
                    }
                )

                code_history_item = {
                    "history_type": "revision",
                    "code": {
                        "new_code": new_test_code_response.new_code,
                        "what_was_the_problem": new_test_code_response.what_was_the_problem,
                        "what_is_fixed": new_test_code_response.what_is_fixed,
                        "code_type": new_test_code_response.code_type
                    },

                    "test_revising_input_prompt" : new_messages_ft,
                    "test_report_before_revising": pytest_response,
                    "test_report_after_revising": None,
                    "iteration_index": test_item["iteration_count"]
                }

                pytest_response  = run_pytest(test_file_name)
                test_item["status"] = pytest_response["status"]


                code_history_item["test_report_after_revising"] = pytest_response

                test_item["code_history"].append(code_history_item)
                create_report_json(state)
                commit_and_push_changes(
                    message=f"Code revised for {file_name_to_revise}",
                    description=commit_description
                )

                if code_history_item["test_report_after_revising"]["summary"]==code_history_item["test_report_before_revising"]["summary"]:
                    log("test_node", f"Test success is not changing, stopping the iteration: {test_item['iteration_count']}", send)
                    break
                
                        
            else:
                break

        
    new_trace = {
        "node_name": "test_node",
        "node_type": "test",
        "node_input": state["test_status"],
        "node_output": state["test_status"],
        "trace_timestamp": datetime.now(),
        "description": "Test cases generated and executed."
    }
    return {"test_status": state["test_status"], "trace": [new_trace]}

def create_schemas_endpoint(state: State):
    routes = set()
    for item in state["resources"]:
        module_name = item["resource_file_name"].replace(".py", "")
        routes.add(module_name)

    schemas_service = read_python_code_template("schemas.py")
    for route in routes:
        schemas_service = schemas_service.replace("## Routes", f'## Routes\n"{route}",')

    save_python_code(
        schemas_service,
        "schemas.py"
    )

    api_code = read_python_code("api.py")
    api_code = api_code.replace("###IMPORTS###", f"###IMPORTS###\nfrom schemas import SchemasResource")
    api_code = api_code.replace("###ENDPOINTS###", f"###ENDPOINTS###\napp.add_route('/schemas', SchemasResource())")
    save_python_code(
        api_code,
        "api.py"
    )

def report_node(state: State):
    task = state["messages"][0].content
    if os.environ.get("FT_SAVE_MODE","false") == "true":
        create_ft_data(state)
    create_test_report(task, state)
    commit_and_push_changes(
        message="Test report created.",
        description=""
    )

    commit_and_push_changes(
        message="All done",
        description="All done"
    )
    
    env_file = open("src/revolve/source_generated/.env", "w")
    env_file.write(f"DB_NAME={os.environ['DB_NAME']}\n")
    env_file.write(f"DB_USER={os.environ['DB_USER']}\n")
    env_file.write(f"DB_PASSWORD={os.environ['DB_PASSWORD']}\n")
    env_file.write(f"DB_HOST={os.environ['DB_HOST']}\n")
    env_file.write(f"DB_PORT={os.environ['DB_PORT']}\n")
    env_file.close()
    api_code = read_python_code("api.py")

    i = 0
    while i < 3:
        try:
            readme_result = llm_readme_generator.invoke(
                [
                    {
                        "role": "system",
                        "content": "You are a software engineer. You are responsible for writing the README file for the project. The README file should be in markdown format."
                    },
                    {
                        "role": "user",
                        "content": f"""Write a clean and concise README.md file for a Python API (api.py) built using the Falcon framework. The README should include:
env variables must be set in the .env file ("DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT")
"pip install falcon falcon-cors psycopg2" should be installed
Use the provided API code below as a reference when writing the README.
Here is the API code:\n{api_code}"""
                    }
                ]
            )

            if readme_result:
                # Validate if the response can be deserialized
                Readme(**readme_result)
                break
            i += 1
        except ValidationError:
            log("test_node", "Regenerating test code")
            i += 1


    #save the readme file
    save_python_code(
        readme_result["md_content"],
        "README.md"
    )

    commit_and_push_changes(
        message="README file created.",
        description=""
    )

    
    new_trace = {
        "node_name": "report_node",
        "node_type": "report",
        "node_input": state["test_status"],
        "node_output": state["test_status"],
        "trace_timestamp": datetime.now(),
        "description": "Test report created and README file generated."
    }

    return {
        "trace": [new_trace]
    }

def generate_prompt_for_code_generation(state: State):
    send  = state.get("send")
    log("generate_prompt_for_code_generation", "Started", send)
    last_message_content = state["messages"][-1].content
    schemas = get_schemas_from_db()

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

    i = 0
    while i < 3:
        try:
            structured_db_response = llm_table_extractor.invoke(messages)
            if structured_db_response:
                # Validate if the response can be deserialized
                DBSchema(**structured_db_response)
                break
            i += 1
        except ValidationError:
            log("generate_prompt_for_code_generation", "Regenerating prompt ", send)
            i += 1


    trace = state.get("trace", [])
    new_trace = {
        "node_name": "generate_prompt_for_code_generation",
        "node_type": "db",
        "node_input": last_message_content,
        "node_output": "place_holder",
        "trace_timestamp": datetime.now(),
        "description": "Table schemas extracted from the database and prompts generated for each table."
    }

    log("generate_prompt_for_code_generation", "Completed", send)

    return {
        "DBSchema": structured_db_response,
        "trace": [new_trace],
    }

def process_table(table_state:Table):
    table_name = table_state["table_name"]
    log("process_table", f"Processing table: {table_name}")
    columns = table_state["columns"]
    # print(f"Table: {table_name}")
    # print("User Prompt: ", table_state["individual_prompt"])
    # for col in columns:
    #     print(f"Table Name : {table_name}, Column: {col['column']}, Type: {col['type']}, Is Nullable: {col['is_nullable']}")

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

    i = 0
    while i < 3:
        try:
            structured_resource_response = llm_resource_generator.invoke(messages)
            if structured_resource_response:
                # Validate if the response can be deserialized
                Resource(**structured_resource_response)
                break
            i += 1
        except ValidationError:
            log("process_table", "Regenerating ")
            i += 1

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

def _process_table(state:State):
    traces = []
    resources = []
    for table_state in state["DBSchema"]["tables"]:
        table_name = table_state["table_name"]
        log("process_table", f"Processing table: {table_name}")
        columns = table_state["columns"]
        # print(f"Table: {table_name}")
        # print("User Prompt: ", table_state["individual_prompt"])
        # for col in columns:
        #     print(f"Table Name : {table_name}, Column: {col['column']}, Type: {col['type']}, Is Nullable: {col['is_nullable']}")

        code_template = read_python_code_template("service.py")

        system_prompt = f"""Generate resource code according to the user request.
        Generate Falcon 4.x resource code for a Python API implementing CRUD (Create, Read, Update, Delete) and LIST operations based on the provided schema. The schema may include unique constraints, data types (e.g., UUID, JSONB, timestamps), and nullable fields. The code must adhere to the following guidelines:
        Framework Compliance:
        Use Falcon 4.x with falcon.asgi.App for asynchronous support.
        Utilize the latest Falcon request/response structures, avoiding deprecated attributes (req, resp).
        Data Handling and Serialization:
        Implement data validation and serialization checks.
        Ensure all output data is JSON-serializable, handling complex types (e.g., UUID, JSONB) appropriately.
        Security and Input Sanitization:
        Apply input sanitization to guard against SQL injection.
        Enforce data validation for fields with unique constraints to prevent false positives.
        Error Handling and Logging:
        Implement structured error handling using Falcon’s HTTPError.
        Enable logging for all key operations, including CRUD actions and filtering operations.
        LIST Operations and Filtering:
        Implement LIST operations with sorting, ordering, and filtering capabilities.
        If a field is a date, include comparison operators (eq, lt, gt) for filtering.
        Ensure pagination support for large datasets.
        Endpoint Structure and Consistency:
        Define separate endpoints for CRUD and LIST operations to maintain clarity.
        Ensure all routes are named clearly and consistently, e.g., /users for LIST, /users/{{user_id}} for CRUD.
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

        i = 0
        while i < 3:
            try:
                structured_resource_response = llm_resource_generator.invoke(messages)
                if structured_resource_response:
                    # Validate if the response can be deserialized
                    Resource(**structured_resource_response)
                    break
                i += 1
            except ValidationError:
                log("process_table", "Regenerating ")
                i += 1

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
            "trace_timestamp": datetime.now()
        }

        traces.append(new_trace)
        resources.append(structured_resource_response)

    return {
        "resources":resources,
        "trace": traces
    }

def generate_api(state:State):
    send = state.get("send")
    log("generate_api", "Started", send)
    resources = state.get("resources", [])
    added_sources = []
    if resources:
        api_template = read_python_code_template("api.py")
        for resource in resources:
            api_routes = resource["api_route"]
            for route in api_routes:
                uri = route["uri"]
                resource_object = route["resource_object"]
                module_name = resource["resource_file_name"].replace(".py","")
                library_name = resource_object.replace("()","")
                if module_name+"."+library_name not in added_sources:
                    api_template = api_template.replace("###IMPORTS###", f"###IMPORTS###\nfrom {module_name} import {library_name}")
                    added_sources.append(module_name+"."+library_name)
                if uri+"."+resource_object not in added_sources:
                    api_template = api_template.replace("###ENDPOINTS###", f"""###ENDPOINTS###\napp.add_route("{uri}", {resource_object})""")
                    added_sources.append(uri+"."+resource_object)

    save_python_code(
        api_template,
        "api.py"
    )

    #somehow do this once
    static = read_python_code_template("static.py")
    utils = read_python_code_template("utils.py")
    save_python_code(static, "static.py")
    save_python_code(utils, "utils.py")
    create_schemas_endpoint(state)
    commit_and_push_changes(
        message="Codes and api generated."
    )


    new_trace = {
        "node_name": "generate_api",
        "node_type": "process",
        "node_input": state["resources"],
        "node_output": api_template,
        "trace_timestamp": datetime.now(),
        "description": "APIs are generated. You can take a look by clicking Start under Server Controls (on the left). I am still going to run tests."
    }

    return {
        "trace": [new_trace]
    }

def send_message(message):
    print(f"{message}")

def run_workflow(task=None, db_config=None, send=None):
    if send is None:
        send = send_message

    if db_config:
        os.environ["DB_NAME"] = db_config["DB_NAME"]
        os.environ["DB_USER"] = db_config["DB_USER"]
        os.environ["DB_PASSWORD"] = db_config["DB_PASSWORD"]
        os.environ["DB_HOST"] = db_config["DB_HOST"]
        os.environ["DB_PORT"] = db_config["DB_PORT"]
    
    db_test_result = test_db(db_user=os.environ["DB_USER"],
                             db_password=os.environ["DB_PASSWORD"],
                             db_host=os.environ["DB_HOST"],
                             db_port=os.environ["DB_PORT"],
                             db_name=os.environ["DB_NAME"])
    if not db_test_result:
        send({
            "status":"error",
            "text": "Database connection failed. Please check your database configuration.",
            "name": "Database Connection Error"
        })
         
         
    
    graph = StateGraph(State)

    # nodes
    graph.add_node("router_node", router_node)

    graph.add_node("generate_prompt_for_code_generation", generate_prompt_for_code_generation)
    # graph.add_node("process_table", process_table)
    # graph.add_node("_process_table", _process_table)
    graph.add_node("generate_api", generate_api)

    graph.add_node("test_node", test_node)
    graph.add_node("report_node", report_node)


    #workflow logic
    graph.add_edge(START, "router_node")
    graph.add_conditional_edges(
        "router_node", lambda state: state["next_node"], {"generate_prompt_for_code_generation":"generate_prompt_for_code_generation", "test_node": "test_node", "report_node": "report_node", "__end__":END}
    )
    if parallel:
        graph.add_node("process_table", process_table)
        graph.add_conditional_edges(
            "generate_prompt_for_code_generation", lambda state: [Send("process_table", s) for s in state["DBSchema"]["tables"]], ["process_table"]
        )
    else:
        graph.add_node("process_table", _process_table)
        graph.add_edge(
            "generate_prompt_for_code_generation","process_table"
        )
    # graph.add_edge("generate_prompt_for_code_generation", "_process_table")
    graph.add_edge("process_table", "generate_api")
    graph.add_edge("generate_api", "router_node")
    graph.add_edge("test_node", "router_node")
    graph.add_edge("report_node", "router_node")


    #Compiling the graph
    workflow = graph.compile()

    #Running the workflow:
    if not task:
        task = "Created crud operations for passes, satellites, ground stations and orbits"
        #task = "Created crud operations for all the tables"

    # state = retrieve_state(state_file_name="after_test_2025-05-13_15-05-39.pkl", reset_tests=False)
    for event in workflow.stream({"messages": [HumanMessage(task)], "send":send}): #workflow.stream(state):
        name = ""
        text = ""
        key = list(event.keys())[0]
        if "trace" in event[key]:
            if "description" in event[key]["trace"][-1]:
                name = event[key]["trace"][-1]["node_name"]
                text = event[key]["trace"][-1]["description"]
                send({
                    "status":"processing",
                    "text":text,
                    "name":name,
                    "level":"workflow"
                })
    send({
        "status":"done",
        "text":"Task completed.",
        "name":"Workflow",
        "level":"workflow"
    })
    
    #Running workflow with a state
    # result_state = workflow.invoke(retrieve_state(reset_tests=False, state_file_name="after_test_2025-05-07_14-31-48.pkl"))


    # display(Image(workflow.get_graph().draw_mermaid_png(output_file_path="workflow.png")))


if __name__ == "__main__":
    for result in run_workflow():
        print(result)