import warnings
import sys
import os

from .vectorstore import VectorStoreManager
from .graph import RAGGraph



warnings.filterwarnings("ignore")

def main():
    """Main execution function"""
    # Initialize vector store manager
    vector_store_manager = VectorStoreManager()
    
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
    print("\nQuery: What does goodbye_night do?")
    result2 = rag_graph.query("What does goodbye_night do?")
    print("Answer:", result2["answer"])

if __name__ == "__main__":
    main() 