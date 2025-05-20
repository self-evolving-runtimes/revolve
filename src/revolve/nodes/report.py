
from datetime import datetime
import os
from revolve.data_types import Readme, State
from revolve.functions import read_python_code, save_python_code
from revolve.prompts import get_readme_prompt
from revolve.utils import create_ft_data, create_test_report
from revolve.external import get_source_folder
from revolve.utils_git import commit_and_push_changes

from revolve.llm import invoke_llm


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
    
    env_file = open(f"{get_source_folder()}/.env", "w")
    env_file.write(f"DB_NAME={os.environ['DB_NAME']}\n")
    env_file.write(f"DB_USER={os.environ['DB_USER']}\n")
    env_file.write(f"DB_PASSWORD={os.environ['DB_PASSWORD']}\n")
    env_file.write(f"DB_HOST={os.environ['DB_HOST']}\n")
    env_file.write(f"DB_PORT={os.environ['DB_PORT']}\n")
    env_file.close()
    api_code = read_python_code("api.py")

    messages = get_readme_prompt(api_code)
    
    readme_result = invoke_llm(
        messages,
        max_attempts=3,
        validation_class=Readme,
        method="function_calling"
    )


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
