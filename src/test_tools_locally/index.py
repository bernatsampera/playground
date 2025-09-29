import json
import sys
from langchain_ollama import ChatOllama


# llm = ChatOllama(model="llama3.1")
llm = ChatOllama(model="gpt-oss:20b")


def main():
    # Read the JSON trace from the file
    trace_file = "src/test_tools_locally/trace.json"
    with open(trace_file, "r") as f:
        trace = json.load(f)

    # Extract system prompt (first message, role: "system")
    system_prompt = next(
        (msg["content"] for msg in trace if msg["role"] == "system"), None
    )
    if not system_prompt:
        print("Error: No system prompt found in trace.")
        return

    # Extract tools (all role: "tool" messages)
    tools = []
    for msg in trace:
        if msg["role"] == "tool":
            tool_def = msg["content"]
            if isinstance(tool_def, dict) and tool_def.get("type") == "function":
                tools.append(tool_def)

    if not tools:
        print("Error: No tools found in trace.")
        return

    # Messages: Just the system for initial invocation (add user if present, but trace starts empty)
    messages = [{"role": "system", "content": system_prompt}]

    # Invoke the model
    try:
        model_with_tools = llm.bind_tools(tools)
        response = model_with_tools.invoke(messages)

        # Print formatted response
        print("🤖 LLM Response:")
        print("=" * 50)

        # Print content if available
        if hasattr(response, "content") and response.content:
            print(f"📝 Content: {response.content}")

        # Print tool calls if available
        if hasattr(response, "tool_calls") and response.tool_calls:
            print(f"\n🔧 Tool Calls ({len(response.tool_calls)}):")
            for i, tc in enumerate(response.tool_calls, 1):
                print(f"\n  {i}. Tool: {tc.get('name', 'Unknown')}")
                if "args" in tc:
                    print(f"     Arguments: {json.dumps(tc['args'], indent=6)}")
                elif hasattr(tc, "function") and hasattr(tc.function, "arguments"):
                    print(
                        f"     Arguments: {json.dumps(tc.function.arguments, indent=6)}"
                    )

        # Print metadata if available
        if hasattr(response, "response_metadata") and response.response_metadata:
            metadata = response.response_metadata
            print(f"\n📊 Model: {metadata.get('model_name', 'Unknown')}")
            if "usage_metadata" in response.__dict__:
                usage = response.usage_metadata
                print(
                    f"📈 Tokens: {usage.get('input_tokens', 0)} input, {usage.get('output_tokens', 0)} output"
                )

        print("\n" + "=" * 50)

    except Exception as e:
        print(f"❌ Error during invocation: {e}")
        print("This might be due to model configuration or tool binding issues.")


if __name__ == "__main__":
    main()
