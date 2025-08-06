from typing import List
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.documents import Document
from chonkie import SemanticChunker
from rapidfuzz import fuzz
import os

class ChonkieStore:
    """Manages a Chroma vector store for code chunks and similarity searches."""

    def __init__(self, db_path: str = "./rag_chroma_db"):
        """Initialize Chroma vector store with persistent storage."""
        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)
        
        self.embedding = OllamaEmbeddings(model="nomic-embed-text")
        self.vector_store = Chroma(
            embedding_function=self.embedding,
            persist_directory=db_path
        )

    def add_code_chunks(self, code: str) -> None:
        """Chunk code and store unique chunks in the vector store."""
        chunker = SemanticChunker(
            threshold=0.5,
            chunk_size=2048,
            min_sentences=1,
            delim=["\n\n"]
        )
        
        chunks = chunker.chunk(code)
        sentences = [s for s in chunks[0].sentences if s.text.strip()]
        
        unique_sentences = [
            s for s in sentences 
            if not self._is_similar_content(s.text)
        ]
        
        documents = [
            Document(
                page_content=s.text.strip(),
                metadata={"type": self._detect_content_type(s.text)}
            )
            for s in unique_sentences
        ]
        print("documents", documents)
        
        if documents:
            self.vector_store.add_documents(documents=documents)

    def _is_similar_content(self, content: str, threshold: float = 200) -> bool:
        """Check if content is similar to existing documents."""
        similar_docs = self.vector_store.similarity_search_with_score(content, k=2)
        return any(score < threshold for _, score in similar_docs)

    def _score_keywords(self, keywords: List[str], text: str) -> float:
        """Calculate maximum similarity score for keywords against text."""
        return max(fuzz.token_set_ratio(k, text) for k in keywords)

    def _detect_content_type(self, text: str) -> str:
        """Determine if text is Python, SQL, or plain text based on keyword scores."""
        text = text.strip().lower()
        
        PYTHON_KEYWORDS = ['def', 'import', 'return', 'print', 'lambda', 'class', '#']
        SQL_KEYWORDS = ['select', 'from', 'where', 'insert', 'update', 'delete', '--', 'join']
        
        python_score = self._score_keywords(PYTHON_KEYWORDS, text)
        sql_score = self._score_keywords(SQL_KEYWORDS, text)
        
        max_score = max(python_score, sql_score)
        
        if max_score < 60:
            return "text"
        return "python" if python_score > sql_score else "sql"