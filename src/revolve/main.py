import os

from agents import Agent, Runner
from dotenv import load_dotenv

HTTP_TO_INTENT_REASONING_PROMPT = """
You are a highly trained AI model. You are specialized in converting HTTP requests into python code that will 
read data from a postgres tool. You will use the `Database Administrator Agent` to create new data table when 
needed. 
"""


def main() -> None:
    load_dotenv()
    agent = Agent(name="HTTP Parser Agent", instructions=HTTP_TO_INTENT_REASONING_PROMPT)

    result = Runner.run_sync(agent, "GET /accounts/mahesh")
    print(result.final_output)

    # Code within the code,
    # Functions calling themselves,
    # Infinite loop's dance.

if __name__ == '__main__':
    main()