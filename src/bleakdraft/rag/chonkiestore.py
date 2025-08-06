from typing import Any, Dict, Optional, List, cast
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.documents import Document
from chonkie import Chunk, CodeChunker, RecursiveChunker, SemanticSentence
import os
from uuid import uuid4
import sys
from chonkie import ChromaHandshake, SemanticChunker, CodeChunker
from rapidfuzz import fuzz

class ChonkieStore:
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

    def add_code_chunks(self, text: str):
        """
        Process code into chunks and add unique chunks to the vector store.
        
        Args:
            code: Source code to be chunked and stored
            
        Returns:
            The configured Chroma vector store instance
        """
        
        chunker = SemanticChunker(
            # embedding_model="minishlab/potion-base-8M",  # Default model
            threshold=0.5,                               # Similarity threshold (0-1) or (1-100) or "auto"
            chunk_size=2048,                              # Maximum tokens per chunk
            min_sentences=1,                             # Initial sentences per chunk
            delim=["\n\n"]
        )
        chunks = chunker.chunk(text)

        sentences = chunks[0].sentences

        # Filter out empty sentences
        sentences = [sentence for sentence in sentences if sentence.text.strip()]

        unique_sentences = []
        for sentence in sentences:
            print("--------------START------------------")
            is_similar = self.sentence_similarity_search(sentence.text)
            if not is_similar:
                unique_sentences.append(sentence)

        documents = [Document(page_content=sentence.text.strip(), metadata={"type": self.detect_type(sentence.text)}) for sentence in unique_sentences]


        print("--------------END------------------")
        print("documents", documents)
        
        if len(documents) > 0:
            self.rag_store.add_documents(documents=documents)

        # for sentence in sentences:
        #     self.handshake.write(sentence)


    # 200 is just a guess, in future a better logic about this will be needed.
    def sentence_similarity_search(self, new_content: str, distance_threshold: float = 200) -> bool:
        """
        Check if new content is similar to existing documents in the vector store.
        
        Args:
            new_content: Content to check for similarity
            metadata: Optional metadata for the content
            distance_threshold: Threshold for considering documents similar (higher = more similar)
            
        Returns:
            True if similar document found, False otherwise
        """        
        
        # Search for similar documents with similarity scores
        # print("new_content", new_content[:10])
        similar_docs = self.rag_store.similarity_search_with_score(new_content, k=2)

        for doc, score in similar_docs:
            # print("doc", doc.page_content[:10])
            # print("score", score)
            # ChromaDB returns similarity scores: lower = more similar
            if score < distance_threshold:
                return True
          
        return False

    def score_keywords(self, keywords, text):
        return max([fuzz.token_set_ratio(k, text) for k in keywords])


    PYTHON_KEYWORDS = ['def', 'import', 'return', 'print', 'lambda', 'class', '#']
    SQL_KEYWORDS = ['select', 'from', 'where', 'insert', 'update', 'delete', '--', 'join']

    def detect_type(self,chunk: str) -> str:
        text = chunk.strip().lower()

        python_score = self.score_keywords(self.PYTHON_KEYWORDS, text)
        sql_score = self.score_keywords(self.SQL_KEYWORDS, text)

        # Debug (optional)
        print(f"PYTHON={python_score}, SQL={sql_score}, TEXT='{chunk[:30]}...'")

        max_score = max(python_score, sql_score)

        if max_score < 60:
            return "text"
        if python_score > sql_score:
            return "python"
        else:
            return "sql"

        