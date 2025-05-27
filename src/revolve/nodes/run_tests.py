from datetime import datetime
from revolve.nodes import test_node
from revolve.functions import run_pytest, get_file_list, log
from revolve.prompts import get_run_test_prompt
from revolve.llm import invoke_llm

def run_tests(state):
    """
    Run tests for the resources in the state.
    """
    send = state.get("send")
    file_list = get_file_list()
    test_files = [file for file in file_list if file.startswith("test_") and file.endswith(".py")]

    test_reports = ""

    log("Running tests for the following files: " + ", ".join(test_files), send=send)
    for test_file in test_files:
        test_report = run_pytest(test_file)
        if not test_report:
            log(f"No tests found in {test_file}.", send=send)
            continue
        test_reports += f"\n\nTest report for {test_file}:\n{test_report}\n"
    
    messages = get_run_test_prompt(test_reports)

    response = invoke_llm(
        messages=messages,
        max_attempts=3,
    )

    new_trace = {
        "node_name": "run_tests",
        "node_type": "run_tests",
        "node_input": test_report,
        "node_output": "place_holder",
        "trace_timestamp": datetime.now(),
        "description": response.content,
    }

    return {
        "trace": [new_trace],
    }
    
 

