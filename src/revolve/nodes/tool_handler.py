


from langchain_openai import ChatOpenAI
from revolve.data_types import State
from revolve.tools import get_tools
from langchain_core.messages import ToolMessage
from revolve.functions import log



def tool_handler(state:State):
    # [TODO] llm_model will be imported from revolve.llm
    llm_model = ChatOpenAI(
    model="gpt-4o",
    temperature=0.2,
    )
    llm_with_tools = llm_model.bind_tools(get_tools())
    messages = state.get("messages", [])

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def should_continue_tool_call(state: State):
    send = state.get("send", False)
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tool_executor"
    if send:
        log(last_message.content, send=send, level="workflow")
        
    return "__end__"

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
                    content=str(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}
