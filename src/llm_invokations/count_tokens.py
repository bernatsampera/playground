from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage

load_dotenv()


llm = init_chat_model("google_genai:gemini-2.5-flash-lite")


# response = llm.invoke("Hello, world!")

# Example response from init_chat_model
mock_response = BaseMessage(
    type="ai",
    content="Hello there! It's nice to meet you. How can I help you today?",
    additional_kwargs={},
    response_metadata={
        "prompt_feedback": {"block_reason": 0, "safety_ratings": []},
        "finish_reason": "STOP",
        "model_name": "gemini-2.5-flash-lite",
        "safety_ratings": [],
    },
    id="run--f961ed4a-df54-4b71-9ee6-60c0b2daaa37-0",
    usage_metadata={
        "input_tokens": 5,
        "output_tokens": 18,
        "total_tokens": 23,
        "input_token_details": {"cache_read": 0},
    },
)


print(mock_response)
