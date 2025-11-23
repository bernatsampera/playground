from ollama import chat

stream = chat(
    model="qwen3:14b",
    messages=[{"role": "user", "content": "What is the capital of France?"}],
    stream=True,
    think=True,
)
for chunk in stream:
    print(chunk["message"]["content"], end="", flush=True)
