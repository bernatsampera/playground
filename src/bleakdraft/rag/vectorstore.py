from langchain.vectorstores import Chroma
from langchain.embeddings import OllamaEmbeddings
from chonkie import CodeChunker
import os

class VectorStoreManager:
    def __init__(self, chroma_db_path: str = "./rag_chroma_db"):
        self.chroma_db_path = chroma_db_path
        os.makedirs(chroma_db_path, exist_ok=True)
        self.embedding = OllamaEmbeddings(model="nomic-embed-text")
        self.rag_store = None
    
    def setup_code_chunks(self, code: str):
        """Setup vector store with code chunks"""
        chunker = CodeChunker(
            language="python", 
            tokenizer_or_token_counter="character", 
            chunk_size=100
        )
        chunks = chunker.chunk(code)
        
        # Initialize ChromaDB with persistent storage
        self.rag_store = Chroma.from_texts(
            [c.text for c in chunks], 
            embedding=self.embedding,
            persist_directory=self.chroma_db_path
        )
        
        # Persist the database to disk
        self.rag_store.persist()
        return self.rag_store
    
    def similarity_search(self, query: str, k: int = 2):
        """Perform similarity search on the vector store"""
        if not self.rag_store:
            raise ValueError("Vector store not initialized. Call setup_code_chunks first.")
        return self.rag_store.similarity_search(query, k=k)

