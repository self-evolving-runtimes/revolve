from revolve.utils import read_python_code
from revolve.functions import get_file_list, run_pytest
from db import get_adapter
from external import get_db_type

from langchain_core.tools import tool, Tool



@tool
def _get_file_list()-> list:
    """Get a list of files in the source folder."""
    file_list = get_file_list()
    filtered_files = [file for file in file_list if file.endswith(('.py', '.md', '.json'))]
    return filtered_files

@tool
def _read_file(file_name: str) -> str:
    """Read the content of a file. Only supports .py, .md, and .json files."""
    #if file ends with only .py, .md, or .json
    if not file_name.endswith(('.py', '.md', '.json')):
        return "File name is not valid or file type is not supported. Please provide a valid file name with .py, .md, or .json extension."

    return read_python_code(file_name)

@tool
def _run_query_on_db(query: str) -> str:
    """Run a query on the database."""
    adapter = get_adapter(get_db_type())

    if not adapter:
        return "Database adapter is not available."
    
    try:
        result = adapter.run_query_on_db(query)
        return result
    except Exception as e:
        return f"Error running query: {e}"

# Dynamically generate description
db_type = get_db_type()
description = f"Run a query on the database. The database type is {db_type}."



@tool
def _run_test(test_file: str) -> str:
    """Run pytest on a test file."""
    #check if starts with test_ and ends with .py
    if not test_file.startswith("test_") or not test_file.endswith(".py"):
        return "Test file name is not valid. Please provide a valid test file name starting with 'test_' and ending with '.py'."

    return run_pytest(test_file)

def get_tools():
    """Get the list of tools."""
    db_type = get_adapter(get_db_type())
    methods = get_functions(db_type)
    tool_methods = [
        _get_file_list,
        _read_file,
        _run_test
    ]

    for method in methods:
        tool = Tool(
            name=method["name"],
            func=getattr(db_type, method["name"]),
            description=method["doc"] if method["doc"] else "No description available."
        )
        tool_methods.append(tool)
    return tool_methods

def get_functions(adapter):
    """
    Retrieve a list of functions of the adapter
    """
    methods = []

    for m in dir(adapter):
        if m.startswith("__"):
            continue

        attr = getattr(adapter, m)
        if not callable(attr):
            continue

        if not getattr(attr, "_db_tool", False):
            continue

        methods.append({
            "name": m,
            "doc": attr.__doc__
        })

    return methods