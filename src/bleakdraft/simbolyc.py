from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.runnables import RunnableLambda

# ---- Step 1: Symbolic index ----
symbolic_index = {
    "hello_world": {
        "description": "Prints 'Hello, Chonkie!'",
        "signature": "def hello_world()"
    },
    "hello_world_2": {
        "description": "Prints 'Hello, Chonkie 2!'",
        "signature": "def hello_world_2()"
    }
}

# ---- Step 2: Define LangGraph state ----
from typing import TypedDict, Optional

class ToolState(TypedDict):
    question: str
    symbolic_info: Optional[str]
    answer: Optional[str]

# ---- Step 3: Symbolic lookup node ----
def symbolic_lookup_node(state: ToolState) -> ToolState:
    question = state["question"]
    for name, data in symbolic_index.items():
        if name in question:
            info = f"{data['signature']}\n{data['description']}"
            return {"question": question, "symbolic_info": info, "answer": None}
    return {"question": question, "symbolic_info": "No symbolic info found.", "answer": None}

# ---- Step 4: LLM node using Ollama ----
llm = ChatOllama(model="llama3.2")

def llm_response_node(state: ToolState) -> ToolState:
    prompt = f"""
You are a helpful assistant. Based on the following symbolic information, answer the user's question.

User Question:
{state['question']}

Symbolic Info:
{state['symbolic_info']}
"""
    response = llm.invoke(prompt)
    return {**state, "answer": response.content.strip()}

# ---- Step 5: Build LangGraph ----
graph = StateGraph(ToolState)
graph.add_node("symbolic_lookup", symbolic_lookup_node)
graph.add_node("llm_response", llm_response_node)
graph.set_entry_point("symbolic_lookup")
graph.add_edge("symbolic_lookup", "llm_response")
graph.add_edge("llm_response", END)
app = graph.compile()

# ---- Step 6: Run ----
result1 = app.invoke({"question": "What does hello_world do?"})
result2 = app.invoke({"question": "Tell me about hello_world_2"})
result3 = app.invoke({"question": "What is foo_bar?"})

print("--- Result 1 ---")
print(result1["answer"])
print("\n--- Result 2 ---")
print(result2["answer"])
print("\n--- Result 3 ---")
print(result3["answer"])
