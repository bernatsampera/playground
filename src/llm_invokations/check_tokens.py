import datetime
import logging
from collections import deque
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage
import time
from datetime import datetime

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%H:%M:%S",
)

# Mock response
mock_response = BaseMessage(
    type="ai",
    content="Hello there!",
    additional_kwargs={},
    response_metadata={},
    id="1",
    usage_metadata={"total_tokens": 23},
)


class LLM_Service:
    def __init__(self):
        self.llm_primary = init_chat_model("google_genai:gemini-2.5-flash-lite")
        self.llm_fallback = init_chat_model("ollama:llama3.2")
        self.history = deque()
        self.penalty_until = 0

    def print_history(self):
        now = time.time()
        if not self.history:
            print("History is empty.")
            return
        print("\n=== Token History ===")
        for ts, tokens in list(self.history):
            dt = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
            minutes_ago = round((now - ts) / 60, 2)
            print(f"{dt} | {tokens} tokens | {minutes_ago} min ago")
        print("=====================\n")

    def invoke(self, prompt: str) -> BaseMessage:
        now = time.time()
        self.print_history()

        # Clean history (older than 60s)
        while self.history and now - self.history[0][0] > 60:
            self.history.popleft()

        tokens_last_min = sum(t for _, t in self.history)

        # Check penalty mode
        if now < self.penalty_until:
            llm = self.llm_fallback
            logging.warning("Penalty active: forcing fallback model.")
        elif tokens_last_min > 2000:
            llm = self.llm_fallback
            logging.warning(
                f"Token usage in last minute = {tokens_last_min} (>2000). "
                f"Switching to fallback model: {self.llm_fallback.get_name()}"
            )
        else:
            llm = self.llm_primary
            logging.info(
                f"Token usage in last minute = {tokens_last_min}. "
                f"Using primary model: {self.llm_primary.get_name()}"
            )

        # Try calling model
        try:
            response = llm.invoke(prompt)
            used = response.usage_metadata["total_tokens"]
        except Exception as e:
            logging.error(f"Error with {llm.get_name()}: {e}")
            # If it was the primary, activate penalty + retry with fallback
            if llm is self.llm_primary:
                self.penalty_until = now + 300  # 5 min penalty
                used = 2500  # fake >2000 tokens
                self.history.append((now, used))
                logging.warning(
                    "Primary failed. Forcing fallback + penalty mode for 5 minutes."
                )
                return self.llm_fallback.invoke(prompt)
            else:
                raise
        if llm is self.llm_primary:
            self.history.append((now, used))

        logging.info(
            f"Model={llm.get_name()} | TokensThisCall={used} | TokensLastMin={tokens_last_min + used}"
        )
        return response


if __name__ == "__main__":
    llm_service = LLM_Service()
    print(llm_service.invoke("Hello, world!").content)
    print(llm_service.invoke("Hello, world!").content)
    print(llm_service.invoke("Hello, world!").content)
