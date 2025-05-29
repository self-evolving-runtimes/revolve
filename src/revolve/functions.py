from datetime import datetime
import time
import os
from pathlib import Path
from pprint import pprint

import subprocess
from typing import Dict, List, Any
import pickle

import json
from revolve.external import get_source_folder
from revolve.utils import log



def save_state(state, state_name="state"):
    try:
        state.pop("send", None)
        time_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"states/{state_name}_{time_stamp}.pkl"
        os.makedirs("states", exist_ok=True)
        with open(file_name, "wb") as f:
            pickle.dump(state, f)
    except Exception as e:
        log(f"Error saving state: {e}")
        return f"Error saving state: {e}"

def retrieve_state(state_file_name="state_2025-05-01_16-28-50.pkl", reset_tests=True):
    with open(f"states/{state_file_name}", "rb") as f:
        backup_state = pickle.load(f)
    
    if reset_tests:
        backup_state["test_status"] = None
    return backup_state

def check_schema_for_unsupported_types(columns: Dict[str, Any]) -> bool:
    # for column in columns:
    #     if column.get("foreign_key"):
    #         return True
    #     column_type = column.get("type")
    #     if column_type == "USER-DEFINED":
    #         return True
    return False


def order_tables_by_dependencies_(dependencies: Dict[str, Any]) -> List[str]:
    # Step 1: Track all tables that are children and referenced parents
    child_tables = set(dependencies.keys())
    referenced_parents = set()

    for links in dependencies.values():
        for info in links.values():
            referenced_parents.add(info["links_to_table"])

    # Step 3: Build final dependency map (children only) and include isolated tables with []
    final_dependency_map = {
        table: [info["links_to_table"] for info in links.values()]
        for table, links in dependencies.items()
    }

    all_linked_values = {
        info["links_to_table"]
        for links in dependencies.values()
        for info in links.values()
    }

    remove_list = []
    for table , links in final_dependency_map.items():
        if table in all_linked_values and len(links) == 0:
            remove_list.append(table)

    #remove the tables in remove_list from final_dependency_map
    for table in remove_list:
        final_dependency_map.pop(table)
    return final_dependency_map



def run_pytest(file_name="test_api.py") -> List[Dict[str, Any]]:
    """
    Runs pytest with JSON reporting and returns a structured output
    for failed tests or collection errors.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries summarizing test failures,
                              collection errors, or a success message if all tests pass.
    """
    log("Running pytest with JSON reporting...")


    report_path = Path(__file__).parent / "report.json"
    test_file_path = Path(get_source_folder()) / file_name
    test_file_path = test_file_path.resolve()
    print("Looking for test file at:", str(test_file_path))
    try:
        # Run pytest with JSON reporting.
        result = subprocess.run(
            [
                "pytest",
                str(test_file_path.name),
                "--json-report",
                f"--json-report-file={report_path}",
                "--log-cli-level=DEBUG",
                "--show-capture=all",
                "-q",
            ],
            capture_output=True,
            text=True,
            check=False,
            cwd=test_file_path.parent
        )

        time.sleep(0.2)
        if not report_path.exists():
            log("report.json not generated. Pytest might have failed before reporting.")
            return {
                "status":"error",
                "message": "report.json not generated. Pytest might have failed before reporting.",
                "test_results": [],
                }
            

        with report_path.open() as json_file:
            try:
                report_data = json.load(json_file)
            except json.JSONDecodeError as decode_err:
                log(f"Error decoding JSON: {decode_err}")
                return {
                    "status":"error",
                    "message": f"Error decoding JSON: {decode_err}",
                    "test_results": [], 
                    }
                

        test_results: List[Dict[str, Any]] = []

        # Retrieve tests; support both list and dict formats.
        tests = report_data.get("tests", [])
        summary = report_data.get("summary", {})
        if not isinstance(tests, list):
            tests = list(tests.values())

        # Process each test entry.
        for test in tests:
            if test.get("outcome") != "passed":
                nodeid = test.get("nodeid", "unknown")
                # Choose which phase to pull error details from.
                if "call" in test:
                    phase = "call"
                elif "setup" in test:
                    phase = "setup"
                elif "teardown" in test:
                    phase = "teardown"
                else:
                    phase = "unknown"
                details = test.get(phase, {})
                longrepr = details.get("longrepr", "")
                stdout = details.get("stdout", "")
                logs = (
                    [log_item.get("msg", "") for log_item in details.get("log", [])]
                    if details.get("log")
                    else []
                )
                test_results.append(
                    {
                        "name": nodeid,
                        "outcome": test.get("outcome", "unknown"),
                        "phase": phase,
                        "longrepr": longrepr,
                        "stdout": stdout,
                        "stderr": details.get("stderr", ""),
                        "logs": logs,
                    }
                )

        # If no test failures, check for collector errors.
        if not test_results:
            collectors = report_data.get("collectors", [])
            for collector in collectors:
                if collector.get("outcome") == "failed":
                    nodeid = collector.get("nodeid", "unknown")
                    log(f"Collector failed: {nodeid}")
                    test_results.append(
                        {
                            "name": nodeid,
                            "outcome": "collection_failed",
                            "longrepr": collector.get(
                                "longrepr", "Unknown error during collection."
                            ),
                            "stdout": collector.get("stdout", ""),
                            "stderr": collector.get("stderr", ""),
                            "logs": [],
                        }
                    )

        if not test_results:
            log("All tests passed.")
            report = {"status":"success","message": "All tests passed.", "test_results": [], "summary": summary}
            pprint(report)
            return report
        print("*" * 100)
        print("-- Test Results --")
        pprint(test_results)
        print("-- Summary --")


        failed_tests = [test["name"] for test in test_results]
        passed_percentage = (
            round(1 - len(failed_tests) / len(tests),2)
            if len(tests) > 0
            else 0
        )
        summary["passed_percentage"] = passed_percentage
        summary["failed_tests"] = failed_tests
        pprint(summary)
        print("*" * 100)
        return {
            "status":"failed",
            "message": "Some tests failed.",
            "test_results": test_results,
            "summary": summary,
        }

    except Exception as e:
        log(f"Error running pytest: {e}")
        print(f"Error running pytest: {e}")
        return {
                "status": "error",
                "message": f"Error running pytest: {e}",
                "test_results": [],
                "summary": {},
            }

def get_file_list():
    try:
        file_path =  get_source_folder()
        if file_path and os.path.exists(file_path):
            return os.listdir(file_path)

    except Exception as e:
        log(f"Error getting file list: {e}", level="DEBUG")
        return f"Error getting file list: {e}"
    return []




