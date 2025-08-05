from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.runnables import RunnableLambda
from langchain.vectorstores import Chroma
from langchain.embeddings import OllamaEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from chonkie import CodeChunker
import warnings
import ast

warnings.filterwarnings("ignore")

# ---- Step 1: Symbolic index ----
# symbolic_index = {
#     "hello_world": {
#         "description": "Prints 'Hello, Chonkie!'",
#         "signature": "def hello_world()"
#     },
#     "hello_world_2": {
#         "description": "Prints 'Hello, Chonkie 2!'",
#         "signature": "def hello_world_2()"
#     }
# }

# ---- Step 2: Code chunking + RAG loading ----
code = """
def hello_world():
    '''
    Prints Hello, Chonkie!
    '''
    print("Hello, Chonkie!")

def hello_world_2():
    '''
    Prints 'Hello, Chonkie 2!'
    '''
    print("Hello, Chonkie 2!")
"""

def build_symbolic_index_from_code(code: str):
    tree = ast.parse(code)
    index = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            name = node.name
            args = [arg.arg for arg in node.args.args]
            signature = f"def {name}({', '.join(args)})"
            docstring = ast.get_docstring(node) or "No description."
            index[name] = {
                "signature": signature,
                "description": docstring.strip()
            }

    return index



symbolic_index = build_symbolic_index_from_code(code)
print("---- Symbolic Index ----")
print(symbolic_index)


chunker = CodeChunker(language="python", tokenizer_or_token_counter="character", chunk_size=100)
chunks = chunker.chunk(code)

embedding = OllamaEmbeddings(model="nomic-embed-text")
rag_store = Chroma.from_texts([c.text for c in chunks], embedding=embedding)

# ---- Step 3: Define LangGraph state ----
from typing import TypedDict, Optional

class HybridState(TypedDict):
    question: str
    symbolic_info: Optional[str]
    rag_context: Optional[str]
    answer: Optional[str]

# ---- Step 4: Symbolic lookup node ----
def symbolic_lookup_node(state: HybridState) -> HybridState:
    question = state["question"]
    for name, data in symbolic_index.items():
        if name in question:
            info = f"{data['signature']}\n{data['description']}"
            return {**state, "symbolic_info": info}
    return {**state, "symbolic_info": None}

# ---- Step 5: RAG context node ----
def rag_lookup_node(state: HybridState) -> HybridState:
    question = state["question"]
    docs = rag_store.similarity_search(question, k=2)
    context = "\n".join([d.page_content for d in docs])
    return {**state, "rag_context": context}

# ---- Step 6: LLM node using Ollama ----
llm = ChatOllama(model="llama3.2")

def hybrid_llm_node(state: HybridState) -> HybridState:
    prompt = f"""
You are a helpful assistant. Answer the user's question based on the following information.

User Question:
{state['question']}

Symbolic Info:
{state.get('symbolic_info', 'None')}

RAG Context:
{state.get('rag_context', 'None')}
"""
    response = llm.invoke(prompt)
    return {**state, "answer": response.content.strip()}

# ---- Step 7: Build LangGraph ----
graph = StateGraph(HybridState)
graph.add_node("symbolic_lookup", symbolic_lookup_node)
graph.add_node("rag_lookup", rag_lookup_node)
graph.add_node("hybrid_llm", hybrid_llm_node)
graph.set_entry_point("symbolic_lookup")
graph.add_edge("symbolic_lookup", "rag_lookup")
graph.add_edge("rag_lookup", "hybrid_llm")
graph.add_edge("hybrid_llm", END)
app = graph.compile()

# ---- Step 8: Run ----
result1 = app.invoke({"question": "What does hello_world do?"})
result2 = app.invoke({"question": "Tell me about hello_world_2"})
result3 = app.invoke({"question": "What function prints 2?"})

print("--- Result 1 ---")
print(result1["answer"])
print("\n--- Result 2 ---")
print(result2["answer"])
print("\n--- Result 3 ---")
print(result3["answer"])
