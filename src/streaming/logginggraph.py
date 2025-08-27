from typing import Optional, TypedDict, Callable
from langgraph.graph import StateGraph
import json

# Define state
class StateRequired(TypedDict):
    message: str
    count: int

class StateOptional(TypedDict, total=False):
    comment: Optional[str]

class State(StateRequired, StateOptional):
    pass

# Reusable state tracking wrapper with diff
def with_state_tracking(node_func: Callable[[State], State], node_name: str) -> Callable[[State], State]:
    def _truncate(value, max_len=80):
        str_val = str(value)
        return str_val if len(str_val) <= max_len else str_val[:max_len] + "..."
    
    def wrapper(state: State) -> State:
        print(f"\n--- {node_name} START ---")
        
        result = node_func(state)
        
        # Find changes
        changes = {}
        for k in result:
            if k not in state:
                changes[k] = ("NEW", _truncate(result[k]))
            elif result[k] != state[k]:
                changes[k] = (_truncate(state[k]), _truncate(result[k]))
        
        if changes:
            print("Changes:")
            for key, change in changes.items():
                if change[0] == "NEW":
                    print(f" NEW - {key}: {change[1]}")
                else:
                    print(f" CHANGE - {key}: {change[0]} -> {change[1]}")
        else:
            print("No changes")
        
        print(f"--- {node_name} END ---\n")
        return result
    
    return wrapper


# Custom StateGraph with automatic state tracking
class TrackedStateGraph(StateGraph):
    def add_node(self, key: str, action: Callable[[State], State]) -> None: # type: ignore
        # Wrap the node function with state tracking
        wrapped_action = with_state_tracking(action, key)
        super().add_node(key, wrapped_action) # type: ignore

# Define two simple nodes
def node1(state: State) -> State:
    return {"message": "Hello from Node 1", "count": state["count"] + 1}

def node2(state: State) -> State:
    return {"message": state["message"] + " -> Node 2", "count": state["count"] + 1, "comment": "This is a comment"}

# Create graph
graph = TrackedStateGraph(State)

# Add nodes (automatically wrapped with state tracking)
graph.add_node("node1", node1)
graph.add_node("node2", node2)

# Add edge
graph.add_edge("node1", "node2")

# Set entry and finish points
graph.set_entry_point("node1")
graph.set_finish_point("node2")

# Compile and run
runner = graph.compile()
result = runner.invoke({"message": "", "count": 0})

print("\nFinal result:")
print(json.dumps(result, indent=2))