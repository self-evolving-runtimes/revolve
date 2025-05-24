import inspect
import sys
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
from collections import defaultdict, deque

import sqlparse
from loguru import logger
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time} | {level} | {message}")

def _log(method_name, description, level="INFO"):
    logger.log(level, f"{method_name:<20} - {description:<30}")

def log(description, send=None, level="system"):

    method_name = inspect.currentframe().f_back.f_code.co_name
    if send:
        send({
            "name": method_name,
            "text": description,
            "status":"processing",
            "level":level}
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
        log(f"Error saving state: {e}")
        return f"Error saving state: {e}"

def retrieve_state(state_file_name="state_2025-05-01_16-28-50.pkl", reset_tests=True):
    with open(f"states/{state_file_name}", "rb") as f:
        backup_state = pickle.load(f)
    
    if reset_tests:
        backup_state["test_status"] = None
    return backup_state

def check_schema_for_unsupported_types(columns: Dict[str, Any]) -> bool:
    for column in columns:
        if column.get("foreign_key"):
            return True
        column_type = column.get("type")
        if column_type == "USER-DEFINED":
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
                            'character_max_length', c.character_maximum_length,
                            'numeric_precision', c.numeric_precision,
                            'numeric_scale', c.numeric_scale,
                            'enum_values', ev.enum_values,
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
            LEFT JOIN LATERAL (
                SELECT jsonb_agg(e.enumlabel) AS enum_values
                FROM pg_type t
                JOIN pg_enum e ON t.oid = e.enumtypid
                JOIN pg_namespace ns ON ns.oid = t.typnamespace
                WHERE t.typname = c.udt_name
            ) ev ON true
            WHERE c.table_schema NOT IN ('pg_catalog', 'information_schema')
            GROUP BY c.table_name
        ) AS sub;""")

    return query_result

def get_table_dependencies():
    query_result = run_query_on_db("""
        WITH fk_info AS (
        SELECT
            kcu.table_name AS from_table,
            kcu.column_name AS from_column,
            ccu.table_name AS to_table,
            ccu.column_name AS to_column,
            -- Check if from_column is unique or part of primary key
            EXISTS (
                SELECT 1 FROM information_schema.table_constraints tc2
                JOIN information_schema.key_column_usage kcu2
                  ON tc2.constraint_name = kcu2.constraint_name
                WHERE tc2.table_name = kcu.table_name
                  AND kcu2.column_name = kcu.column_name
                  AND tc2.constraint_type IN ('PRIMARY KEY', 'UNIQUE')
            ) AS is_from_unique,
            -- Check if to_column is unique or primary
            EXISTS (
                SELECT 1 FROM information_schema.table_constraints tc3
                JOIN information_schema.key_column_usage kcu3
                  ON tc3.constraint_name = kcu3.constraint_name
                WHERE tc3.table_name = ccu.table_name
                  AND kcu3.column_name = ccu.column_name
                  AND tc3.constraint_type IN ('PRIMARY KEY', 'UNIQUE')
            ) AS is_to_unique
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu
            ON tc.constraint_name = ccu.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema NOT IN ('pg_catalog', 'information_schema')
    )
    SELECT jsonb_object_agg(
        from_table,
        column_mappings
    ) AS fk_relationships
    FROM (
        SELECT
            from_table,
            jsonb_object_agg(
                from_column,
                jsonb_build_object(
                    'links_to_table', to_table,
                    'reltype',
                        CASE
                            WHEN is_from_unique AND is_to_unique THEN 'one-to-one'
                            WHEN NOT is_from_unique AND is_to_unique THEN 'many-to-one'
                            ELSE 'uncertain' -- fallback
                        END
                )
            ) AS column_mappings
        FROM fk_info
        GROUP BY from_table
    ) AS rels;

    """)

from typing import Dict, Any

def order_tables_by_dependencies(dependencies: Dict[str, Any]) -> List[str]:
    # Extract child tables and all referenced parent tables
    child_tables = set(dependencies)
    referenced_parents = {
        info["links_to_table"]
        for links in dependencies.values()
        for info in links.values()
    }

    # Build dependency map: table -> list of tables it links to
    final_dependency_map = {
        table: [info["links_to_table"] for info in links.values()]
        for table, links in dependencies.items()
    }

    # Identify and remove tables that are only referenced and have no outgoing links
    for table in list(final_dependency_map):
        if table in referenced_parents and not final_dependency_map[table]:
            del final_dependency_map[table]

    tp_sorted = topological_sort(dependencies)

    return final_dependency_map, tp_sorted


def topological_sort(dependencies: Dict[str, Any]) -> List[str]:
    graph = defaultdict(list)  # parent -> list of children
    in_degree = defaultdict(int)
    all_tables = set(dependencies)  # explicitly defined tables

    # Parse dependencies to construct graph and in-degrees
    for child, columns in dependencies.items():
        if isinstance(columns, dict):
            for col_info in columns.values():
                if isinstance(col_info, dict) and "links_to_table" in col_info:
                    parent = col_info["links_to_table"]
                    graph[parent].append(child)
                    in_degree[child] += 1
                    all_tables.add(parent)  # include implicit parent tables

    # Start with all tables that have no incoming edges
    queue = deque([table for table in all_tables if in_degree[table] == 0])
    sorted_tables = []

    # Kahn’s Algorithm for topological sorting
    while queue:
        table = queue.popleft()
        sorted_tables.append(table)

        for dependent in graph[table]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    # Detect cycles
    if len(sorted_tables) != len(all_tables):
        raise ValueError("Cycle detected in table dependencies.")

    return sorted_tables

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
        log(f"Error running query: {e}")
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
    try:
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "source_template", file_name)
        
        with open(file_path, "r") as f:
            python_code = f.read()
    except Exception as e:
        log(f"Error getting python code: {e}")
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
    log("Running pytest with JSON reporting...")


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
        file_list = os.listdir(f"{get_source_folder()}")
    except Exception as e:
        log(f"Error getting file list: {e}", level="DEBUG")
        return f"Error getting file list: {e}"
    return file_list

def check_db(
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
    log("Testing database connection...")
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
                log(f"ℹ️ Database '{new_dbname}' already exists.")
            else:
                log(f"📦 Creating database '{new_dbname}' owned by '{user}'...")
                cur.execute(
                    sql.SQL("CREATE DATABASE {} OWNER {}")
                    .format(sql.Identifier(new_dbname), sql.Identifier(user))
                )
                log(f"✅ Database '{new_dbname}' created.")
        conn.close()
    except Exception as e:
        raise RuntimeError(f"[{method}] ❌ Failed to create database '{new_dbname}': {e}")


def apply_create_table_ddls(table_ddl_map, existing_dbname, new_dbname, user, password, host='localhost', port=5432, drop_if_exists=False):
    method = "apply_create_table_ddls"
    create_database_if_not_exists(existing_dbname, new_dbname, user, password, host, port)
    conn = psycopg2.connect(
        dbname=new_dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    conn.set_session(autocommit=False)

    with conn.cursor() as cur:
        for table, ddl in table_ddl_map.items():
            log(f"▶️ Creating table: {table}")
            try:
                cur.execute(ddl)
            except errors.DuplicateTable:
                log(f"⚠️ Table '{table}' already exists.")
                conn.rollback()
                if drop_if_exists:
                    try:
                        log(f"🔁 Dropping and recreating table '{table}'...")
                        cur.execute(sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(sql.Identifier(table)))
                        conn.commit()
                        cur.execute(ddl)
                        conn.commit()
                        log(f"✅ Recreated table: {table}")
                    except Exception as drop_err:
                        log(f"❌ Error recreating '{table}': {drop_err}")
                        conn.rollback()
                else:
                    log(f"⏩ Skipping '{table}' (already exists)")
            except Exception as e:
                log(f"❌ Error creating '{table}': {e}")
                conn.rollback()
            else:
                conn.commit()
                log(f"✅ Created table: {table}")
    conn.close()

def clone_db():
    result = get_schemas_from_db()
    ddls = json.loads(result)[-1][-1]
    tables = gen_table_map(ddls)

    new_dbname = os.getenv("DB_NAME") + "_test"
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")

    apply_create_table_ddls(tables, os.getenv("DB_NAME"), new_dbname, user, password, host=host, port=port, drop_if_exists=True)
    os.environ["DB_NAME_TEST"] = new_dbname

def check_permissions():
    db_user_name = os.getenv("DB_USER")
    query = f"""
