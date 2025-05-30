from revolve.utils import read_python_code
from revolve.functions import get_file_list, run_pytest
from revolve.db import get_adapter
from revolve.external import get_db_type

from langchain_core.tools import tool
from langchain_core.tools.structured import StructuredTool




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
def _run_test(test_file: str) -> str:
    """Run pytest on a test file."""
    #check if starts with test_ and ends with .py
    if not test_file.startswith("test_") or not test_file.endswith(".py"):
        return "Test file name is not valid. Please provide a valid test file name starting with 'test_' and ending with '.py'."

    return run_pytest(test_file)

def get_tools():
    """Get the list of tools."""
    adapter = get_adapter(get_db_type())
    methods = get_functions(adapter)
    tool_methods = [
        _get_file_list,
        _read_file,
        _run_test
    ]

    for method in methods:
        tool = StructuredTool.from_function(
            method,
            name=method.__name__,
            description=method.__doc__ or "No description available.",
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

        methods.append(attr)

    return methods