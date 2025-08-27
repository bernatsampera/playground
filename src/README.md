# Scripts Organization

This directory contains organized test scripts and utilities grouped by functionality:

## 📁 Directory Structure

### `audio/`

- **index.py** - Audio recording and transcription using Whisper

### `database/`

- **index.py** - SQLite database management utilities
- **manage_sqlite.py** - User management for workflows database
- **tunneldb.py** - Database tunneling and sync functionality
- **content.db** - SQLite database file

### `rag/`

- **main.py** - RAG (Retrieval-Augmented Generation) main entry point
- **load.py** - Data loading utilities for RAG
- **create_summary.py** - Summary generation functionality
- **chonkiestore.py** - Chunk storage implementation
- **graph.py** - Graph-based processing for RAG
- **pythoncodeparser.py** - Python code parsing utilities
- **vectorstore.py** - Vector storage implementation
- **state.py** - State management for RAG
- **simbolyc.py** - Symbolic processing utilities
- **example.md** / **example_small.md** - Example markdown files
- **README.md** - RAG-specific documentation

### `streaming/`

- **stream_api.py** - FastAPI streaming endpoint
- **event_emitter.py** - Event emission system
- **graph.py** - Graph processing for streaming
- **test_sse_client.py** - Server-Sent Events client testing
- **logginggraph.py** - Graph logging utilities
- **indenterror.py** - Indentation error handling
- **classify.py** - Classification utilities
- **detect_code.py** - Code detection functionality

### `text-processing/`

- **rapidfuzztest.py** - Fuzzy text matching using rapidfuzz
- **markdown_to_html.py** - Markdown to HTML conversion

### `utils/`

- **index.py** - Local file system utilities (model file finder)
- **delete.py** - File deletion utilities

## 🚀 Usage

Each directory contains related functionality. Navigate to the specific directory and run the scripts as needed:

```bash
# Example: Run audio transcription
cd audio && python index.py

# Example: Run text processing
cd text-processing && python rapidfuzztest.py

# Example: Run streaming API
cd streaming && python stream_api.py
```