SELECT jsonb_build_object(
  'can_connect', has_database_privilege('postgres', current_database(), 'CONNECT'),
  'can_use_schema', has_schema_privilege('postgres', 'public', 'USAGE'),
  'can_create_db', rolcreatedb,
  'can_create_role', rolcreaterole,
  'is_superuser', rolsuper
) AS permissions
FROM pg_roles
WHERE rolname = '{db_user_name}';
"""
    result = run_query_on_db(query)
    permissions = json.loads(result)[-1][-1]

    suggested_queries_template ={
    'can_connect': "GRANT CONNECT ON DATABASE {database} TO {username};",
    'is_superuser': "ALTER ROLE {username} WITH SUPERUSER;",
    'can_create_db': "ALTER ROLE {username} WITH CREATEDB;",
    'can_use_schema': "GRANT USAGE ON SCHEMA public TO {username};",
    'can_create_role': "ALTER ROLE {username} WITH CREATEROLE;",
    }
    suggested_queries = {}
    for key, value in permissions.items():
        if value == False:
            suggested_queries[key] = suggested_queries_template[key].format(database=os.getenv("DB_NAME"), username=db_user_name)

    if all(value == True for value in permissions.values()):
        return {
            "status": "success",
            "permissions": permissions,
            "message": "All required permissions are already granted. "
        }
    else:
        suggested_queries_str = "\n".join([f"{key}: {value}" for key, value in suggested_queries.items()])
        return {
            "status": "error",
            "permissions": permissions,
            "error": f"You do not have the necessary permissions to perform this operation. You can use the following "
                     f"SQL statements to grant the required permissions:<pre style={{ whiteSpace: 'pre-wrap', "
                     f"background: '#f6f8fa', padding: 10, borderRadius: 4 }}>{suggested_queries_str}</pre>",
        }

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
    #print(run_pytest("test_watch_history.py"))
    d_map = {"users": {}, "orders": {"customer_id": {"reltype": "many-to-one", "links_to_table": "customers"}}, "courses": {}, "devices": {}, "patients": {}, "students": {}, "customers": {}, "employees": {}, "device_logs": {"device_id": {"reltype": "many-to-one", "links_to_table": "devices"}}, "enrollments": {"course_id": {"reltype": "one-to-one", "links_to_table": "courses"}, "student_id": {"reltype": "one-to-one", "links_to_table": "students"}}, "order_items": {"order_id": {"reltype": "many-to-one", "links_to_table": "orders"}}, "appointments": {"patient_id": {"reltype": "many-to-one", "links_to_table": "patients"}}, "employee_details": {"employee_id": {"reltype": "one-to-one", "links_to_table": "employees"}}}
    d_map = {
  "orders": {
    "user_id": {
      "reltype": "many-to-one",
      "links_to_table": "users"
    },
    "product_id": {
      "reltype": "many-to-one",
      "links_to_table": "products"
    }
  },
  "products": {
    "supplier_id": {
      "reltype": "many-to-one",
      "links_to_table": "suppliers"
    }
  },
  "users": {},
  "suppliers": {}
}
    d_map = {"orders":{"customer_id":{"reltype":"many-to-one","links_to_table":"customers"},"payment_id":{"reltype":"one-to-one","links_to_table":"payments"}},"payments":{"transaction_id":{"reltype":"many-to-one","links_to_table":"transactions"}},"transactions":{"processor_id":{"reltype":"many-to-one","links_to_table":"payment_processors"}},"customers":{"referrer_id":{"reltype":"many-to-one","links_to_table":"users"}},"users":{},"products":{"supplier_id":{"reltype":"many-to-one","links_to_table":"suppliers"},"category_id":{"reltype":"many-to-one","links_to_table":"categories"}},"suppliers":{"region_id":{"reltype":"many-to-one","links_to_table":"regions"}},"categories":{},"regions":{},"order_items":{"order_id":{"reltype":"many-to-one","links_to_table":"orders"},"product_id":{"reltype":"many-to-one","links_to_table":"products"}},"inventory":{"product_id":{"reltype":"one-to-one","links_to_table":"products"},"warehouse_id":{"reltype":"many-to-one","links_to_table":"warehouses"}},"warehouses":{"region_id":{"reltype":"many-to-one","links_to_table":"regions"}},"students":{},"courses":{},"enrollments":{"student_id":{"reltype":"many-to-one","links_to_table":"students"},"course_id":{"reltype":"many-to-one","links_to_table":"courses"}},"appointments":{"patient_id":{"reltype":"many-to-one","links_to_table":"patients"},"doctor_id":{"reltype":"many-to-one","links_to_table":"employees"}},"patients":{},"employees":{"department_id":{"reltype":"many-to-one","links_to_table":"departments"}},"departments":{},"device_logs":{"device_id":{"reltype":"many-to-one","links_to_table":"devices"},"user_id":{"reltype":"many-to-one","links_to_table":"users"}},"devices":{"assigned_to":{"reltype":"many-to-one","links_to_table":"employees"}},"audit_trail":{"user_id":{"reltype":"many-to-one","links_to_table":"users"}},"payment_processors":{},"feedback":{"order_id":{"reltype":"many-to-one","links_to_table":"orders"},"customer_id":{"reltype":"many-to-one","links_to_table":"customers"}},"alerts":{"device_id":{"reltype":"many-to-one","links_to_table":"devices"}},"settings":{}}
    d_map = {"users": {}, "alerts": {"device_id": {"reltype": "many-to-one", "links_to_table": "devices"}}, "orders": {"payment_id": {"reltype": "one-to-one", "links_to_table": "payments"}, "customer_id": {"reltype": "many-to-one", "links_to_table": "customers"}}, "courses": {}, "devices": {"assigned_to": {"reltype": "many-to-one", "links_to_table": "employees"}}, "regions": {}, "feedback": {"order_id": {"reltype": "many-to-one", "links_to_table": "orders"}, "customer_id": {"reltype": "many-to-one", "links_to_table": "customers"}}, "patients": {}, "payments": {"transaction_id": {"reltype": "many-to-one", "links_to_table": "transactions"}}, "products": {"category_id": {"reltype": "many-to-one", "links_to_table": "categories"}, "supplier_id": {"reltype": "many-to-one", "links_to_table": "suppliers"}}, "settings": {}, "students": {}, "customers": {"referrer_id": {"reltype": "many-to-one", "links_to_table": "users"}}, "employees": {"department_id": {"reltype": "many-to-one", "links_to_table": "departments"}}, "inventory": {"product_id": {"reltype": "one-to-one", "links_to_table": "products"}, "warehouse_id": {"reltype": "many-to-one", "links_to_table": "warehouses"}}, "suppliers": {"region_id": {"reltype": "many-to-one", "links_to_table": "regions"}}, "categories": {}, "warehouses": {"region_id": {"reltype": "many-to-one", "links_to_table": "regions"}}, "audit_trail": {"user_id": {"reltype": "many-to-one", "links_to_table": "users"}}, "departments": {}, "device_logs": {"user_id": {"reltype": "many-to-one", "links_to_table": "users"}, "device_id": {"reltype": "many-to-one", "links_to_table": "devices"}}, "enrollments": {"course_id": {"reltype": "many-to-one", "links_to_table": "courses"}, "student_id": {"reltype": "many-to-one", "links_to_table": "students"}}, "order_items": {"order_id": {"reltype": "many-to-one", "links_to_table": "orders"}, "product_id": {"reltype": "many-to-one", "links_to_table": "products"}}, "appointments": {"doctor_id": {"reltype": "many-to-one", "links_to_table": "employees"}, "patient_id": {"reltype": "many-to-one", "links_to_table": "patients"}}, "transactions": {"processor_id": {"reltype": "many-to-one", "links_to_table": "payment_processors"}}, "payment_processors": {}}
    #d_map = {"users": {}, "courses": {}, "regions": {}, "patients": {}, "students": {}, "customers": {}, "employees": {}, "categories": {}, "departments": {}, "payment_processors": {}}
    d_map, _ = order_tables_by_dependencies(d_map)
    print(d_map)
    




