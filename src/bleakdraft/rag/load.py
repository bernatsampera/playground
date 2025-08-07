import warnings
import sys
import os

from .vectorstore import VectorStoreManager
from .graph import RAGGraph
from .chonkiestore import ChonkieStore

# Sample code for testing
SAMPLE_TEXT = '''
def create_interrupt_payload(text: str) -> dict:
    """Creates interrupt payload."""
    return {"text_to_revise": text}

def process_human_input(state: State, text_key: str) -> dict:
    """Processes human input for text key."""
    value = interrupt(create_interrupt_payload(state[text_key]))
    return {text_key: value}

def build_workflow() -> StateGraph:
    """Configures state graph workflow."""
    graph_builder = StateGraph(State)
    graph_builder.add_node("human_node_1", lambda state: process_human_input(state, "text_1"))
    graph_builder.add_node("human_node_2", lambda state: process_human_input(state, "text_2"))
    graph_builder.add_edge(START, "human_node_1")
    graph_builder.add_edge(START, "human_node_2")
    return graph_builder

def initialize_workflow() -> tuple[StateGraph, InMemorySaver]:
    """Initializes workflow with checkpointer."""
    checkpointer = InMemorySaver()
    graph = build_workflow().compile(checkpointer=checkpointer)
    return graph, checkpointer

def create_thread_config() -> RunnableConfig:
    """Creates config with unique thread ID."""
    return {"configurable": {"thread_id": str(uuid4())}}

def process_resume_map(parent, thread_config: RunnableConfig) -> dict:
    """Creates resume map from interrupt states."""
    return {
        i.interrupt_id: f"human input for prompt {i.value}"
        for i in parent.get_state(thread_config).interrupts
    }

def main():
    """Executes workflow."""
    graph, checkpointer = initialize_workflow()
    config = create_thread_config()
    initial_state = {"text_1": "original text 1", "text_2": "original text 2"}
    graph.invoke(initial_state, config=config)
    resume_map = process_resume_map(graph, config)
    result = graph.invoke(Command(resume=resume_map), config=config)
    print(result)
''' 

warnings.filterwarnings("ignore")

def main():
    """Main execution function"""
    # Initialize vector store manager
    # vector_store_manager = VectorStoreManager()
    chonkie_store = ChonkieStore()
    chonkie_store.add_code_chunks(SAMPLE_TEXT)
    
    # Setup code chunks
    # vector_store_manager.setup_code_chunks(SAMPLE_CODE)
    # vector_store_manager.setup_semantic_chunks(SAMPLE_CODE)
    

if __name__ == "__main__":
    main() 



