from datetime import datetime

from revolve.db import get_adapter
from revolve.data_types import State
from revolve.functions import save_state, log
from revolve.utils_git import init_or_attach_git_repo, create_branch_with_timestamp
from revolve.external import get_db_type


def router_node(state: State):
    next_node = state.get("next_node", None)
    test_status = state.get("test_status", None)
    resources = state.get("resources", None)
    dbSchema = state.get("DBSchema", None)

    send = state.get("send")
    test_mode = state.get("test_mode", False)
    adapter = get_adapter(get_db_type())

    if not next_node:
        if test_mode:
            adapter.clone_db()

        init_or_attach_git_repo()
        branch_name = create_branch_with_timestamp()
        log(f"Branch created: {branch_name}", send)
        log("defaulting to generate_prompt_for_code_generation", send)
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

        log("Routing to test_node", send)
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
        log("Routing to report_node")
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
        log("routing to END", send)
        return {
            "next_node": "__end__",
        }
