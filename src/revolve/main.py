import ast
from langchain_core.messages import AnyMessage
from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, START, END
# from IPython.display import Image, display
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.revolve.data_types import State, DBSchema, Table, Resource, NextNode, GeneratedCode, RevisedCode
from langchain_openai import ChatOpenAI
from src.revolve.functions import run_query_on_db, read_python_code, read_python_code_template, save_python_code, log, save_state, retrieve_state, run_pytest
from src.revolve.prompts import get_simple_prompt
from datetime import datetime
from langgraph.constants import Send
import pickle
from src.revolve.utils_git import *

#OPENAI
llm  = ChatOpenAI(model="gpt-4.1", temperature=0.2, max_tokens=16000)

# LLM - RUNPOD
# llm  = ChatOpenAI(model="Qwen/Qwen3-30B-A3B", temperature=0.1, max_tokens=16000, base_url="http://localhost:8000/v1/", api_key="no_needed")

# LLM - Local Ollama
# llm  = ChatOpenAI(model="qwen3:30b-a3b", temperature=0.1, max_tokens=7000, base_url="http://localhost:11434/v1/", api_key="ollama")



llm_router = llm.with_structured_output(NextNode, method="function_calling")
llm_table_extractor = llm.with_structured_output(DBSchema, method="function_calling")
llm_resource_generator = llm.with_structured_output(Resource, method="function_calling")
llm_test_generator = llm.with_structured_output(GeneratedCode, method="function_calling")
llm_test_and_code_reviser = llm.with_structured_output(RevisedCode, method="function_calling")

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
    if not next_node:

        init_or_attach_git_repo()
        branch_name = create_branch_with_timestamp()
        log("router_node", f"Branch created: {branch_name}")

        log("router_node", "defaulting to generate_prompt_for_code_generation")
        return {
            "next_node": "generate_prompt_for_code_generation",
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
            new_test["code_history"] = [res["resource_code"]]
            new_test["iteration_count"] = 0
            new_test["table"] = table_object
            test_status.append(new_test)
                    
        log("router_node", f"Routing to test_node")
        return {
            "next_node": "test_node",
            "test_status": test_status
        }
    else:
        save_state(state, "after_test")
        log("router_node", f"routing to END")
        return {
            "next_node": "__end__",
        }



def test_node(state: State):
    test_example = read_python_code_template("test_api.py")
    api_code = read_python_code("api.py")
    for test_item in state["test_status"]:
        resouce_file = read_python_code(test_item["resource_file_name"])
        test_file_name = "test_"+test_item["resource_file_name"]
        table_name = test_item["table"]["table_name"]
        schema = str(test_item["table"]["columns"])
        system_message = f"""You are responsible for writing the test cases for the given code.
        Follow the same pattern as the example test file. Do not add any extarnal libraries.
        Always print the response content in the test for better debugging.
        Be careful with non-nullable columns when generating tests.
        Don't assume any id is already in the database.
        Do not use placeholder values, everything should be ready to use.
        Example test file should be like this:
        {test_example}"""
        
        user_message = f"""Here is my api code for the endpoints.
        {api_code}
        Here are the schema of the table ({table_name}) is used in the api:
        {schema}
        Write test methods foreach function in the resource code:
        {resouce_file}"""

        messages = [
            {
                "role": "system",
                "content": system_message
            },
            {
                "role": "user",
                "content": user_message
            }
        ]

        structured_test_response = llm_test_generator.invoke(messages)
        messages.append(
            {
                "role": "assistant",
                "content": structured_test_response["full_test_code"]
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

        for i in range(10):
            test_item["status"] = "in_progress"
            pytest_response  = run_pytest(test_file_name)
            if pytest_response["status"]!= "success":
                test_item["status"] = "failed"
                new_system_message = f"""You are responsible for fixing the errors.
                Fix the test or the source code according to the test report provided by user.
                You are responsible for writing the test cases for the given code.
                Do not add any extarnal libraries.
                Always print the response content in the test for better debugging.
                Be careful with non-nullable columns when generating tests.
                Don't assume any id is already in the database.
                Do not use placeholder values, everything should be ready to use."""
                individual_prompt = test_item["table"]["individual_prompt"]
                source_code = read_python_code(test_item["resource_file_name"])
                test_code = read_python_code(test_file_name)
                example_resource_code = read_python_code_template("service.py")
                new_user_message = f"""My initial goal was {individual_prompt}.
                However some tests are failing. 
                Please fix the test or the resource code, which one is needed.
                I only need the code, do not add any other comments or explanations.
                Here is the resource code :
                {source_code}
                This is the example resource code in case you need to refer:
                {example_resource_code}
                Here is the test code:
                {test_code}
                The api and routes are here:
                {api_code}
                The schema of the related {table_name} table is:
                {schema}
                And Here is the report of the failing tests:
                {pytest_response}"""
                
                # messages.append(
                #     {
                #         "role": "user",
                #         "content": new_user_message
                #     }
                # )

                new_messages = [
                    {
                        "role": "system",
                        "content": new_system_message
                    },
                    {
                        "role": "user",
                        "content": new_user_message
                    }
                ]

                test_item["iteration_count"] += 1
                new_test_code_response = llm_test_and_code_reviser.invoke(new_messages)
                messages.append(
                    {
                        "role": "assistant",
                        "content": str(new_test_code_response)
                    }
                )
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
                commit_and_push_changes(
                    message=f"Code revised for {file_name_to_revise}",
                    description=new_test_code_response.what_fixed
                )
                
                test_item["code_history"].append(new_test_code_response.new_code)
           
                # else:
                #     messages.append(
                #         {
                #             "role": "user",
                #             "content": "Your output is not valid. Please follow the json format."
                #         }
                #     )
                        
            else:
                test_item["status"] = "success"
                break

        test_item["messages"] = messages   

    return {"test_status": state["test_status"]}

def do_other_stuff(state: State):
    return {}

def generate_prompt_for_code_generation(state: State):
    log("generate_prompt_for_code_generation", "Started")
    last_message_content = state["messages"][-1].content
    schemas = run_query_on_db("""SELECT jsonb_object_agg(
            table_name,
            columns
        ) AS schema_dict
    FROM (
        SELECT
            table_name,
            jsonb_agg(
                jsonb_build_object(
                    'column_name', column_name,
                    'data_type', data_type,
                    'is_nullable', is_nullable
                )
            ) AS columns
        FROM information_schema.columns
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        GROUP BY table_name
    ) AS sub;""")

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
    
    structured_db_response = llm_table_extractor.invoke(messages)
    trace = state.get("trace", [])
    trace.append({
        "node_name": "generate_prompt_for_code_generation",
        "node_type": "db",
        "node_input": last_message_content,
        "node_output": "place_holder",
        "trace_timestamp": datetime.now()
    })

    log("generate_prompt_for_code_generation", "Completed")

    return {
        "DBSchema": structured_db_response,
        "trace": trace,
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

    system_prompt = f"""Generate resource code according to the user request.
    Make sure that you write production quality code that can be maintained by developers.
    Requests should be trackable with logs in INFO mode. Double check the imports.
    Make sure that you check whether data is serializable and convert data when needed.
    Guard against SQL injection attacks. Always sanitize inputs before sending it to database.
    While creating List functionality, provide functionality to sort, order by and filter based on
    key columns. If the search filter is a date field, provide functionality to match greater than,
    less than and equal to date. Filter may not be specified - handle those cases as well.
    There could be multiple endpoints for the same resource.
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
    structured_resource_response = llm_resource_generator.invoke(messages)
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
        Make sure that you write production quality code that can be maintained by developers.
        Requests should be trackable with logs in INFO mode. Double check the imports.
        Make sure that you check whether data is serializable and convert data when needed.
        Guard against SQL injection attacks. Always sanitize inputs before sending it to database.
        While creating List functionality, provide functionality to sort, order by and filter based on
        key columns. If the search filter is a date field, provide functionality to match greater than,
        less than and equal to date. Filter may not be specified - handle those cases as well.
        There could be multiple endpoints for the same resource.
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
        structured_resource_response = llm_resource_generator.invoke(messages)
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
    log("generate_api", "Started")
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
    commit_and_push_changes(
        message="Codes and api generated."
    )
    new_trace = {
        "node_name": "generate_api",
        "node_type": "process",
        "node_input": state["resources"],
        "node_output": api_template,
        "trace_timestamp": datetime.now()
    }
    return {
        "trace": [new_trace]
    }

if __name__== "__main__":

    graph = StateGraph(State)

    # nodes
    graph.add_node("router_node", router_node)

    graph.add_node("generate_prompt_for_code_generation", generate_prompt_for_code_generation)
    graph.add_node("process_table", process_table)
    # graph.add_node("_process_table", _process_table)
    graph.add_node("generate_api", generate_api)

    graph.add_node("test_node", test_node)
    graph.add_node("do_other_stuff", do_other_stuff)


    #workflow logic
    graph.add_edge(START, "router_node")
    graph.add_conditional_edges(
        "router_node", lambda state: state["next_node"], {"generate_prompt_for_code_generation":"generate_prompt_for_code_generation", "test_node": "test_node", "do_other_stuff": "do_other_stuff", "__end__":END}
    )
    graph.add_conditional_edges(
        "generate_prompt_for_code_generation", lambda state: [Send("process_table", s) for s in state["DBSchema"]["tables"]], ["process_table"]
    )
    # graph.add_edge("generate_prompt_for_code_generation", "_process_table")
    graph.add_edge("process_table", "generate_api")
    graph.add_edge("generate_api", "router_node")
    graph.add_edge("test_node", "router_node")
    graph.add_edge("do_other_stuff", "router_node")


    #Compiling the graph
    workflow = graph.compile()

    #Running the workflow:
    # task = "Create crud operations for all the tables in db"
    task = "Created crud operations for the owners and watch history table"
    result_state = workflow.invoke({"messages": [HumanMessage(task)]})

    #Running workflow with a state
    # result_state = workflow.invoke(retrieve_state())


    # display(Image(workflow.get_graph().draw_mermaid_png(output_file_path="workflow.png")))

