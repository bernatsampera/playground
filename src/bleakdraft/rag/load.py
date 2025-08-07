import warnings
import sys
import os

from .vectorstore import VectorStoreManager
from .graph import RAGGraph
from .chonkiestore import ChonkieStore

# Sample code for testing
SAMPLE_TEXT = '''
from typing import TypedDict
from uuid import uuid4
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import RunnableConfig, Command

class State(TypedDict):
    """State dictionary to hold text data."""
    text_1: str
    text_2: str

def create_interrupt_payload(text: str) -> dict:
    """Create a standardized interrupt payload for human input."""
    return {"text_to_revise": text}

def process_human_input(state: State, text_key: str) -> dict:
    """
    Process human input for a specific text key in the state.
    
    Args:
        state: The current state dictionary
        text_key: The key in the state to process (e.g., 'text_1')
    
    Returns:
        Updated state fragment with the processed text
    """
    value = interrupt(create_interrupt_payload(state[text_key]))
    return {text_key: value}

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



