import warnings
import sys
import os

from .vectorstore import VectorStoreManager
from .graph import RAGGraph
from langchain_ollama import ChatOllama


warnings.filterwarnings("ignore")

def main():
    """Main execution function"""
    # Initialize vector store manager
    vector_store_manager = VectorStoreManager()
    

    # Get all docs from the database
    docs = vector_store_manager.rag_store.get(include=["documents"])

    # for doc in docs['documents']:
    #     print("doc", doc[0:20])
    #     print("-"*100)

    for doc in docs["ids"]:
        print("doc", doc[0:20])
        print("-"*100)

    docs_str = "\n".join([doc for doc in docs['documents']])

    llm = ChatOllama(model="gemma3:12b")
    # response = llm.invoke(f"You have to create a summary of the following text: {docs_str}")
    # print("response", response)



if __name__ == "__main__":
    main() 