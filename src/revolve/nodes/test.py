
from datetime import datetime
from revolve.data_types import CodeHistoryMessage, GeneratedCode, State
from revolve.utils import log, read_python_code, read_python_code_template, save_python_code
from revolve.functions import check_schema_for_unsupported_types, run_pytest
from revolve.prompts import get_test_generation_prompt, get_test_generation_prompt_ft, get_test_revising_prompt, get_test_revising_prompt_ft
from revolve.llm import invoke_llm
from revolve.utils import create_report_json
from revolve.utils_git import commit_and_push_changes


def test_node(state: State):
    send = state.get("send")
    MAX_TEST_ITERATIONS = 3
    test_example = read_python_code_template("test_api.py")
    utils = read_python_code_template("db_utils.py")
    api_code = read_python_code("api.py")
    for test_item in state["test_status"]:
        is_unsupported_type_exist = check_schema_for_unsupported_types(test_item["table"]["columns"])
        if is_unsupported_type_exist or not state["test_mode"]:
            log(f"Skipping test generation for {test_item['resource_file_name']}", send)
            test_item["status"] = "skipped"
            continue
        resouce_file = read_python_code(test_item["resource_file_name"])
        test_file_name = "test_"+test_item["resource_file_name"]
        log(f"Creating and testing for {test_file_name}", send)
        table_name = test_item["table"]["table_name"]
        schema = str(test_item["table"]["columns"])
        
        messages = get_test_generation_prompt(
            test_example=test_example,
            api_code=api_code,
            table_name=table_name,
            schema=schema,
            utils=utils,
            resouce_file=resouce_file,
            resource_file_name = test_item["resource_file_name"]
        )
        messages_ft = get_test_generation_prompt_ft(
            test_example=test_example,
            api_code=api_code,
            table_name=table_name,
            schema=schema,
            utils=utils,
            resouce_file=resouce_file,
            resource_file_name = test_item["resource_file_name"]
        )

        structured_test_response = invoke_llm(messages, max_attempts=3, validation_class=GeneratedCode, method="function_calling", manual_validation=True)
        full_test_code = structured_test_response.full_test_code


        messages_ft.append(
            {
                "role": "assistant",
                "content": structured_test_response.json(),
            }
        )


        test_item["test_code"] = structured_test_response.full_test_code
        test_item["test_file_name"] = test_file_name
        save_python_code(
            structured_test_response.full_test_code,
            test_file_name
        )
        commit_and_push_changes(
            message=f"Test code generated for {test_item['resource_file_name']}"
        )
        pytest_response  = run_pytest(test_file_name)
        test_item["status"] = pytest_response["status"]

        test_item["code_history"] = test_item.get("code_history", [])
        code_history_item = {
            "history_type": "creation",
            "code": {
                "new_code": "N/A",
                "what_was_the_problem": "N/A",
                "what_is_fixed": "N/A",
                "code_type": "N/A"
            },
            "test_report_before_revising": None,
            "test_report_after_revising": pytest_response,
            "iteration_index": 0
        }
        test_item["code_history"].append(code_history_item)
        test_item["test_generation_input_prompt"] = messages_ft

        for i in range(MAX_TEST_ITERATIONS):

            #get the previous code history and add pytest_response to the test_report_after_revising
            if pytest_response["status"]!= "success":
                test_item["status"] = "failed"
        

                individual_prompt = test_item["table"]["individual_prompt"]
                source_code = read_python_code(test_item["resource_file_name"])
                test_code = read_python_code(test_file_name)
                example_resource_code = read_python_code_template("service.py")
                
                new_messages = get_test_revising_prompt(
                    individual_prompt=individual_prompt,
                    source_code=source_code,
                    example_resource_code=example_resource_code,
                    test_code=test_code,
                    api_code=api_code,
                    table_name=table_name,
                    schema=schema,
                    utils=utils,
                    pytest_response=pytest_response,
                    resource_file_name = test_item["resource_file_name"]
                )

                new_messages_ft  = get_test_revising_prompt_ft(
                    individual_prompt=individual_prompt,
                    source_code=source_code,
                    example_resource_code=example_resource_code,
                    test_code=test_code,
                    api_code=api_code,
                    table_name=table_name,
                    schema=schema,
                    utils=utils,
                    pytest_response=pytest_response,
                    resource_file_name = test_item["resource_file_name"]
                )


                
                new_test_code_response = invoke_llm(new_messages, max_attempts=3, validation_class=CodeHistoryMessage, method="function_calling", manual_validation=True)
                test_item["iteration_count"] += 1

                if new_test_code_response.code_type == "resource":
                    file_name_to_revise = test_item["resource_file_name"]
                elif new_test_code_response.code_type == "test":
                    file_name_to_revise = test_file_name
                else:
                    file_name_to_revise = "api.py"

                save_python_code(
                    new_test_code_response.new_code,
                    file_name_to_revise
                )
                commit_description = f"""What was the problem: {new_test_code_response.what_was_the_problem}
What is fixed: {new_test_code_response.what_is_fixed}
"""
                new_messages_ft.append(
                    {
                        "role": "assistant",
                        "content": new_test_code_response.json(),
                    }
                )

                code_history_item = {
                    "history_type": "revision",
                    "code": {
                        "new_code": new_test_code_response.new_code,
                        "what_was_the_problem": new_test_code_response.what_was_the_problem,
                        "what_is_fixed": new_test_code_response.what_is_fixed,
                        "code_type": new_test_code_response.code_type
                    },

                    "test_revising_input_prompt" : new_messages_ft,
                    "test_report_before_revising": pytest_response,
                    "test_report_after_revising": None,
                    "iteration_index": test_item["iteration_count"]
                }

                pytest_response  = run_pytest(test_file_name)
                test_item["status"] = pytest_response["status"]


                code_history_item["test_report_after_revising"] = pytest_response

                test_item["code_history"].append(code_history_item)
                create_report_json(state)
                commit_and_push_changes(
                    message=f"Code revised for {file_name_to_revise}",
                    description=commit_description
                )

                if code_history_item["test_report_after_revising"]["summary"]==code_history_item["test_report_before_revising"]["summary"]:
                    log(f"Test success is not changing, stopping the iteration: {test_item['iteration_count']}", send)
                    break
                
                        
            else:
                break

        
    new_trace = {
        "node_name": "test_node",
        "node_type": "test",
        "node_input": state["test_status"],
        "node_output": state["test_status"],
        "trace_timestamp": datetime.now(),
        "description": "Test cases generated and executed."
    }
    return {"test_status": state["test_status"], "trace": [new_trace]}
