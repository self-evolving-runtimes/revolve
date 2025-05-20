

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
import psycopg2
from psycopg2 import errors, sql
import sqlparse


def _log(method_name, description):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{method_name:<20} - {timestamp:<20} - {description:<30}")

def log(method_name, description, send=None):
    if send:
        send({
            "name": method_name,
            "text": description,
            "status":"processing",
            "level":"log"}
        )
    _log(method_name, description)
    

def save_state(state, state_name="state"):
    try:
        state.pop("send", None)
        time_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"states/{state_name}_{time_stamp}.pkl"
        os.makedirs("states", exist_ok=True)
        with open(file_name, "wb") as f:
            pickle.dump(state, f)
    except Exception as e:
        log("save_state", f"Error saving state: {e}")
        return f"Error saving state: {e}"

def retrieve_state(state_file_name="state_2025-05-01_16-28-50.pkl", reset_tests=True):
    with open(f"states/{state_file_name}", "rb") as f:
        backup_state = pickle.load(f)
    
    if reset_tests:
        backup_state["test_status"] = None
    return backup_state

def check_schema_if_has_foreign_key(columns: Dict[str, Any]) -> bool:
    for column in columns:
        if column.get("foreign_key"):
            return True
    return False

def get_schemas_from_db():

    query_result = run_query_on_db("""SELECT jsonb_object_agg(
            table_name,
            columns
        ) AS schema_dict
    FROM (
        SELECT
            table_name,
            jsonb_agg(
                jsonb_build_object(
                    'column_name', column_name,
                    'data_type', data_type,
                    'is_nullable', is_nullable
                )
            ) AS columns
        FROM information_schema.columns
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        GROUP BY table_name
    ) AS sub;""")

    query_result = run_query_on_db("""
SELECT jsonb_object_agg(
           table_name,
           columns
       ) AS schema_dict
FROM (
    SELECT
        c.table_name,
        jsonb_agg(
            jsonb_strip_nulls(
                jsonb_build_object(
                    'column_name', c.column_name,
                    'data_type', c.data_type,
                    'is_nullable', c.is_nullable,
                    'foreign_key', jsonb_build_object(
                        'foreign_table', ccu.table_name,
                        'foreign_column', ccu.column_name
                    )
                )
            )
        ) AS columns
    FROM information_schema.columns c
    LEFT JOIN information_schema.key_column_usage kcu
        ON c.table_name = kcu.table_name
        AND c.column_name = kcu.column_name
        AND c.table_schema = kcu.table_schema
    LEFT JOIN information_schema.table_constraints tc
        ON kcu.constraint_name = tc.constraint_name
        AND tc.constraint_type = 'FOREIGN KEY'
    LEFT JOIN information_schema.constraint_column_usage ccu
        ON tc.constraint_name = ccu.constraint_name
    WHERE c.table_schema NOT IN ('pg_catalog', 'information_schema')
    GROUP BY c.table_name
) AS sub;
""")

    return query_result
    

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
    os.makedirs(f"{get_source_folder()}", exist_ok=True)

    # log("save_python_code", f"Saving python code to file: {file_name}")
    python_code = python_code.encode("utf-8").decode("unicode_escape")
    try:
        with open(f"{get_source_folder()}/{file_name}", "w") as f:
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
        with open(f"{get_source_folder()}/{file_name}", "r") as f:
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
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "source_template", file_name)
        
        with open(file_path, "r") as f:
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
                f"{get_source_folder()}/{file_name}",
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
                    log("run_pytest", f"Collector failed: {nodeid}")
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
            log("run_pytest", "All tests passed.")
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
        log("run_pytest", f"Error running pytest: {e}")
        print(f"Error running pytest: {e}")
        return {
                "status": "error",
                "message": f"Error running pytest: {e}",
                "test_results": [],
                "summary": {},
            }

def get_file_list():
    try:
        file_list = os.listdir(f"{get_source_folder()}")
    except Exception as e:
        log("get_file_list", f"Error getting file list: {e}")
        return f"Error getting file list: {e}"
    return file_list

def test_db(
    db_name: str, db_user: str, db_password: str, db_host: str, db_port: str
) -> str:
    """
    This function tests the database connection.
    Args:
        db_name (str): The name of the database.
        db_user (str): The user of the database.
        db_password (str): The password of the database.
        db_host (str): The host of the database.
        db_port (str): The port of the database.
    """
    log("test_db", "Testing database connection...")
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        conn.close()
    except Exception:
        return False

    return True


def recreate_database_psycopg2(dbname, user, password, host, port):
    """Drop and recreate the target database using psycopg2."""
    conn = psycopg2.connect(
        dbname="postgres",  # connect to control DB
        user=user,
        password=password,
        host=host,
        port=port
    )
    conn.set_session(autocommit=True)
    with conn.cursor() as cur:
        try:
            cur.execute(f"DROP DATABASE IF EXISTS {dbname};")
            print(f"✅ Dropped database '{dbname}'")
        except Exception as e:
            print(f"⚠️ Failed to drop: {e}")
        try:
            cur.execute(f"CREATE DATABASE {dbname};")
            print(f"✅ Created database '{dbname}'")
        except Exception as e:
            print(f"❌ Failed to create database: {e}")
            raise
    conn.close()

