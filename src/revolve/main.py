import ast
from langchain_core.messages import AnyMessage
from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.revolve.data_types import State, DBSchema, Table, Resource, NextNode
from langchain_openai import ChatOpenAI
from src.revolve.functions import run_query_on_db, read_python_code, read_python_code_template, save_python_code
from src.revolve.prompts import get_simple_prompt
from datetime import datetime
from langgraph.constants import Send

llm  = ChatOpenAI(model="gpt-4o", temperature=0.1, max_tokens=16000)

llm_router = llm.with_structured_output(NextNode)
llm_table_extractor = llm.with_structured_output(DBSchema)
llm_resource_generator = llm.with_structured_output(Resource)

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
    if not next_node:
        return {
            "next_node": "generate_prompt_for_code_generation",
        }
    else:
        return {
            "next_node": "__end__",
        }

def do_stuff(state: State):
    return {}

def do_other_stuff(state: State):
    return {}

def generate_prompt_for_code_generation(state: State):


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

    return {
        "DBSchema": structured_db_response,
        "trace": trace,
    }

def process_table(table_state:Table):
    table_name = table_state["table_name"]
    columns = table_state["columns"]
    # print(f"Table: {table_name}")
    # print("User Prompt: ", table_state["individual_prompt"])
    # for col in columns:
    #     print(f"Table Name : {table_name}, Column: {col['column']}, Type: {col['type']}, Is Nullable: {col['is_nullable']}")

    api_template = read_python_code_template("api.py")
    code_template = read_python_code_template("service.py")
    test_template = read_python_code_template("test_api.py")

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

def generate_api(state:State):
    resources = state.get("resources", [])
    if resources:
        api_template = read_python_code_template("api.py")
        for resource in resources:
            api_routes = resource["api_route"]
            import_counter = 0
            for route in api_routes:
                uri = route["uri"]
                resource_object = route["resource_object"]
                module_name = resource["resource_file_name"].replace(".py","")
                library_name = resource_object.replace("()","")
                if import_counter==0:
                    api_template = api_template.replace("###IMPORTS###", f"###IMPORTS###\nfrom {module_name} import {library_name}")
                import_counter += 1
                api_template = api_template.replace("###ENDPOINTS###", f"""###ENDPOINTS###\napp.add_route("{uri}", {resource_object})""")

    save_python_code(
        api_template,
        "api.py"
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
graph = StateGraph(State)

# nodes
graph.add_node("router_node", router_node)

graph.add_node("generate_prompt_for_code_generation", generate_prompt_for_code_generation)
graph.add_node("process_table", process_table)
graph.add_node("generate_api", generate_api)

graph.add_node("do_stuff", do_stuff)
graph.add_node("do_other_stuff", do_other_stuff)


#workflow logic
graph.add_edge(START, "router_node")
graph.add_conditional_edges(
    "router_node", lambda state: state["next_node"], {"generate_prompt_for_code_generation":"generate_prompt_for_code_generation", "do_stuff": "do_stuff", "do_other_stuff": "do_other_stuff", "__end__":END}
)
graph.add_conditional_edges(
    "generate_prompt_for_code_generation", lambda state: [Send("process_table", s) for s in state["DBSchema"]["tables"]], ["process_table"]
)
graph.add_edge("process_table", "generate_api")
graph.add_edge("generate_api", "router_node")
graph.add_edge("do_stuff", "router_node")
graph.add_edge("do_other_stuff", "router_node")


#Compiling the graph
workflow = graph.compile()

#Running the workflow
task = "Create crud operations for the tables related to the hospital"
result_state = workflow.invoke({"messages": [HumanMessage(task)]})

display(Image(workflow.get_graph().draw_mermaid_png(output_file_path="workflow.png")))

