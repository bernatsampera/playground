from langchain.chat_models import init_chat_model


llm = init_chat_model("ollama:llama3.2")


print(llm.invoke("Hello, world!").content)
