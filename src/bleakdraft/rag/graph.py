from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage
from typing import Any, Dict
from .state import HybridState
from .vectorstore import VectorStoreManager

class RAGGraph:
    def __init__(self, vector_store_manager: VectorStoreManager):
        self.vector_store_manager = vector_store_manager
        self.llm = ChatOllama(model="llama3.2")
        self.graph = None
        self.app = None
        self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph with nodes and edges"""
        self.graph = StateGraph(HybridState)
        
        # Add nodes
        self.graph.add_node("rag_lookup", self._rag_lookup_node)
        self.graph.add_node("hybrid_llm", self._hybrid_llm_node)
        
        # Set entry point and edges
        self.graph.set_entry_point("rag_lookup")
        self.graph.add_edge("rag_lookup", "hybrid_llm")
        self.graph.add_edge("hybrid_llm", END)
        
        # Compile the graph
        self.app = self.graph.compile()
    
    def _rag_lookup_node(self, state: HybridState) -> HybridState:
        """RAG context retrieval node"""
        question = state["question"]
        docs = self.vector_store_manager.similarity_search(question, k=2)
        print("docs found", len(docs))
        print("docs", docs)
        
        context = "\n".join([d.page_content for d in docs])
        return {**state, "rag_context": context}
    
    def _hybrid_llm_node(self, state: HybridState) -> HybridState:
        """LLM response generation node"""
        prompt = f"""
You are a helpful assistant. Answer the user's question based on the following information.

User Question:
{state['question']}

RAG Context:
{state.get('rag_context', 'None')}
"""
        response = self.llm.invoke(prompt)
        if hasattr(response, 'content'):
            answer = str(response.content)
        else:
            answer = str(response)
        return {**state, "answer": answer.strip()}
    
    def query(self, question: str) -> HybridState:
        """Execute a query through the RAG graph"""
        if not self.app:
            raise ValueError("Graph not compiled. Call _build_graph first.")
        
        input_state: HybridState = {"question": question, "rag_context": None, "answer": None}
        result = self.app.invoke(input_state)
        return result  # type: ignore 