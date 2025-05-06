import json
def make_serializable(obj):
    if hasattr(obj, '__dict__'):
        return {k: make_serializable(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(v) for v in obj]
    else:
        return obj

def create_test_report(task,state):
    test_status = state.get("test_status", {})
    test_status_json = make_serializable(test_status)
    #save json into source_generated folder
    with open(f"src/revolve/source_generated/test_status_history.json", "w") as f:
        json.dump(test_status_json, f, indent=4)
    
    output_path = "src/revolve/source_generated/test_status_report.md"

    with open(output_path, "w") as f:
        f.write("# Test Report\n\n")
        f.write(f"## Task: {task}\n\n")
        
        for test_item in test_status:
            f.write("---\n")
            f.write(f"### 📄 {test_item['resource_file_name']}\n")
            f.write(f"- **Status:** `{test_item['status']}`\n")
            f.write(f"- **Iteration Count:** `{test_item['iteration_count']}`\n\n")


