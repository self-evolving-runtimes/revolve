from revolve.utils import read_python_code
from revolve.functions import get_file_list, run_pytest
from revolve.db import get_adapter
from revolve.external import get_db_type

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
    _run_query = Tool(
    name="_run_query",
    func=_run_query_on_db,
    description=description
    )
    return [
        _get_file_list,
        _read_file,
        _run_query,
        _run_test
    ]