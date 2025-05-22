from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage

from revolve.data_types import State
from revolve.functions import test_db

from langgraph.constants import Send
from revolve.utils_git import *
from revolve.functions import clone_db
import os


from revolve.nodes import (
    router_node,
    generate_prompt_for_code_generation,
    process_table,
    generate_api,
    test_node,
    report_node
)


def send_message(message):
    print(f"{message}")

def run_workflow(task=None, db_config=None, send=None):
    if send is None:
        send = send_message
    test_mode = False
    if db_config:
        os.environ["DB_NAME"] = db_config["DB_NAME"]
        os.environ["DB_USER"] = db_config["DB_USER"]
        os.environ["DB_PASSWORD"] = db_config["DB_PASSWORD"]
        os.environ["DB_HOST"] = db_config["DB_HOST"]
        os.environ["DB_PORT"] = db_config["DB_PORT"]

        if db_config["USE_CLONE_DB"]:
            test_mode = True
            clone_db()

    
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
        return
         
         
    
    graph = StateGraph(State)

    graph.add_node("router_node", router_node)
    graph.add_node("generate_prompt_for_code_generation", generate_prompt_for_code_generation)
    graph.add_node("process_table", process_table)
    graph.add_node("generate_api", generate_api)
    graph.add_node("test_node", test_node)
    graph.add_node("report_node", report_node)



    graph.add_edge(START, "router_node")
    graph.add_conditional_edges(
        "router_node", lambda state: state["next_node"], {"generate_prompt_for_code_generation":"generate_prompt_for_code_generation", "test_node": "test_node", "report_node": "report_node", "__end__":END}
    )

    graph.add_conditional_edges(
        "generate_prompt_for_code_generation", lambda state: [Send("process_table", s) for s in state["DBSchema"]["tables"]], ["process_table"]
    )

    graph.add_edge("process_table", "generate_api")
    graph.add_edge("generate_api", "router_node")
    graph.add_edge("test_node", "router_node")
    graph.add_edge("report_node", "router_node")

    workflow = graph.compile()

    if not task:
        #task = "Created crud operations for passes, satellites, ground stations and orbits"
        task = "Created crud operations for orbits"

    for event in workflow.stream({"messages": [HumanMessage(task)], "send":send,"test_mode": test_mode}):
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
    
if __name__ == "__main__":
    run_workflow()
