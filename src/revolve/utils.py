import json
import random
import subprocess
import time
import os

from revolve.data_types import State
from revolve.external import get_source_folder
from revolve.functions import read_python_code, read_python_code_template, save_python_code

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
    api_code = api_code.replace("###IMPORTS###", f"###IMPORTS###\nfrom schemas import SchemasResource")
    api_code = api_code.replace("###ENDPOINTS###", f"###ENDPOINTS###\napp.add_route('/schemas', SchemasResource())")
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
            f.write(f"- **Test Summary:**\n")
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
    if process_state["pid"] is not None:
        return {"message": f"Server already running at {process_state['link']}"}

    COMMAND = ["python", "api.py"]  
    env_vars = os.environ.copy()
    port = os.environ.get("PORT", str(random.randint(1024, 65535)))
    env_vars["PORT"] = port
    env_vars["STATIC_DIR"] = env_vars.get("STATIC_DIR", "-")

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