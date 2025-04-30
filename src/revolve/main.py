import ast
from langchain_core.messages import AnyMessage
from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.revolve.data_types import State, DBSchema, Table, Resource, NextNode
from langchain_openai import ChatOpenAI
from src.revolve.functions import run_query_on_db
from src.revolve.prompts import get_simple_prompt
from datetime import datetime
from langgraph.constants import Send

llm  = ChatOpenAI(model="gpt-4o", temperature=0.1)
llm_table_extractor = llm.with_structured_output(DBSchema)
llm_resource_generator = llm.with_structured_output(Resource)
llm_router = llm.with_structured_output(NextNode)

def router_node(state: State):
    
    # ---------------------------------------
    # ROUTE with LLM Decisions like an Agent, we can use the LLM to decide the next step
    # messages = [
    #     {
    #         "role": "system",
    #         "content": "Based on user request select the next path to take. The options are: get_table_makeup_from_prompt, do_stuff, do_other_stuff. If none of these options are relevant, return __end__."
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
            "next_node": "get_table_makeup_from_prompt",
        }
    else:
        return {
            "next_node": "__end__",
        }

def do_stuff(state: State):
    return {}

def do_other_stuff(state: State):
    return {}

def get_table_makeup_from_prompt(state: State):


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
        "node_name": "get_table_makeup_from_prompt",
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
    """Process a table to extract its columns and types"""
    table_name = table_state["table_name"]

    columns = table_state["columns"]
    print(f"Table: {table_name}")
    for col in columns:
        print(f"Table Name : {table_name}, Column: {col['column']}, Type: {col['type']}, Is Nullable: {col['is_nullable']}")


    new_trace = {
        "node_name": "process_table",
        "node_type": "process",
        "node_input": table_name,
        "node_output": "place_holder",
        "trace_timestamp": datetime.now()
    }

    return {
        "trace": [new_trace],
    }


graph = StateGraph(State)

# nodes
graph.add_node("router_node", router_node)
graph.add_node("get_table_makeup_from_prompt", get_table_makeup_from_prompt)
graph.add_node("process_table", process_table)
graph.add_node("do_stuff", do_stuff)
graph.add_node("do_other_stuff", do_other_stuff)


#workflow logic
graph.add_edge(START, "router_node")
graph.add_conditional_edges(
    "router_node", lambda state: state["next_node"], {"get_table_makeup_from_prompt":"get_table_makeup_from_prompt", "do_stuff": "do_stuff", "do_other_stuff": "do_other_stuff", "__end__":END}
)
graph.add_conditional_edges(
    "get_table_makeup_from_prompt", lambda state: [Send("process_table", s) for s in state["DBSchema"]["tables"]], ["process_table"]
)
graph.add_edge("process_table", "router_node")
graph.add_edge("do_stuff", "router_node")
graph.add_edge("do_other_stuff", "router_node")


#Compiling the graph
workflow = graph.compile()
display(Image(workflow.get_graph().draw_mermaid_png(output_file_path="workflow.png")))

#Running the workflow
task = "Create crud operations for the tables related to the hospital"
result_state = workflow.invoke({"messages": [HumanMessage(task)]})

