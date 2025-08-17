import markdown


post_content_markdown = """
## Services and Libraries  
- **langgraph** – graph‑based workflow engine for LLM applications.  
- **langgraph.checkpoint.memory.InMemorySaver** – keeps state in RAM.  
- **langgraph.checkpoint.sqlite.SqliteSaver** – persists state to a SQLite file.  
- **langchain.chat_models.init_chat_model** – loads a LLM (e.g., Gemini).  
- **dotenv.load_dotenv** – loads environment variables for secure credentials.

## Implementation Details of the Topic  
1. **Initialize the LLM**  
   ```python
   llm = init_chat_model("google_genai:gemini-2.5-flash-lite")
   ```

2. **Define the chatbot node** – returns the LLM’s reply.  
   ```python
   def chatbot(state: State):
       return {"messages": [llm.invoke(state["messages"])]}
   ```

3. **Build the graph**  
   ```python
   graph_builder = StateGraph(State)
   graph_builder.add_node("chatbot", chatbot)
   graph_builder.add_edge(START, "chatbot")
   graph_builder.add_edge("chatbot", END)
   ```

4. **Choose a checkpointer**  
   *In‑memory* (short‑term sessions):  
   ```python
   from langgraph.checkpoint.memory import InMemorySaver
   checkpointer = InMemorySaver()
   ```
   *SQLite* (long‑term persistence):  
   ```python
   import sqlite3
   from langgraph.checkpoint.sqlite import SqliteSaver
   conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
   checkpointer = SqliteSaver(conn)
   ```

5. **Compile the graph with the checkpointer**  
   ```python
   graph = graph_builder.compile(checkpointer=checkpointer)
   ```

6. **Configure the thread ID** – used by the checkpointer to isolate conversations.  
   ```python
   config = RunnableConfig({"configurable": {"thread_id": "1"}})
   ```

7. **Stream updates to the user** – yields partial results as the LLM generates them.  
   ```python
   def stream_graph_updates(user_input: str):
       events = graph.stream(
           {"messages": [{"role": "user", "content": user_input}]},
           config,
           stream_mode="values",
       )
       for event in events:
           event["messages"][-1].pretty_print()
   ```

"""





# Convert markdown to HTML for database storage with syntax highlighting
post_content_html = markdown.markdown(
    post_content_markdown,
    extensions=[
        # 'fenced_code', 
        'tables', 
        'toc',
        'codehilite'
    ],
    extension_configs={
        'codehilite': {
            'css_class': 'highlight',
            'use_pygments': True,
            'noclasses': False,
            'linenums': True
        }
    }
)

import mistune
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

class HighlightRenderer(mistune.HTMLRenderer):
    def block_code(self, code, info=None):
        if not info:
            return f'<pre><code>{mistune.escape(code)}</code></pre>'
        lexer = get_lexer_by_name(info, stripall=True)
        formatter = HtmlFormatter(style="friendly")  # choose a Pygments theme
        return highlight(code, lexer, formatter)

# markdown = mistune.create_markdown(renderer=HighlightRenderer())
# post_content_html = markdown(post_content_markdown)

with open("post_content_html.html", "w") as f:
    f.write(post_content_html)