def restore_schema_with_psycopg2(
    dump_file,
    dbname,
    user,
    password,
    host="localhost",
    port=5432,
    recreate_db=False
):
    if recreate_db:
        recreate_database_psycopg2(dbname, user, password, host, port)

    with open(dump_file, "r") as f:
        raw_sql = f.read()

    statements = sqlparse.split(raw_sql)

    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    conn.set_session(autocommit=False)
    with conn.cursor() as cur:
        for stmt in statements:
            stmt = stmt.strip()
            if not stmt:
                continue
            try:
                cur.execute(stmt)
            except psycopg2.errors.DuplicateTable:
                print("⚠️ Table already exists. Skipped.")
                conn.rollback()
            except psycopg2.errors.DuplicateObject:
                print("⚠️ Object already exists. Skipped.")
                conn.rollback()
            except Exception as e:
                print(f"❌ Error executing statement:\n{stmt[:200]}...\n{e}")
                conn.rollback()
            else:
                conn.commit()

    conn.close()
    print(f"✅ Schema restored to '{dbname}'")


def generate_create_table_sql(table_name: str, columns: List[Dict]) -> str:
    col_lines = []
    for col in columns:
        data_type = col["data_type"]
        # Fix for ARRAY type
        if data_type == "ARRAY":
            data_type = "text[]"  # Default assumption; adjust per actual use-case
        line = f"  {col['column_name']} {data_type}"
        if col['is_nullable'] == 'NO':
            line += " NOT NULL"
        col_lines.append(line)
    body = ",\n".join(col_lines)
    ddl = f"CREATE TABLE {table_name} (\n{body}\n);"
    return ddl

def gen_table_map(map : Dict) -> Dict:
    # Regenerate with fixed function
    fixed_create_table_ddls = {
        table_name: generate_create_table_sql(table_name, columns)
        for table_name, columns in map.items()
    }
    return fixed_create_table_ddls

def create_database_if_not_exists(existing_dbname, new_dbname, user, password, host='localhost', port=5432):
    method = "create_database_if_not_exists"
    try:
        conn = psycopg2.connect(
            dbname=existing_dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.set_session(autocommit=True)
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (new_dbname,))
            if cur.fetchone():
                log(method, f"ℹ️ Database '{new_dbname}' already exists.")
            else:
                log(method, f"📦 Creating database '{new_dbname}' owned by '{user}'...")
                cur.execute(
                    sql.SQL("CREATE DATABASE {} OWNER {}")
                    .format(sql.Identifier(new_dbname), sql.Identifier(user))
                )
                log(method, f"✅ Database '{new_dbname}' created.")
        conn.close()
    except Exception as e:
        raise RuntimeError(f"[{method}] ❌ Failed to create database '{new_dbname}': {e}")


def apply_create_table_ddls(table_ddl_map, existing_dbname, new_dbname, user, password, host='localhost', port=5432, drop_if_exists=False):
    method = "apply_create_table_ddls"
    create_database_if_not_exists(existing_dbname, new_dbname, user, password, host, port)

    conn = psycopg2.connect(
        dbname=existing_dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    conn.set_session(autocommit=False)

    with conn.cursor() as cur:
        for table, ddl in table_ddl_map.items():
            log(method, f"▶️ Creating table: {table}")
            try:
                cur.execute(ddl)
            except errors.DuplicateTable:
                log(method, f"⚠️ Table '{table}' already exists.")
                conn.rollback()
                if drop_if_exists:
                    try:
                        log(method, f"🔁 Dropping and recreating table '{table}'...")
                        cur.execute(sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(sql.Identifier(table)))
                        conn.commit()
                        cur.execute(ddl)
                        conn.commit()
                        log(method, f"✅ Recreated table: {table}")
                    except Exception as drop_err:
                        log(method, f"❌ Error recreating '{table}': {drop_err}")
                        conn.rollback()
                else:
                    log(method, f"⏩ Skipping '{table}' (already exists)")
            except Exception as e:
                log(method, f"❌ Error creating '{table}': {e}")
                conn.rollback()
            else:
                conn.commit()
                log(method, f"✅ Created table: {table}")
    conn.close()

if __name__ =="__main__":
    # print(run_pytest("test_patients.py"))
    # print(run_pytest("test_doctors.py"))
    # print(run_pytest("test_appointments.py"))
    # print(run_pytest("test_courses.py"))
    # print(run_pytest("test_movies.py"))
    # print(run_pytest("test_users.py"))
    # print(run_pytest("test_customers.py"))
    # print(run_pytest("test_owners.py"))
    # print(run_pytest("test_students.py"))
    # print(run_pytest("test_watch_history.py"))


    result = get_schemas_from_db()
    ddls = json.loads(result)[-1][-1]
    tables = gen_table_map(ddls)

    new_dbname = os.getenv("DB_NAME") + "_1"
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")

    apply_create_table_ddls(tables, os.getenv("DB_NAME"), new_dbname, user, password, host=host, port=port, drop_if_exists=True )
