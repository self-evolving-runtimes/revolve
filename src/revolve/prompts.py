
from revolve.external import get_db_type
from revolve.data_types import GeneratedCode, CodeHistoryMessage
import json

prompt_list = {
    "table_schema_extractor":
        """
You are a table-schema extractor. When given a full database schema, identify and extract only the table(s) the user intends to work with.
For each requested table, generate a concise instruction—without including the schema itself—such as:
“Create POST method for the X table."""
}

def get_test_generation_prompt(test_example: str, api_code: str, table_name: str, schema: str, utils: str, resouce_file: str, resource_file_name:str) -> str:
    system_prompt = f"""
Generate comprehensive test cases (max:10) for a Python API that implements CRUD (Create, Read, Update, Delete) and LIST operations based on the provided schema. The schema may include unique constraints, data types (e.g., UUID, JSONB, timestamps), and nullable fields. The tests must adhere to the following guidelines:
Data Integrity:
Validate unique constraints effectively to prevent false positives.
Ensure test data is dynamically generated to avoid conflicts, particularly for fields marked as unique.
Data Types and Validation:
Handle UUIDs, JSONB, and timestamp fields with proper parsing and formatting.
CRUD Operations:
Verify CRUD functionality, ensuring that data is created, read, updated, and deleted as expected.
Focus on testing CRUD and LIST operations using realistic scenarios.
Do not create tests for unrealistic and edge cases such as missing fields or invalid data types.        
Include tests for partial updates and soft deletes if applicable.
LIST Operations:
Test pagination, filtering, and sorting behavior.
Validate list responses for consistency, ensuring correct data types and structures.
For lists since we are connecting to the database, do not test cases such as ones where you need the latest entries created or anything unreasonable like that which are not expected in real world. Provide filters for such cases such as ids to get data expected.  
Error Handling:
Confirm that appropriate error messages are returned for invalid data, missing parameters, and constraint violations.
Idempotency and State Management:
Ensure that multiple test runs do not interfere with each other, maintaining test isolation and data consistency.
Implementation Constraints:
Do not introduce external libraries beyond standard testing libraries such as unittest, pytest, and requests.
The test code should be modular, reusable, and structured for easy maintenance and readability.
Minimize hard-coded values and prefer parameterized test cases.
For fields like created_at / updated_at that are determined by the database / server - do not assert in tests.
When sending data to simulate use json.dumps to convert py objects into valid json
Pay attention to datatypes such as text array when making payloads and send the right form of it.

Example test file should be like this:
{test_example}"""

    user_message = f"""
Here is my api code for the endpoints.
{api_code}
Here are the schema of the table ({table_name}) is used in the api:
{schema}
Here is the db_utils file (import methods from db_utils.py if needed):
{utils}
Write test methods foreach function in the resource code:
{resouce_file}"""
    return [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]

def get_test_generation_prompt_ft(test_example: str, api_code: str, table_name: str, schema: str, utils: str, resouce_file: str, resource_file_name: str) -> str:
    
    raw_output_structure = CodeHistoryMessage.model_json_schema()
    output_structure = json.dumps(raw_output_structure, indent=2)
    
    system_prompt = f"""
### SYSTEM ###
Generate comprehensive test cases (max:10) for a Python API that implements CRUD (Create, Read, Update, Delete) and LIST operations based on the provided schema. The schema may include unique constraints, data types (e.g., UUID, JSONB, timestamps), and nullable fields. The tests must adhere to the following guidelines:
Data Integrity:
Validate unique constraints effectively to prevent false positives.
Ensure test data is dynamically generated to avoid conflicts, particularly for fields marked as unique.
Data Types and Validation:
Handle UUIDs, JSONB, and timestamp fields with proper parsing and formatting.
CRUD Operations:
Verify CRUD functionality, ensuring that data is created, read, updated, and deleted as expected.
Focus on testing CRUD and LIST operations using realistic scenarios.
Do not create tests for unrealistic and edge cases such as missing fields or invalid data types.        
Include tests for partial updates and soft deletes if applicable.
LIST Operations:
Test pagination, filtering, and sorting behavior.
Validate list responses for consistency, ensuring correct data types and structures.
For lists since we are connecting to the database, do not test cases such as ones where you need the latest entries created or anything unreasonable like that which are not expected in real world. Provide filters for such cases such as ids to get data expected.  
Error Handling:
Confirm that appropriate error messages are returned for invalid data, missing parameters, and constraint violations.
Idempotency and State Management:
Ensure that multiple test runs do not interfere with each other, maintaining test isolation and data consistency.
Implementation Constraints:
Do not introduce external libraries beyond standard testing libraries such as unittest, pytest, and requests.
The test code should be modular, reusable, and structured for easy maintenance and readability.
Minimize hard-coded values and prefer parameterized test cases.
For fields like created_at / updated_at that are determined by the database / server - do not assert in tests.
When sending data to simulate use json.dumps to convert py objects into valid json
Pay attention to datatypes such as text array when making payloads and send the right form of it.
#### Example Test File ####
{test_example}
#### Instructions for Output ####
Return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{output_structure}
</tool_call>
"""

    user_message = f"""
### USER ###
Write test methods foreach function in the resource code:
#### Api Code (api.py) ####
{api_code}
#### Schema for ({table_name}) table ####
{schema}
#### db_utils (db_utils.py) ####
{utils}
#### Resource Code ({resource_file_name}) ####
{resouce_file}
"""
    return [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]

