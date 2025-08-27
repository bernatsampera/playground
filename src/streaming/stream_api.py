from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import concurrent.futures
from event_emitter import event_emitter
from graph import create_sample_graph

app = FastAPI(title="Graph Event Streaming API", version="1.0.0")

class InitialState(BaseModel):
    message: str

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
        graph_factory = create_sample_graph()
        
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