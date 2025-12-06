import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_ollama import ChatOllama
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TweetPayload(BaseModel):
    tweet_url: str
    tweet_text: str
    helper_text: str | None = None


model = ChatOllama(model="llama3.1", temperature=0.7)


@app.post("/api/analyze_tweet")
def analyze(payload: TweetPayload):
    prompt = f"""
    You're helping someone reply to this tweet:

    URL: {payload.tweet_url}
    Tweet: {payload.tweet_text}

    Context: {payload.helper_text}

    Write a natural, authentic reply that sounds like a real person typing quickly. Keep it brief and conversational.

    Important - make it feel rushed and real:
    - Skip some punctuation or use it inconsistently (commas periods etc)
    - occasional typos are fine (missing letters, double letters, wrong letters)
    - dont always use apostrophes in contractions (dont, cant, youre)
    - lowercase is fine, no need to capitalize everything properly
    - sentence fragments are totally ok
    - run-on sentences without proper breaks
    - maybe throw in "lol" or "tbh" if it fits

    Avoid:
    - Perfect grammar and punctuation
    - Starting with "Great point!" or similar
    - Formal phrases like "I appreciate", "Furthermore", "Indeed"
    - Being overly diplomatic or hedge-y
    - Corporate language
    - Excessive enthusiasm or gratitude - keep it understated
    - Thanking people for obvious things
    - Multiple exclamation marks
    - Being overly affirming

    Write like youre texting fast not writing an essay. A couple small errors make it feel more human. Keep your energy more reserved and mysterious rather than eager or grateful
    """
    print("💬 Prompt:", prompt)

    ai = model.invoke(prompt)

    print("🔥 AI:", ai.content)

    return {"reply": ai.content}


MAX_FORBIDDEN_WORDS_ITERATIONS = 3


def get_forbidden_words_in_content(content: str) -> list[str]:
    """
    Returns a list of forbidden words found in the content.
    """
    forbidden_words_in_content = []

    for word in forbidden_words:
        # If the word is only punctuation/symbols, check direct presence
        if re.match(r"^[^\w\s]+$", word):
            if word in content:
                forbidden_words_in_content.append(word)
        else:
            # Whole-word match, plural allowed
            pattern = r"\b" + re.escape(word) + r"s?\b"
            if re.search(pattern, content, re.IGNORECASE):
                forbidden_words_in_content.append(word)

    return forbidden_words_in_content


def clean_content(
    content: str, max_iterations: int = MAX_FORBIDDEN_WORDS_ITERATIONS
) -> str:
    """
    Cleans AI-sounding words from content using simple string replacement.
    No LLM, no async, no LangGraph.
    """

    for _ in range(max_iterations):
        found = get_forbidden_words_in_content(content)

        if not found:
            break

        # Simple, predictable replacement (customize these)
        for w in found:
            # Replace whole word (case-insensitive)
            pattern = re.compile(r"\b" + re.escape(w) + r"s?\b", re.IGNORECASE)
            content = pattern.sub("[removed]", content)

    # Remove the AI-ish dashes
    # (ChatGPT often uses — and –)
    content = content.replace(" — ", ", ")
    content = content.replace(" – ", ", ")

    return content


forbidden_words = [
    "seamless",
    "em dashes",
    "—",
    "dive",
    "endless",
    "absurdly",
    "cranking",
    "down to the minute",
    "hidden strength",
    "precise",
    "handle",
    "struggle",
    "unpacks",
    "full breadth",
    "detailed",
    "demands",
    "deliver",
    "cover",
    "full range",
    "reveal",
    "what no one’s talking about",
    "what really works",
    "goldmine",
    "cutting-edge",
    "innovative",
    "powerful",
    "game-changing",
    "unprecedented",
    "intuitive",
    "lightning-fast",
    "effortless",
    "state-of-the-art",
    "next-level",
    "robust",
    "versatile",
    "scalable",
    "groundbreaking",
    "streamlined",
    "optimized",
    "sophisticated",
    "transformative",
    "comprehensive",
    "seamlessly integrated",
    "dive deeper",
    "explore",
    "unlock",
    "discover",
    "unpack",
    "break down",
    "decode",
    "delve into",
    "analyze",
    "examine",
    "showcase",
    "showcasing",
    "unveil",
    "craft",
    "leverage",
    "empower",
    "navigate",
    "master",
    "build from scratch",
    "at its core",
    "behind the scenes",
    "step-by-step",
    "here’s how it works",
    "let’s break it down",
    "the beauty of",
    "the power of",
    "in the wild",
    "in the real world",
    "from the ground up",
    "under the hood",
    "makes it easier than ever",
    "you’ll be surprised by",
    "what sets it apart",
    "the magic happens when",
    "bridges the gap",
    "boost",
    "maximize",
    "accelerate",
    "supercharge",
    "transform",
    "redefine",
    "streamline",
    "enhance",
    "revolutionize",
    "scale",
    "automate",
    "achieve more",
    "take it to the next level",
    "save countless hours",
    "cut through the noise",
    "in seconds",
    "like never before",
    "from start to finish",
    "effortlessly",
    "with ease",
    "smartly",
    "instantly",
    "on autopilot",
    "no manual work required",
    "powered by",
    "driven by data",
    "built with precision",
    "tailored to your needs",
    "hidden layers",
    "underlying",
    "uncovers",
    "depth",
    "Whether",
    "must-see",
    "must-",
    "stay in the loop",
    "essential",
    "capable",
    "this is a",
    "Introducing",
    "uncover",
    "Ready to",
    "scattered",
    "just clear",
    "fluff",
    "took control",
    "extra steps",
    "prioritized",
    "stepped in",
    "baller",
]
