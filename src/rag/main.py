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
    print("\nQuery: How to translate a sentence using the glossary?")
    result1 = rag_graph.query("How to retrieve the glossary for a user?")
    print("Answer:", result1["answer"])


if __name__ == "__main__":
    main() 