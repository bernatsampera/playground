from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.runnables import RunnableLambda
from langchain.vectorstores import Chroma
from langchain.embeddings import OllamaEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from chonkie import CodeChunker
import warnings
import os

warnings.filterwarnings("ignore")

# Create a directory for the ChromaDB persistence
chroma_db_path = "./rag_chroma_db"
os.makedirs(chroma_db_path, exist_ok=True)

# ---- Step 2: Code chunking + RAG loading ----
code = """
def hello_world():
    '''
    Prints Hello, Chonkie!
    '''
    print("Hello, Chonkie!")

def goodbye_night():
    '''
    Prints 'Good night!'
    '''
    print("Good night!")

def hello_world_2():
    '''
    Prints 'Hello, Chonkie 2!'
    '''
    print("Hello, Chonkie 2!")
"""


chunker = CodeChunker(language="python", tokenizer_or_token_counter="character", chunk_size=100)
chunks = chunker.chunk(code)

embedding = OllamaEmbeddings(model="nomic-embed-text")

# Initialize ChromaDB with persistent storage
rag_store = Chroma.from_texts(
    [c.text for c in chunks], 
    embedding=embedding,
    persist_directory=chroma_db_path
)

# Persist the database to disk
rag_store.persist()

# ---- Step 3: Define LangGraph state ----
from typing import TypedDict, Optional

class HybridState(TypedDict):
    question: str
    rag_context: Optional[str]
    answer: Optional[str]


# ---- Step 5: RAG context node ----
def rag_lookup_node(state: HybridState) -> HybridState:
    question = state["question"]
    docs = rag_store.similarity_search(question, k=2)
    print("docs found", len(docs))
    print("docs", docs)

    context = "\n".join([d.page_content for d in docs])
    return {**state, "rag_context": context}

# ---- Step 6: LLM node using Ollama ----
llm = ChatOllama(model="llama3.2")

def hybrid_llm_node(state: HybridState) -> HybridState:
    prompt = f"""
You are a helpful assistant. Answer the user's question based on the following information.

User Question:
{state['question']}

RAG Context:
{state.get('rag_context', 'None')}
"""
    response = llm.invoke(prompt)
    return {**state, "answer": response.content.strip()}

# ---- Step 7: Build LangGraph ----
graph = StateGraph(HybridState)
graph.add_node("rag_lookup", rag_lookup_node)
graph.add_node("hybrid_llm", hybrid_llm_node)
graph.set_entry_point("rag_lookup")
graph.add_edge("rag_lookup", "hybrid_llm")
graph.add_edge("hybrid_llm", END)
app = graph.compile()

# ---- Step 8: Run ----
result1 = app.invoke({"question": "What does hello_world do?"})

print("--- Result 1 ---")
print(result1["answer"])
