from typing import TypedDict
from langgraph.graph import StateGraph


class State(TypedDict):
    message: str

# Define two simple nodes
def node1(state):
    return {"message": "Hello from Node 1"}

def node2(state):
    return {"message": state["message"] + " -> Node 2"}

# Create graph
graph = StateGraph(State)

# Add nodes
graph.add_node("node1", node1)
graph.add_node("node2", node2)

# Add edge
graph.add_edge("node1", "node2")

# Set entry and finish points
graph.set_entry_point("node1")
graph.set_finish_point("node2")

# Compile and run
runner = graph.compile()
result = runner.invoke({"message": ""})

print(result)