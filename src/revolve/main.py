from langgraph.graph import StateGraph, START, END

from revolve.data_types import State
from revolve.db import get_adapter

from langgraph.constants import Send
from revolve.utils_git import *

import os


from revolve.nodes import (
    router_node,
    generate_prompt_for_code_generation,
    process_table,
    generate_api,
    test_node,
    report_node,
    check_user_request,
    tool_handler,
    BasicToolNode,
    should_continue_tool_call
)

from revolve.external import get_db_type
from revolve.tools import get_tools


def send_message(message):
    print(f"{message}")

def run_workflow(task=None, db_config=None, send=None):
    if send is None:
        send = send_message
    test_mode = True if db_config and db_config.get("USE_CLONE_DB", False) else False
    if db_config:
        os.environ["DB_NAME"] = db_config["DB_NAME"]
        os.environ["DB_USER"] = db_config["DB_USER"]
        os.environ["DB_PASSWORD"] = db_config["DB_PASSWORD"]
        os.environ["DB_HOST"] = db_config["DB_HOST"]
        os.environ["DB_PORT"] = db_config["DB_PORT"]
        os.environ["DB_TYPE"] = db_config["DB_TYPE"]

    adapter = get_adapter(get_db_type())

    db_test_result = adapter.check_db(db_user=os.environ["DB_USER"],
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
    graph.add_node("check_user_request", check_user_request)
    graph.add_node("generate_prompt_for_code_generation", generate_prompt_for_code_generation)
    graph.add_node("process_table", process_table)
    graph.add_node("generate_api", generate_api)
    graph.add_node("test_node", test_node)
    graph.add_node("report_node", report_node)
    graph.add_node("tool_handler", tool_handler)

    tool_executor = BasicToolNode(tools=get_tools())
    graph.add_node("tool_executor", tool_executor)



    graph.add_edge(START, "check_user_request")
    graph.add_conditional_edges("check_user_request", lambda state: state["classification"], {"create_crud_task" : "router_node",  "__end__":END, "respond_back": END, "other_tasks":"tool_handler"})
    graph.add_conditional_edges(
        "router_node", lambda state: state["next_node"], {"generate_prompt_for_code_generation":"generate_prompt_for_code_generation", "test_node": "test_node", "report_node": "report_node", "__end__":END}
    )

    graph.add_conditional_edges(
        "tool_handler", should_continue_tool_call, {"tool_executor": "tool_executor", "__end__": END}
    )
    graph.add_edge("tool_executor", "tool_handler")


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
        task = [
            {
                "role": "user",
                "content": "Create CRUD operations for passes, satellites, ground stations and orbits."
            }
        ]

    for event in workflow.stream({"messages": task, "send":send,"test_mode": test_mode}):
        name = ""
        text = ""
        key = list(event.keys())[0]
        if event[key]:
            if "trace" in event[key]:
                if "description" in event[key]["trace"][-1]:
                    name = event[key]["trace"][-1]["node_name"]
                    text = event[key]["trace"][-1]["description"]
                    level = "workflow" if name in ["report_node","run_tests"] else "system"
                    send({
                        "status":"processing",
                        "text":text,
                        "name":name,
                        "level":level
                    })
    # send({
    #     "status":"done",
    #     "text":"Task completed.",
    #     "name":"Workflow",
    #     "level":"workflow"
    # })
    
if __name__ == "__main__":
    run_workflow()
