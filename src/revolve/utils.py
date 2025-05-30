import inspect
import json
import random
import subprocess
import sys
import time
import os

from revolve.data_types import State
from revolve.external import get_source_folder, get_db_type

from loguru import logger

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time} | {level} | {message}")
def make_serializable(obj):
    if hasattr(obj, '__dict__'):
        return {k: make_serializable(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(v) for v in obj]
    else:
        return obj

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
    api_code = api_code.replace("###IMPORTS###", "###IMPORTS###\nfrom schemas import SchemasResource")
    api_code = api_code.replace("###ENDPOINTS###", "###ENDPOINTS###\napp.add_route('/schemas', SchemasResource())")
    save_python_code(
        api_code,
        "api.py"
    )


def create_ft_data(state):
    test_status = state.get("test_status", {})
    samples = []
    samples_json = []
    for test_sample in test_status:
        if test_sample["status"] == "success":
            if test_sample["iteration_count"]==0:
                samples.append(test_sample["test_generation_input_prompt"])
            else:
                samples.append(test_sample["code_history"][-1]["test_revising_input_prompt"])

    if len(samples)>0:
        samples_json = make_serializable(samples)
        with open(f"{get_source_folder()}/ft_data.json", "w") as f:
            json.dump(samples_json, f, indent=4)
        
        if os.path.exists("ft"):        
            file_name_with_time = f"ft/ft_data_{int(time.time())}.json"
            with open(file_name_with_time, "w") as f:
                json.dump(samples_json, f, indent=4)
        
    return samples, samples_json


def create_report_json(state):
    test_status = state.get("test_status", {})
    test_status_json = make_serializable(test_status)
    with open(f"{get_source_folder()}/test_status_history.json", "w") as f:
        json.dump(test_status_json, f, indent=4)
    
    return test_status, test_status_json    

def create_test_report(task,state):

    test_status, _ = create_report_json(state)
    output_path = f"{get_source_folder()}/test_status_report.md"

    with open(output_path, "w") as f:
        f.write("# Test Report\n\n")
        f.write(f"## Task: {task}\n\n")
        
        for test_item in test_status:
            f.write("---\n")
            f.write(f"### 📄 {test_item['resource_file_name']}\n")
            f.write(f"- **Test Status:** `{test_item['status']}`\n")
            f.write(f"- **Iteration Count:** `{test_item['iteration_count']}`\n\n")
            f.write("- **Test Summary:**\n")
            if "code_history" in test_item and len(test_item['code_history']) > 0:
                last_test = test_item['code_history'][-1]
                last_summary = last_test['test_report_after_revising']["summary"]
                for key, value in last_summary.items():
                    if key =="failed_tests":
                        f.write(f"  - **{key}:**\n")
                        for test in value:
                            f.write(f"    - `{test}`\n")
                    else:
                        f.write(f"  - **{key}:** `{value}`\n")



process_state = {
    "pid": None,
    "port": None,
    "link": None
}

def start_process():

    # get directory of current file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    resources = current_dir + "/" + "resources"



    if process_state["pid"] is not None:
        return {"message": f"Server already running at {process_state['link']}"}

    COMMAND = ["python", "api.py"]  
    env_vars = os.environ.copy()
    port = os.environ.get("PORT", str(random.randint(1024, 65535)))
    env_vars["PORT"] = port
    #get current directory


    env_vars["STATIC_DIR"] = env_vars.get("STATIC_DIR", resources)

    try:
        code_dir = f"{get_source_folder()}"
        process = subprocess.Popen(COMMAND, cwd=code_dir, env=env_vars)
        process_state["pid"] = process.pid
        process_state["port"] = port
        process_state["link"] = f"http://localhost:{port}"
        return {"message": f"External server started at {process_state['link']}"}
    except Exception as e:
        return {"error": f"Failed to start external process: {e}"}

def stop_process():
    pid = process_state.get("pid")
    if pid:
        try:
            os.kill(pid, 9)
            process_state["pid"] = None
            process_state["port"] = None
            process_state["link"] = None
            return {"message": f"Process with PID {pid} stopped"}
        except Exception as e:
            return {"error": f"Failed to stop process: {e}"}
    else:
        return {"message": "No process is running"}


def save_python_code(python_code: str, file_name: str) -> str:
    """
    This functions saves the generated python code.
    Args:
        python_code (str): Python code to be saved.
        file_name (str): The name of the file to be saved.
    """

    # create the directory if it doesn't exist
    os.makedirs(f"{get_source_folder()}", exist_ok=True)

    # log("save_python_code", f"Saving python code to file: {file_name}")
    python_code = python_code.encode("utf-8").decode("unicode_escape")
    try:
        with open(f"{get_source_folder()}/{file_name}", "w") as f:
            f.write(python_code)
    except Exception as e:
        log(f"Error saving python code: {e}")
        return f"Error saving python code: {e}"

    log(f"Python code saved successfully to {file_name}.")
    return f"Python code saved to {file_name} successfully."


def read_python_code(file_name: str) -> str:
    """
    This function returns the generated python code from the given file name.
    Args:
        file_name (str): The name of the file to be read.
    """
    # log("get_python_code", f"Getting python code from file: {file_name}")
    try:
        with open(f"{get_source_folder()}/{file_name}", "r") as f:
            python_code = f.read()
    except Exception as e:
        log(f"Error getting python code: {e}")
        return f"Error getting python code: {e}"

    # log("get_python_code", f"Python code retrieved successfully.")
    return python_code


def read_python_code_template(file_name: str) -> str:
    """
    " This function reads the template python code from the given file name.
     Args:
         file_path (str): The path to the template file.
    """
    # log("read_python_code_template", f"Getting python code from file: {file_name}")
    db_dependent_files = ["service.py","db_utils.py"]
    try:
        if file_name in db_dependent_files:
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "source_template", get_db_type(), file_name)
        else:
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "source_template", file_name)

        with open(file_path, "r") as f:
            python_code = f.read()
    except Exception as e:
        log(f"Error getting python code: {e}")
        return f"Error getting python code: {e}"

    # log("read_python_code_template", f"Python code retrieved successfully.")
    return python_code

def copy_template_files_to_source_folder(file_names):
    """
    This function copies the files from the template folder to the source folder.
    """
    for file_name in file_names:
        file_content = read_python_code_template(file_name)
        save_python_code(file_content, file_name)

def _log(method_name, description, level="INFO"):
    logger.log(level, f"{method_name:<20} - {description:<30}")


def log(description, send=None, level="system"):
    method_name = inspect.currentframe().f_back.f_code.co_name
    if send:
        send({
            "name": method_name,
            "text": description,
            "status": "processing",
            "level": level}
        )
    _log(method_name, description)