def get_test_revising_prompt(individual_prompt: str, source_code: str, example_resource_code: str, test_code: str, api_code: str, table_name: str, schema: str, utils: str, pytest_response: str, resource_file_name:str) -> str:
    new_system_message = """
You are responsible for fixing the errors.
Fix the test or the source code according to the test report provided by user.
You are responsible for writing the test cases for the given code.
Do not add any external libraries.
Always print the response content in the test for better debugging.
Be careful with non-nullable columns when generating tests.
Don't assume any id is already in the database.
Do not use placeholder values, everything should be ready to use."""
    new_user_message = f"""
My initial goal was {individual_prompt}.
However some tests are failing. 
Please fix the test, api or the resource code, which one is needed.
I only need the code, do not add any other comments or explanations.
Here is the resource code :
{source_code}
This is the example resource code in case you need to refer:
{example_resource_code}
Here is the test code:
{test_code}
The api and routes are here:
{api_code}
The db_utils file is here (import methods from db_utils.py if needed):
{utils}
The schema of the related {table_name} table is:
{schema}
And Here is the report of the failing tests:
{pytest_response}"""
    return [
        {
            "role": "system",
            "content": new_system_message,
        },
        {
            "role": "user",
            "content": new_user_message,
        },
    ]

def get_test_revising_prompt_ft(individual_prompt: str, source_code: str, example_resource_code: str, test_code: str, api_code: str, table_name: str, schema: str, utils: str, pytest_response: str, resource_file_name:str) -> str:
    raw_output_structure = CodeHistoryMessage.model_json_schema()
    output_structure = json.dumps(raw_output_structure, indent=2)
    
    new_system_message = """
### SYSTEM ###
You are responsible for fixing the errors.
Fix the test or the source code according to the test report provided by user.
You are responsible for writing the test cases for the given code.
Do not add any external libraries.
Always print the response content in the test for better debugging.
Be careful with non-nullable columns when generating tests.
Don't assume any id is already in the database.
Do not use placeholder values, everything should be ready to use.
#### Instructions for Output ####
Return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{output_structure}
</tool_call>
"""
    
    new_user_message = f"""
### USER ###
My initial goal was to {individual_prompt}.
However some tests are failing. 
Please fix the test, api or the resource code, which one is needed.
I only need the code, do not add any other comments or explanations.
#### Resource Code ({resource_file_name}) ####
{source_code}
#### Example Resource Code (in case you need to refer) ####
{example_resource_code}
#### Test Code ####
{test_code}
#### Api Code (api.py) ####
{api_code}
#### db_utils (db_utils.py, in case you need to import) ####
{utils}
#### Schema for ({table_name}) table ####
{schema}
#### Report of the failing tests ####
{pytest_response}"""
    
    return [
        {
            "role": "system",
            "content": new_system_message,
        },
        {
            "role": "user",
            "content": new_user_message,
        },
    ]

def get_process_table_prompt(utils_template: str, code_template: str, table_name: str, schemas: str, individual_prompt: str) -> list:
    
    system_prompt = f"""
Generate resource code according to the user request.
Make sure that you write production quality code that can be maintained by developers.
Include a /<resource>/schema endpoint to get the schema of the resource so that we can auto generate ui forms.
We are using falcon 4.02 for http - so only use parameters available from that version 
Requests should be trackable with logs in INFO mode. Double check the imports.
when using default values to sanitize input pl used `default` keyword in the method req.get_param('order',default='asc').lower()
Make sure that you check whether data is serializable and convert data when needed.
Guard against SQL injection attacks. Always sanitize inputs before sending it to database.
While creating List functionality, provide functionality to sort, order by and filter based on
key columns as well as skip , limit and total for pagination support. If the search filter is a date field, provide functionality to match greater than,
less than and equal to date. Filter may not be specified - handle those cases as well.
There could be multiple endpoints for the same resource.
Use methods from db_utils if needed. Here is the db_utils.py file:
{utils_template}
Here are the templates for the generation:
for the example api route 'app.add_route("/hello_db", HelloDBResource())'
output should be like this:
uri: /hello_db
resource_object: HelloDBResource()
resource_file_name: hellodb.py
resouce_code : {code_template} 
"""
    

    # add schemas and individual prompt to the user prompt
    user_prompt = f"""
Task : {individual_prompt}
Table Name : {table_name}
Schema : {schemas}
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]
    return messages

def get_readme_prompt(api_code: str) -> list:
    messages =  [
                {
                    "role": "system",
                    "content": "You are a software engineer. You are responsible for writing the README file for the project. The README file should be in markdown format."
                },
                {
                    "role": "user",
                    "content": f"""
Write a clean and concise README.md file for a Python API (api.py) built using the Falcon framework. The README should include:
env variables must be set in the .env file ("DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT")
"pip install falcon falcon-cors psycopg2" should be installed
Use the provided API code below as a reference when writing the README.
Here is the API code:\n{api_code}"""
                }
            ]
    return messages

def get_simple_prompt(prompt_name: str) -> str:
    return prompt_list[prompt_name]

def get_user_intent_prompt(messages):
    system_prompt = f"""
You are a software agent.
Your capabilities include:

1. create_crud_task:
   You can write CRUD APIs for given table names.

2. other_tasks:
   You can handle additional tasks such as:
   - Running tests
   - Running read-only queries on the database ({get_db_type()})
   - Accessing files in the repository
   - Reading Python code
   - Writing Python code, but only if explicitly asked to do so

If the user's intent does not relate to any of the above tasks, respond back to the user with a meaningful message explaining this.
"""

    user_prompt = f"""
        Here is the message from the user:
        {messages[-1]["content"]}
    """

    message_list = []
    message_list.append({
        "role": "system",
        "content": system_prompt
    })
    message_list.extend(messages[:-1])

    message_list.append({
        "role": "user",
        "content": user_prompt
    })
    return message_list
    