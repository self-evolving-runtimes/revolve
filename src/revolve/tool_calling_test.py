import json
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage
from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, MessagesState, START, END

from typing import Literal


@tool
def multiply(a: int, b: int) -> int:
   """Multiply two numbers."""
   return a * b

@tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b



llm_model = ChatOpenAI(
    model="gpt-4o",
    temperature=0.2,
)
llm_model_with_tools = llm_model.bind_tools([multiply, add])


class BasicToolNode:
    """A node that runs the tools requested in the last AIMessage."""

    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}

    def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        outputs = []
        for tool_call in message.tool_calls:
            tool_result = self.tools_by_name[tool_call["name"]].invoke(
                tool_call["args"]
            )
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}

tool_executor = BasicToolNode(tools=[multiply, add])

def should_continue(state: MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tool_executor"
    return END


def call_model(state: MessagesState):
    messages = state["messages"]
    response = llm_model_with_tools.invoke(messages)
    return {"messages": [response]}


workflow = StateGraph(MessagesState)

# Define the two nodes we will cycle between
workflow.add_node("call_model", call_model)
workflow.add_node("tool_executor", tool_executor)


workflow.add_edge(START, "call_model")
workflow.add_conditional_edges("call_model", should_continue, ["tool_executor", END])
workflow.add_edge("tool_executor", "call_model")

app = workflow.compile()



# response = app.invoke({"messages": [{"role": "user", "content": "Hello, can you multiply 3 and 4 for me? After getting the result, sum the result with 5 and 6? Foreach calculation use the tools."}]})

for event in app.stream({"messages": [{"role": "user", "content": "Hello, can you multiply 3 and 4 for me? After getting the result, sum the result with 5 and 6? Foreach calculation use the tools."}]}):
    if "call_model" in event:
        if len(event["call_model"]["messages"][0].tool_calls)>0:
            tool_id = event["call_model"]["messages"][0].tool_calls[0]["id"]
            tool_name = event["call_model"]["messages"][0].tool_calls[0]["name"]
            args = event["call_model"]["messages"][0].tool_calls[0]["args"]
            print(f"Tool {tool_name} ({tool_id}) called with args: {args}")
        else:
            print(event["call_model"]["messages"][0].content)

    if "tool_executor" in event:
        tool_result = json.loads(event["tool_executor"]["messages"][0].content)
        tool_name = event["tool_executor"]["messages"][0].name
        tool_id = event["tool_executor"]["messages"][0].tool_call_id
        print(f"Tool {tool_name} ({tool_id}) returned result: {tool_result}")


pass