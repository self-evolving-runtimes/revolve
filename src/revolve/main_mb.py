from datetime import datetime
import os

from agents import Agent, Runner, function_tool, RunContextWrapper
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

import psycopg2
import json

#utils
def log(method_name, description):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{method_name:<20} - {timestamp:<20} - {description:<30}")

def connect_db():
    load_dotenv() 

    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME", "mydb"),
        user=os.getenv("DB_USER", "user"),
        password=os.getenv("DB_PASSWORD", "1234"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432)
    )
    return conn

#data models
class ColumnDetail(BaseModel):
    column_name: str = ""
    data_type: str = ""

class TableSchema(BaseModel):
    table_name: str = ""
    columns: List[ColumnDetail] = []

class DbDetailsContext(BaseModel):
    tables: List[TableSchema] = []

class FunctionResponse(BaseModel):
    function_name: str
    response_text: str
    status:bool
    data: Optional[Dict[str, Any]] = None
    


#Functions
@function_tool
def get_table_names(context: RunContextWrapper[DbDetailsContext]):
    """
    Fetch all table names in the database and update the context with the result.
    """
    log("get_table_names", "Fetching table names")
    conn = connect_db()

    cursor = conn.cursor()
    
    query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """
    cursor.execute(query)
    tables = cursor.fetchall()
    
    table_names = [table[0] for table in tables]
    context.context.tables = [
        TableSchema(
            table_name=table_name,
            columns=[]
        ) for table_name in table_names
    ]
    cursor.close()

    log("get_table_names", "Table names fetched successfully and updated in the context.")

    return FunctionResponse(
        function_name="get_table_names",
        response_text="Table names fetched successfully and updated in the context.",
        status=True,
        data={"table_names": table_names}
    )

@function_tool
def get_table_details(context: RunContextWrapper[DbDetailsContext], table_name: str):
    """
    Fetch schema of a specific table and return it as a JSON string and update the context with the result.
    """

    log("get_table_details", f"Fetching table details for table {table_name}")
    conn = connect_db()
    cursor = conn.cursor()
    
    query = f"""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = '{table_name}';
    """
    cursor.execute(query)
    columns = cursor.fetchall()
    
    column_details = [
        ColumnDetail(
            column_name=column[0],
            data_type=column[1]
        ) for column in columns
    ]
    for table in context.context.tables:
        if table.table_name == table_name:
            table.columns = column_details
            break
    conn.close()       
    log("get_table_details", f"Table details fetched successfully and updated in the context for table {table_name}.")

    return FunctionResponse(
        function_name="get_table_details",
        response_text=f"Table details fetched successfully and updated in the context for table {table_name}.",
        status=True,
        data={"table_name": table_name, "columns": column_details}
    )

#Agents
main_agent = Agent[DbDetailsContext](name="Db Manager", instructions="You are specialized in managing a postgres database.", tools=[get_table_names, get_table_details])


def main() -> None:
    ctx = RunContextWrapper(DbDetailsContext())
    result = Runner.run_sync(main_agent, input="Get the tables in db and create a report with details", context=ctx)
    print(result.final_output)


if __name__ == '__main__':
    main()





