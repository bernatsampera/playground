# Supervisor-Agent Pattern Blueprint

## Overview

This document describes a reusable supervisor-agent pattern for building LangGraph applications with a central supervisor that orchestrates tool execution through a dedicated tools node.

## Architecture

The pattern consists of three main components:

1. **Supervisor Node** - The "brain" that decides what action to take next
2. **Supervisor Tools Node** - The "hands" that executes the chosen tools
3. **Final Processing Node** - Handles final data transformation/output

## Core State Structure

```python
from typing import Annotated, List, TypedDict
from langchain_core.messages import MessageLikeRepresentation

class SupervisorStateInput(TypedDict):
    """Initial input for the supervisor graph"""
    # Core content being worked on
    content: str = Field(default="", description="Main content/data being processed")

class SupervisorState(SupervisorStateInput):
    """Complete state for the supervisor graph"""
    # Essential tracking variables
    conversation_history: Annotated[list[MessageLikeRepresentation], override_reducer]
    iteration_count: int = 0
```

## Essential Tools

### Action Tool

```python
class ActionTool(BaseModel):
    """Performs the main action of the agent"""
    action_input: str = Field(description="Input for the action to perform")
```

### Think Tool

```python
from langchain_core.tools import tool

@tool(description="Mandatory reflection tool. Analyze results and plan next action.")
def think_tool(reflection: str) -> str:
    """Analyze the last result, identify gaps, and plan the next action.

    You MUST use this tool immediately after every ActionTool call.

    Args:
        reflection: Structured analysis of the last result and next steps

    Returns:
        Confirmation and instruction to proceed
    """
    return f"Reflection recorded. {reflection}"
```

### Finish Tool

```python
class FinishTool(BaseModel):
    """Concludes the process when complete"""
    pass
```

## Node Implementation

### Supervisor Node

```python
async def supervisor_node(
    state: SupervisorState,
    config: RunnableConfig,
) -> Command[Literal["supervisor_tools"]]:
    """The 'brain' of the agent. It decides the next action."""

    tools = [
        ActionTool,
        FinishTool,
        think_tool,
    ]

    tools_model = create_llm_with_tools(tools=tools, config=config)

    # Format conversation history for context
    messages = state.get("conversation_history", [])
    messages_summary = get_buffer_string_with_tools(messages)

    # Build system prompt with current state
    system_message = SystemMessage(
        content=YOUR_SYSTEM_PROMPT.format(
            content=state.get("content", ""),
            messages_summary=messages_summary,
            max_iterations=MAX_ITERATIONS,
        )
    )

    human_message = HumanMessage(content="Start the process.")
    prompt = [system_message, human_message]

    response = await tools_model.ainvoke(prompt)

    return Command(
        goto="supervisor_tools",
        update={
            "conversation_history": [response],
            "iteration_count": state.get("iteration_count", 0) + 1,
        },
    )
```

### Supervisor Tools Node

```python
async def supervisor_tools_node(
    state: SupervisorState,
    config: RunnableConfig,
) -> Command[Literal["supervisor", "final_processing"]]:
    """The 'hands' of the agent. Executes tools and returns routing Command."""

    content = state.get("content", "")
    last_message = state["conversation_history"][-1]
    iteration_count = state.get("iteration_count", 0)

    # Check iteration limits
    exceeded_iterations = iteration_count >= MAX_TOOL_CALL_ITERATIONS

    # If no tool calls or exceeded iterations, finish
    if not last_message.tool_calls or exceeded_iterations:
        return Command(goto="final_processing")

    all_tool_messages = []

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        if tool_name == "FinishTool":
            return Command(goto="final_processing")

        elif tool_name == "think_tool":
            # Record reflection for next supervisor turn
            response_content = tool_args["reflection"]
            all_tool_messages.append(
                ToolMessage(
                    content=response_content,
                    tool_call_id=tool_call["id"],
                    name=tool_name,
                )
            )

        elif tool_name == "ActionTool":
            # Execute the main action
            action_input = tool_args["action_input"]
            result = await your_action_function.ainvoke({
                "action_input": action_input,
                "content": content,
            })

            # Update state with results
            content = result["content"]

            all_tool_messages.append(
                ToolMessage(
                    content="Action completed successfully",
                    tool_call_id=tool_call["id"],
                    name=tool_name,
                )
            )

    return Command(
        goto="supervisor",
        update={
            "content": content,
            "conversation_history": all_tool_messages,
        },
    )
```

### Final Processing Node

```python
async def final_processing(
    state: SupervisorState,
    config: RunnableConfig
) -> dict:
    """Final processing and output generation"""

    content = state.get("content", "")

    if not content:
        return {"final_result": {}}

    # Process final output as needed
    final_result = await process_final_output(content, config)

    return {"final_result": final_result}
```

## Utility Functions

### Message Buffer Formatter

```python
def get_buffer_string_with_tools(messages: list[BaseMessage]) -> str:
    """Return a readable transcript showing roles, including tool names."""
    lines = []
    for m in messages:
        if isinstance(m, HumanMessage):
            lines.append(f"Human: {m.content}")
        elif isinstance(m, AIMessage):
            ai_content = f"AI: {m.content}"
            if hasattr(m, 'tool_calls') and m.tool_calls:
                tool_calls_str = ", ".join([
                    f"{tc.get('name', 'unknown')}({tc.get('args', {})})"
                    for tc in m.tool_calls
                ])
                ai_content += f" [Tool calls: {tool_calls_str}]"
            lines.append(ai_content)
        elif isinstance(m, SystemMessage):
            lines.append(f"System: {m.content}")
        elif isinstance(m, ToolMessage):
            tool_name = (
                getattr(m, "name", None) or
                getattr(m, "tool", None) or
                "unknown_tool"
            )
            lines.append(f"Tool[{tool_name}]: {m.content}")
        else:
            lines.append(f"{m.__class__.__name__}: {m.content}")
    return "\n".join(lines)
```

### State Reducer

```python
import operator

def override_reducer(current_value, new_value):
    """Reducer that allows new value to completely replace the old one."""
    if isinstance(new_value, dict) and new_value.get("type") == "override":
        return new_value.get("value", new_value)
    return operator.add(current_value, new_value)
```

## Graph Assembly

```python
from langgraph.graph import START, END, StateGraph

# Create the workflow
workflow = StateGraph(SupervisorState, input_schema=SupervisorStateInput)

# Add nodes
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("supervisor_tools", supervisor_tools_node)
workflow.add_node("final_processing", final_processing)

# Add edges
workflow.add_edge(START, "supervisor")

# Compile the graph
graph = workflow.compile()
```

## Key Pattern Benefits

1. **Separation of Concerns**: Supervisor decides, tools execute
2. **Iteration Control**: Built-in iteration counting and limits
3. **State Management**: Clear state flow between nodes
4. **Tool Reflection**: Mandatory think step for deliberate action
5. **Extensible**: Easy to add new tools and processing steps
6. **Debuggable**: Clear conversation history and tool execution tracking

## Usage Guidelines

1. Always use the think tool after action tools for reflection
2. Set appropriate iteration limits to prevent infinite loops
3. Include comprehensive context in system prompts
4. Use the message buffer formatter for readable conversation history
5. Implement proper error handling in action functions
6. Test with mock tools before integrating real actions
