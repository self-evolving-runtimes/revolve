

from datetime import datetime
import time
import os
from pathlib import Path
import shutil
from pprint import pprint

import subprocess
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Any, Dict, List, Optional, Any
from langchain_openai import ChatOpenAI
import pickle

import psycopg2
import json


def log(method_name, description):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{method_name:<20} - {timestamp:<20} - {description:<30}")

def save_state(state, state_name="state"):
    time_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"states/{state_name}_{time_stamp}.pkl"
    with open(file_name, "wb") as f:
        pickle.dump(state, f)

def retrieve_state(state_file_name="state_2025-05-01_16-28-50.pkl", reset_tests=True):
    with open(f"states/{state_file_name}", "rb") as f:
        backup_state = pickle.load(f)
    
    if reset_tests:
        backup_state["test_status"] = None
    return backup_state


def run_query_on_db(query: str) -> str:
    """
    This function runs the given query on the database.
    Args:
        query (str): The query to be run.
    """
    # log("run_query_on_db", f"Running query: {query}")
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
        )
        cur = conn.cursor()
        cur.execute(query)
        # if cur.rowcount:
        result = cur.fetchall()
        # else:
        #     result = None
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        log("run_query_on_db", f"Error running query: {e}")
        return f"Error running query: {e}"

    # log("run_query_on_db", f"Query executed successfully.")
    # log("run_query_on_db", f"Result: {result}")
    return json.dumps(result)

def save_python_code(python_code: str, file_name: str) -> str:
    """
    This functions saves the generated python code.
    Args:
        python_code (str): Python code to be saved.
        file_name (str): The name of the file to be saved.
    """

    #create the directory if it doesn't exist
    os.makedirs("src/revolve/source_generated", exist_ok=True)

    # log("save_python_code", f"Saving python code to file: {file_name}")
    python_code = python_code.encode("utf-8").decode("unicode_escape")
    try:
        with open(f"src/revolve/source_generated/{file_name}", "w") as f:
            f.write(python_code)
    except Exception as e:
        log("save_python_code", f"Error saving python code: {e}")
        return f"Error saving python code: {e}"

    log("save_python_code", f"Python code saved successfully to {file_name}.")
    return f"Python code saved to {file_name} successfully."

def read_python_code(file_name: str) -> str:
    """
    This function returns the generated python code from the given file name.
    Args:
        file_name (str): The name of the file to be read.
    """
    # log("get_python_code", f"Getting python code from file: {file_name}")
    try:
        with open(f"src/revolve/source_generated/{file_name}", "r") as f:
            python_code = f.read()
    except Exception as e:
        log("get_python_code", f"Error getting python code: {e}")
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
    try:
        with open(f"src/revolve/source_template/{file_name}", "r") as f:
            python_code = f.read()
    except Exception as e:
        log("read_python_code_template", f"Error getting python code: {e}")
        return f"Error getting python code: {e}"

    # log("read_python_code_template", f"Python code retrieved successfully.")
    return python_code

def run_pytest(file_name="test_api.py") -> List[Dict[str, Any]]:
    """
    Runs pytest with JSON reporting and returns a structured output
    for failed tests or collection errors.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries summarizing test failures,
                              collection errors, or a success message if all tests pass.
    """
    log("run_pytest", "Running pytest with JSON reporting...")


    report_path = Path("report.json")

    try:
        # Run pytest with JSON reporting.
        result = subprocess.run(
            [
                "pytest",
                f"src/revolve/source_generated/{file_name}",
                "--json-report",
                f"--json-report-file={report_path}",
                "--log-cli-level=DEBUG",
                "--show-capture=all",
                "-q",
            ],
            capture_output=True,
            text=True,
            check=False,  # Allow the process to finish even if tests fail.
        )

        if not report_path.exists():
            time.sleep(0.2)
        if not report_path.exists():
            log(
                "run_pytest",
                "report.json not generated. Pytest might have failed before reporting.",
            )
            return {
                "status":"error",
                "message": "report.json not generated. Pytest might have failed before reporting.",
                "test_results": [],
                }
            

        with report_path.open() as json_file:
            try:
                report_data = json.load(json_file)
            except json.JSONDecodeError as decode_err:
                log("run_pytest", f"Error decoding JSON: {decode_err}")
                return {
                    "status":"error",
                    "message": f"Error decoding JSON: {decode_err}",
                    "test_results": [], 
                    }
                

        test_results: List[Dict[str, Any]] = []

        # Retrieve tests; support both list and dict formats.
        tests = report_data.get("tests", [])
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
                        "logs": logs,
                    }
                )

        # If no test failures, check for collector errors.
        if not test_results:
            collectors = report_data.get("collectors", [])
            for collector in collectors:
                if collector.get("outcome") == "failed":
                    nodeid = collector.get("nodeid", "unknown")
                    log("run_pytest", f"Collector failed: {nodeid}")
                    test_results.append(
                        {
                            "name": nodeid,
                            "outcome": "collection_failed",
                            "longrepr": collector.get(
                                "longrepr", "Unknown error during collection."
                            ),
                            "stdout": "",
                            "logs": [],
                        }
                    )

        if not test_results:
            log("run_pytest", "All tests passed.")
            return {"status":"success","message": "All tests passed.", "test_results": []}

        pprint(test_results)
        return {
            "status":"failed",
            "message": "Some tests failed.",
            "test_results": test_results,
        }

    except Exception as e:
        log("run_pytest", f"Error running pytest: {e}")
        print(f"Error running pytest: {e}")
        return {
                "status": "error",
                "message": f"Error running pytest: {e}",
                "test_results": [],
            }
        





if __name__ =="__main__":
    print(run_pytest("test_patients.py"))

