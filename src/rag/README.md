# RAG System Structure

This directory contains a modular RAG (Retrieval-Augmented Generation) system built with LangGraph and ChromaDB.

## Structure

```
rag/
├── state.py          # State definitions and types
├── vectorstore.py    # Vector store setup and management
├── graph.py          # LangGraph definition and nodes
├── main.py           # Main execution script
├── example.py        # Example usage
└── README.md         # This file
```

## Components

### `state.py`

- Defines the `HybridState` TypedDict for the LangGraph state
- Contains question, RAG context, and answer fields

### `vectorstore.py`

- `VectorStoreManager` class for ChromaDB operations
- Code chunking functionality using Chonkie
- Sample code for testing
- Handles vector store persistence

### `graph.py`

- `RAGGraph` class that builds and manages the LangGraph
- Contains RAG lookup and LLM nodes
- Provides a simple query interface

### `main.py`

- Main execution script that demonstrates the full workflow
- Sets up vector store, initializes graph, and runs queries

### `example.py`

- Example usage showing how to use the modular components
- Demonstrates the API for the restructured system

## Usage

```python
from bleakdraft.rag.vectorstore import VectorStoreManager
from bleakdraft.rag.graph import RAGGraph

# Initialize components
vector_store = VectorStoreManager()
vector_store.setup_code_chunks(your_code)

# Create and use RAG system
rag_system = RAGGraph(vector_store)
result = rag_system.query("Your question here")
print(result["answer"])
```

## Benefits of This Structure

1. **Separation of Concerns**: Each file has a specific responsibility
2. **Modularity**: Components can be used independently
3. **Maintainability**: Easier to modify individual parts
4. **Testability**: Each component can be tested separately
5. **Reusability**: Components can be reused in different contexts
