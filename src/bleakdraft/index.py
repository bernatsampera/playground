from chonkie import CodeChunker

# Basic initialization with default parameters
chunker = CodeChunker(
    language="python",                 # Specify the programming language
    tokenizer_or_token_counter="character", # Default tokenizer (or use "gpt2", etc.)
    chunk_size=100,                    # Maximum tokens per chunk
    include_nodes=False                # Optionally include AST nodes in output
)

code = """
def hello_world():
    print("Hello, Chonkie!")

def hello_world_2():
    print("Hello, Chonkie 2!")


"""
chunks = chunker.chunk(code)

for chunk in chunks:
    print(f"Chunk text: {chunk.text}")
    print(f"Token count: {chunk.token_count}")
    # print(f"Language: {chunk.lang}")
    if chunk.nodes:
        print(f"Node count: {len(chunk.nodes)}")