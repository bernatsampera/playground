from typing import Any, Dict, Optional
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from chonkie import CodeChunker
import os

class VectorStoreManager:
    def __init__(self, chroma_db_path: str = "./rag_chroma_db"):
        self.chroma_db_path = chroma_db_path
        os.makedirs(chroma_db_path, exist_ok=True)
        self.embedding = OllamaEmbeddings(model="nomic-embed-text")
        
        # Initialize ChromaDB with persistent storage (empty collection)
        self.rag_store = Chroma(
            embedding_function=self.embedding,
            persist_directory=self.chroma_db_path
        )
    
    def setup_code_chunks(self, code: str):
        """Setup vector store with code chunks"""
        chunker = CodeChunker(
            language="python", 
            tokenizer_or_token_counter="character", 
            chunk_size=100
        )
        chunks = chunker.chunk(code)

        different_docs = []
        for chunk in chunks:
            print("--------------START------------------")
            print("chunk", chunk.text[:100])
            is_similar = self.chunk_similarity_search(chunk.text)
            if not is_similar:
                different_docs.append(chunk)
            print("--------------END------------------")

        print("different_docs", different_docs)
        
        # Add documents to existing ChromaDB instance
        if different_docs:
            self.rag_store.add_texts([c.text for c in different_docs])
            # Persist the database to disk
            self.rag_store.persist()
        
        return self.rag_store
    
    def similarity_search(self, query: str, k: int = 2):
        """Perform similarity search on the vector store"""
        return self.rag_store.similarity_search(query, k=k)

    def chunk_similarity_search(self, new_content: str, metadata: Optional[Dict] = None, distance_threshold: float = 200) -> bool:
        """
        Add new document only if it's significantly different from existing ones.
        
        Args:
            new_content: Content to add
            metadata: Optional metadata
            distance_threshold: Threshold for considering documents similar (lower = more similar)
            
        Returns:
            True if similar document found, False otherwise
        """        
        print("new content", new_content)
        similar_docs = self.rag_store.similarity_search_with_score(new_content, k=2)

        for _, score in similar_docs:
            print("similar_doc", _.page_content)
            print("distance_score", score)
            # ChromaDB returns distance scores: lower = more similar
            if score < distance_threshold:
                return True
          
        return False

