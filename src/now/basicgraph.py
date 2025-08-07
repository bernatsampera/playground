from typing import Callable, TypedDict, Optional, AsyncGenerator
from langgraph.graph import StateGraph
import asyncio
import json
from datetime import datetime
import queue
import threading
from contextlib import contextmanager

class State(TypedDict):
    message: str

class EventEmitter:
    def __init__(self):
        self.event_queue: queue.Queue = queue.Queue()
        self.completed = threading.Event()
        self.execution_started = False
    
    def emit_event_sync(self, node_name: str, state: State):
        """Synchronous method to emit events from non-async contexts"""
        event_data = {
            "node_name": node_name,
            "state": state,
            "timestamp": datetime.now().isoformat()
        }
        self.event_queue.put(event_data)
    
    def start_execution(self):
        """Signal that a new graph execution is starting"""
        self.reset()
        self.execution_started = True
        start_event = {
            "type": "execution_start",
            "message": "Graph execution started",
            "timestamp": datetime.now().isoformat()
        }
        self.event_queue.put(start_event)
    
    def signal_completion(self):
        """Signal that the graph execution is complete"""
        if self.execution_started:
            completion_event = {
                "type": "execution_complete",
                "message": "Graph execution completed successfully",
                "timestamp": datetime.now().isoformat()
            }
            self.event_queue.put(completion_event)
        self.completed.set()
    
    def signal_error(self, error_msg: str):
        """Signal that an error occurred during execution"""
        if self.execution_started:
            error_event = {
                "type": "execution_error",
                "message": f"Graph execution failed: {error_msg}",
                "timestamp": datetime.now().isoformat()
            }
            self.event_queue.put(error_event)
        self.completed.set()
    
    def reset(self):
        """Reset the event emitter for a new execution"""
        # Clear any remaining items in queue
        while not self.event_queue.empty():
            try:
                self.event_queue.get_nowait()
            except queue.Empty:
                break
        self.completed.clear()
        self.execution_started = False
    
    @contextmanager
    def execution_context(self):
        """Context manager for handling graph execution lifecycle"""
        try:
            self.start_execution()
            yield self
        except Exception as e:
            self.signal_error(str(e))
            raise
        else:
            self.signal_completion()
    
    def create_and_run_graph(self, initial_state: dict, graph_factory_func: Callable) -> dict:
        """
        Create and run a graph within the execution context.
        
        Args:
            initial_state: The initial state for the graph
            graph_factory_func: A function that creates and returns a compiled graph
        
        Returns:
            The final state after graph execution
        """
        with self.execution_context():
            print(f"Creating and running graph with initial state: {initial_state}")
            
            # Create and compile the graph using the factory function
            runner = graph_factory_func()
            
            # Run the graph
            result = runner.invoke(initial_state)
            
            # Emit final result
            result_state: State = {"message": result.get("message", "")}
            print(f"Final result: {result_state}")
            self.emit_event_sync("GRAPH_COMPLETE", result_state)
            
            return result
    
    async def get_events(self) -> AsyncGenerator[str, None]:
        """Generate SSE events until completion is signaled"""
        while not self.completed.is_set():
            try:
                # Try to get event with timeout
                event = self.event_queue.get(timeout=0.5)
                yield f"data: {json.dumps(event)}\n\n"
                self.event_queue.task_done()
            except queue.Empty:
                # Send keep-alive ping if not completed
                if not self.completed.is_set():
                    yield "data: {\"type\": \"ping\"}\n\n"
                await asyncio.sleep(0.1)
        
        # Send any remaining events after completion
        while not self.event_queue.empty():
            try:
                event = self.event_queue.get_nowait()
                yield f"data: {json.dumps(event)}\n\n"
                self.event_queue.task_done()
            except queue.Empty:
                break
        
        # Send final completion event if we haven't sent one yet
        if self.execution_started:
            final_event = {
                "type": "stream_end",
                "message": "Event stream ended",
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(final_event)}\n\n"

# Global event emitter instance
event_emitter = EventEmitter()

def with_state_tracking(node_func: Callable[[State], State], node_name: str) -> Callable[[State], State]:
    def wrapper(state: State) -> State:
        result = node_func(state)
        # Emit event synchronously
        event_emitter.emit_event_sync(node_name, result)
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

# Compile the graph (ready for use)
runner = graph.compile()

# Note: The graph execution is now handled by the FastAPI endpoint
# To test, run: python stream_api.py