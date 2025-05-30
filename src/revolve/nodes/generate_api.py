
from datetime import datetime
from revolve.data_types import State
from revolve.utils import log, read_python_code_template, save_python_code, copy_template_files_to_source_folder
from revolve.utils import create_schemas_endpoint
from revolve.utils_git import commit_and_push_changes

def generate_api(state:State):
    send = state.get("send")
    log("Started", send)
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

    template_files = [
        "static.py",
        "db_utils.py",
        "cors.py"
    ]
    copy_template_files_to_source_folder(template_files)

    create_schemas_endpoint(state)
    commit_and_push_changes(
        message="Codes and api generated."
    )


    new_trace = {
        "node_name": "generate_api",
        "node_type": "process",
        "node_input": state["resources"],
        "node_output": api_template,
        "trace_timestamp": datetime.now(),
        "description": "APIs are generated. You can take a look by clicking Start under Server Controls (on the left). I am still going to run tests."
    }

    log("APIs are generated. You can take a look by clicking Start under Server Controls (on the left). I am still going to run tests.", send=send, level="notification") 

    return {
        "trace": [new_trace]
    }
