import warnings
import sys
import os

from .vectorstore import VectorStoreManager
from .graph import RAGGraph

# Sample code for testing
SAMPLE_CODE = """
def hello_world():
    '''
    Prints Hello, Chonkie!
    '''
    print("Hello, Chonkie!")

def goodbye_night():
    '''
    Prints 'Good night!'
    '''
    print("Good night!")

def hello_world_2():
    '''
    Prints 'Hello, Chonkie 2!'
    '''
    print("Hello, Chonkie 2!")
""" 

warnings.filterwarnings("ignore")

def main():
    """Main execution function"""
    # Initialize vector store manager
    vector_store_manager = VectorStoreManager()
    
    # Setup code chunks
    print("Setting up vector store with code chunks...")
    vector_store_manager.setup_code_chunks(SAMPLE_CODE)
    
    # Initialize RAG graph
    print("Initializing RAG graph...")
    rag_graph = RAGGraph(vector_store_manager)
    
    # Run queries
    print("\n--- Running RAG Queries ---")
    
    # Query 1
    print("\nQuery: What does hello_world do?")
    result1 = rag_graph.query("What does hello_world do?")
    print("Answer:", result1["answer"])
    
    # Query 2
    # print("\nQuery: What does goodbye_night do?")
    # result2 = rag_graph.query("What does goodbye_night do?")
    # print("Answer:", result2["answer"])

if __name__ == "__main__":
    main() 