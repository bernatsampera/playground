from chonkie import CodeChunker
from langchain_ollama import ChatOllama
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain.embeddings import OllamaEmbeddings
from langchain.chains import RetrievalQA
import warnings

warnings.filterwarnings("ignore")

# ---- Step 1: Set up vectorstore ----
embedding = OllamaEmbeddings(model="nomic-embed-text")
vectorstore = Chroma(
    collection_name="code-test",
    embedding_function=embedding,
    persist_directory=".chroma-test"
)

# ---- Step 2: Create symbolic index ----
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

# ---- Step 3: Chunk code using Chonkie ----
code = """
def hello_world():
    print("Hello, Chonkie!")

def hello_world_2():
    print("Hello, Chonkie 2!")
"""

chunker = CodeChunker(
    language="python",
    tokenizer_or_token_counter="character",
    chunk_size=100,
    include_nodes=False
)
chunks = chunker.chunk(code)

# Convert chunks to LangChain Document objects
documents = [Document(page_content=chunk.text) for chunk in chunks]
vectorstore.add_documents(documents)

# ---- Step 4: Build retrieval + LLM ----
retriever = vectorstore.as_retriever()
llm = ChatOllama(model="llama3.1")
rag_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type="stuff"
)

# ---- Step 5: Very minimal hybrid query router ----
def hybrid_query(question: str):
    # Try symbolic match first
    for func_name, data in symbolic_index.items():
        if func_name in question:
            return f"Symbolic Answer: {data['signature']}\n{data['description']}"

    # Fallback to RAG
    return rag_chain.run(question)


# ---- Step 6: Test ----
print("---- Test 1 ----, what does hello_world do?")
print(hybrid_query("What does hello_world do?"))

print("---- Test 3 ----, what does hello_world_2 do?")
print(hybrid_query("What does hello_world_2 do?"))