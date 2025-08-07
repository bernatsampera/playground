from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Callable
import asyncio
import concurrent.futures
from basicgraph import TrackedStateGraph, State, event_emitter

app = FastAPI(title="Graph Event Streaming API", version="1.0.0")

class InitialState(BaseModel):
    message: str

def create_graph_factory() -> Callable:
    """Factory function to create and compile a graph"""
    def factory():
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

        # Compile and return
        return graph.compile()
    
    return factory

@app.post("/stream-graph")
async def stream_graph_execution(initial_state: InitialState):
    """
    Stream graph execution events via Server-Sent Events.
    
    Send a POST request with initial state in the body:
    {
        "message": "Your initial message here"
    }
    
    The response will be a stream of SSE events showing state changes.
    """
    try:
        # Convert Pydantic model to dict
        state_dict = initial_state.model_dump()
        
        # Create the graph factory
        graph_factory = create_graph_factory()
        
        # Run the graph in a separate thread to avoid blocking
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Schedule the graph execution using the event emitter's method
            future = loop.run_in_executor(
                executor, 
                event_emitter.create_and_run_graph, 
                state_dict, 
                graph_factory
            )
        
        # Return streaming response
        return StreamingResponse(
            event_emitter.get_events(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running graph: {str(e)}")

@app.get("/")
async def root():
    return {
        "message": "Graph Event Streaming API", 
        "endpoints": {
            "/stream-graph": "POST - Stream graph execution events",
            "/docs": "GET - API documentation"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)