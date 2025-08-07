from typing import Callable, TypedDict
from langgraph.graph import StateGraph


class State(TypedDict):
    message: str

def with_state_tracking(node_func: Callable[[State], State], node_name: str) -> Callable[[State], State]:
    def wrapper(state: State) -> State:
        print(f"--- {node_name} START ---")
        result = node_func(state)
        print(f"--- {node_name} END ---")
        return result
    return wrapper

class TrackedStateGraph(StateGraph):
    def add_node(self, key: str, action: Callable[[State], State]) -> None: # type: ignore
        wrapped_action = with_state_tracking(action, key)
        super().add_node(key, wrapped_action) # type: ignore

# Define two simple nodes
def node1(state: State) -> State:
    return {"message": "Hello from Node 1"}

def node2(state: State) -> State:
    return {"message": state["message"] + " -> Node 2"}

# Create graph
graph = TrackedStateGraph(State)

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