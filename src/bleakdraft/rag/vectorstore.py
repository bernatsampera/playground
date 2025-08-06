from typing import Any, Dict, Optional, List
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.documents import Document
from chonkie import CodeChunker
import os
from uuid import uuid4
import sys

class VectorStoreManager:
    """
    Manages a Chroma vector store for code chunks and similarity search.
    Uses LangChain's Chroma integration for persistent storage and retrieval.
    """
    
    def __init__(self, chroma_db_path: str = "./rag_chroma_db"):
        """
        Initialize the vector store manager with persistent ChromaDB storage.
        
        Args:
            chroma_db_path: Directory path for storing the ChromaDB data
        """
        self.chroma_db_path = chroma_db_path
        os.makedirs(chroma_db_path, exist_ok=True)
        
        # Initialize Ollama embeddings for text vectorization
        self.embedding = OllamaEmbeddings(model="nomic-embed-text")
        
        # Initialize ChromaDB with persistent storage
        # This creates a persistent client that saves data to disk
        self.rag_store = Chroma(
            embedding_function=self.embedding,
            persist_directory=self.chroma_db_path
        )
    
    def setup_code_chunks(self, code: str):
        """
        Process code into chunks and add unique chunks to the vector store.
        
        Args:
            code: Source code to be chunked and stored
            
        Returns:
            The configured Chroma vector store instance
        """
        # Use CodeChunker to split code into manageable pieces
        chunker = CodeChunker(
            language="python", 
            tokenizer_or_token_counter="character", 
            chunk_size=100
        )
        chunks = chunker.chunk(code)


        chunk_texts = [chunk.text[:10] for chunk in chunks]
        print("chunk_texts", chunk_texts)


        # Filter out chunks that are too similar to existing content
        unique_chunks = []
        for chunk in chunks:
            print("--------------START------------------")
            print("chunk", chunk.text[:100])
            is_similar = self.chunk_similarity_search(chunk.text)
            if not is_similar:
                unique_chunks.append(chunk)
            print("--------------END------------------")

        # Add unique chunks as documents to the vector store
        if unique_chunks:
            # Convert chunks to LangChain Document objects
            documents = []
            for chunk in unique_chunks:
                doc = Document(
                    page_content=chunk.text,
                    metadata={"source": "code_chunk"}
                )
                documents.append(doc)
            
            # Add documents with unique IDs
            uuids = [str(uuid4()) for _ in range(len(documents))]
            self.rag_store.add_documents(documents=documents, ids=uuids)
        
        return self.rag_store
    
    def similarity_search(self, query: str, k: int = 2):
        """
        Perform similarity search on the vector store.
        
        Args:
            query: Search query text
            k: Number of similar documents to return
            
        Returns:
            List of similar documents
        """
        return self.rag_store.similarity_search(query, k=k)

    def chunk_similarity_search(self, new_content: str, metadata: Optional[Dict] = None, distance_threshold: float = 0.8) -> bool:
        """
        Check if new content is similar to existing documents in the vector store.
        
        Args:
            new_content: Content to check for similarity
            metadata: Optional metadata for the content
            distance_threshold: Threshold for considering documents similar (higher = more similar)
            
        Returns:
            True if similar document found, False otherwise
        """        
        print("new content", new_content)
        
        # Search for similar documents with similarity scores
        similar_docs = self.rag_store.similarity_search_with_score(new_content, k=2)

        for doc, score in similar_docs:
            print("similar_doc", doc.page_content)
            print("similarity_score", score)
            # ChromaDB returns similarity scores: lower = more similar
            if score < distance_threshold:
                return True
          
        return False

    def update_chunk_by_id(self, chunk_id: str, new_content: str):
        """
        Update a specific code chunk by its chunk_id.
        
        Args:
            chunk_id: The UUID of the chunk to update
            new_content: New content for the chunk
        """
        updated_doc = Document(
            page_content=new_content,
            metadata={"source": "code_chunk", "chunk_id": chunk_id}
        )
        self.rag_store.update_document(document_id=chunk_id, document=updated_doc)
        print(f"Updated chunk {chunk_id}")

    def delete_chunk_by_id(self, chunk_id: str):
        """
        Delete a specific code chunk by its chunk_id.
        
        Args:
            chunk_id: The UUID of the chunk to delete
        """
        self.rag_store.delete(ids=[chunk_id])
        print(f"Deleted chunk {chunk_id}")

    def search_by_source(self, query: str, source: str = "code_chunk", k: int = 5):
        """
        Search for documents with a specific source filter.
        
        Args:
            query: Search query
            source: Source filter (e.g., "code_chunk", "documentation")
            k: Number of results to return
            
        Returns:
            List of matching documents
        """
        return self.rag_store.similarity_search(
            query, 
            k=k, 
            filter={"source": source}
        )

    def get_all_chunks_by_source(self, source: str = "code_chunk"):
        """
        Get all chunks of a specific source type.
        
        Args:
            source: Source filter to apply
            
        Returns:
            List of all documents with the specified source
        """
        # This is a simple approach - in practice you might want to use
        # the underlying Chroma client for more complex queries
        return self.rag_store.similarity_search("", k=1000, filter={"source": source})

    def get_chunk_by_id(self, chunk_id: str):
        """
        Retrieve a specific chunk by its ID.
        
        Args:
            chunk_id: The UUID of the chunk to retrieve
            
        Returns:
            The document if found, None otherwise
        """
        try:
            # Search with a filter for the specific chunk_id
            results = self.rag_store.similarity_search(
                "", 
                k=1, 
                filter={"chunk_id": chunk_id}
            )
            return results[0] if results else None
        except Exception as e:
            print(f"Error retrieving chunk {chunk_id}: {e}")
            return None

