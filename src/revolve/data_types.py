from typing_extensions import TypedDict, Literal
from langchain_core.messages import AnyMessage
from datetime import datetime
from typing import Annotated, List
import operator
from pydantic import BaseModel, Field



class Trace(TypedDict):
    node_name: str
    node_type: str
    node_input:str
    node_output:str
    description: str
    trace_timestamp:datetime


class Column(TypedDict):
    column: str
    type: str
    is_primary_key: bool
    is_foreign_key: bool
    is_unique: bool
    is_nullable: bool
    is_uid: str

class Table(TypedDict):
    individual_prompt: str
    table_name: str
    columns: list[Column]

class DBSchema(TypedDict):
    tables: list[Table]

class ApiRoute(TypedDict):
    uri: str
    resource_object: str

class Resource(TypedDict):
    resource_file_name: str
    resource_code:str
    api_route: List[ApiRoute]

class NextNode(BaseModel):
    name:Literal["generate_prompt_for_code_generation", "do_stuff", "do_other_stuff", "__end__"] = Field(
        None, description="The next step in the routing process"
    )

class CodeHistoryMessage(BaseModel):
    new_code:str
    what_was_the_problem:str
    what_is_fixed:str
    code_type:Literal["resource", "test", "api"]

class CodeHistory(TypedDict):
    history_type:str # generation, revision
    code:CodeHistoryMessage
    test_report_before_revising: str
    test_report_after_revising:str
    iteration_index:int

class TestStatus(TypedDict):
    resource_file_name:str
    resource_code:str
    test_file_name: str
    test_code:str
    status: str # success, failed, fixed, in_progress
    messages: list[AnyMessage]
    code_history:list[CodeHistory]
    iteration_count: int
    table:Table
 
class GeneratedCode(TypedDict):
    full_test_code:str
    test_case_count:int
 
class State(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    trace:Annotated[list, operator.add]
    resources:Annotated[list[Resource], operator.add]
    DBSchema:DBSchema
    next_node:str
    test_status:list[TestStatus]

class Readme(TypedDict):
    md_content:str

if __name__ == "__main__":
    pass


