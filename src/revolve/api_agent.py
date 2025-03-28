from datetime import datetime
import os

from agents import Agent, Runner, function_tool, RunContextWrapper
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

import psycopg2
import json

import pandas as pd

# Utils
def log(method_name, description):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{method_name:<20} - {timestamp:<20} - {description:<30}")

class ServiceDetail(BaseModel):
    path: str
    class_name: str
    module: str

class ApiContext(BaseModel):
    name: str = "Falcon API"
    services: List[ServiceDetail] = []

# Prompts
# def get_example():
#     return """
# Service Example:
# details:
# path,class_name,module
# /service-example,ServiceExample,service_example
# code (service_example.py):
# ```python
# import falcon
# import json

# class ServiceExample:
#     def on_post(self, req, resp):

#         params = req.params
#         userName = params.get("name", None)
#         if userName is None:
#             resp.text = json.dumps({"error": "Name not provided"})
#             resp.status = falcon.HTTP_400
#             return
#         else:
#             resp.text = json.dumps({"message": f"Hello {userName}"})
#             resp.status = falcon.HTTP_200
#             return
# #No need to add route, it will be done automatically.
# ```

# """


# Functions
@function_tool
def save_python_code(context: RunContextWrapper[ApiContext], python_code: str, file_name:str) -> str:
    """
    This functions saves the python code.
    Args:
        python_code (str): Python code to be saved.
        file_name (str): The name of the file to be saved.
    """
    log("save_python_code", f"Saving python code: {python_code[:20]}...")
    try:
        with open(f"src/revolve/services/{file_name}", "w") as f:
            f.write(python_code)
    except Exception as e:
        return f"Error saving python code: {e}"

    return "Python code saved."

@function_tool
def register_service_route(context: RunContextWrapper[ApiContext], serviceDetail: ServiceDetail) -> str:
    """
    This function registers a service route with the given details.
    Args:
        serviceDetail: ServiceDetail
        serviceDetail.path (str): The path of the service.
        serviceDetail.class_name (str): The class name of the service.
        serviceDetail.module (str): The module name of the service.
    """
    log("register_service_route", f"Registering service: {serviceDetail}")
    try:
        registered_services_df = pd.read_csv('src/revolve/registered_routes.csv')
        registered_services_df = pd.concat([registered_services_df, pd.DataFrame([serviceDetail.model_dump()])])
        registered_services_df.to_csv('src/revolve/registered_routes.csv', index=False)
    except Exception as e:
        log("register_service_route", f"Error registering service: {e}")
        return f"Error registering service: {e}"
    
    log("register_service_route", f"Service registered successfully.")
    return "Service registered successfully."

@function_tool
def run_query_on_db(context: RunContextWrapper[ApiContext], query: str) -> str:
    """
    This function runs the given query on the database.
    Args:
        query (str): The query to be run.
    """
    log("run_query_on_db", f"Running query: {query}")
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        cur = conn.cursor()
        cur.execute(query)
        result = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        log("run_query_on_db", f"Error running query: {e}")
        return f"Error running query: {e}"
    
    log("run_query_on_db", f"Query executed successfully.")
    return json.dumps(result)

@function_tool
def get_db_example_connection_code(context: RunContextWrapper[ApiContext]) -> str:
    """
    This function returns the example code to connect to the database.
    """
    log("get_db_example_connection_code", f"Getting example connection code.")
    rs = """ 
conn = psycopg2.connect(
dbname=os.getenv("DB_NAME"),
user=os.getenv("DB_USER"),
password=os.getenv("DB_PASSWORD"),
host=os.getenv("DB_HOST"),
port=os.getenv("DB_PORT")
)"""
    return rs
#Agents

def main() -> None:
    # falcon_agent = Agent[ApiContext](name="Falcon Api Expert", instructions="You are specialized in managing a Falcon API. You can create and save services if needed. Use handoffs when its needed.", tools=[save_python_code, register_service_route], handoffs=[])
    # db_agent = Agent[ApiContext](name="Database Expert", instructions="You are specialized in managing databases. You can run the queries on the db to get data or get schema informations. Use handoffs when its needed.", tools=[save_python_code, register_service_route,run_query_on_db, get_db_example_connection_code], handoffs=[])
    main_agent = Agent[ApiContext](name="Main Agent", instructions="Make sure to follow the instructions.", tools=[save_python_code, register_service_route,run_query_on_db, get_db_example_connection_code], handoffs=[])

    # main_agent.handoffs.append(falcon_agent)
    # main_agent.handoffs.append(db_agent)

    # falcon_agent.handoffs.append(main_agent)
    # falcon_agent.handoffs.append(db_agent)

    # db_agent.handoffs.append(main_agent)
    # db_agent.handoffs.append(falcon_agent)

    ctx = RunContextWrapper(ApiContext())

    Instructions = """" \
    "Task : Create a falcon service that get top 10 rows for each table separately.
    1. Always check the db schema and example connection code before saving service.
    2. Create different services foreach table, and make sure services return json data in media attribute.
    """
    result = Runner.run_sync(main_agent, input=Instructions, context=ctx)
    print(result.final_output)

if __name__ == '__main__':
    main()





