import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from all_forbidden_words import forbidden_words
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_ollama import ChatOllama
from pydantic import BaseModel
from quality_scorer import ReplyScorer
from user_profile import UserProfile

# Path to store Q&A history
QA_HISTORY_PATH = Path("qa_history.json")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TweetPayload(BaseModel):
    user_id: Optional[str] = "default"
    tweet_url: str
    tweet_text: str
    helper_text: str | None = None


class FeedbackPayload(BaseModel):
    user_id: str
    tweet_text: str
    ai_reply: str
    user_edited_reply: Optional[str] = None
    feedback: str  # "good", "bad", "too_formal", "too_casual"


def get_model_for_context(tweet_text: str) -> ChatOllama:
    """Dynamic temperature based on context and expected reply length"""
    # Shorter, more casual replies need higher temperature for creativity
    # Longer, more thoughtful replies can use lower temperature

    # Estimate expected reply length based on tweet
    if len(tweet_text) < 100:  # Short tweet
        temp = 0.9  # More creative, varied responses
    elif len(tweet_text) < 200:  # Medium tweet
        temp = 0.8
    else:  # Long tweet
        temp = 0.7  # More focused responses

    return ChatOllama(model="gemma3:12b", temperature=temp)


# Default model instance
model = ChatOllama(model="gemma3:12b", temperature=0.7)

# In-memory user profile storage (use proper DB in production)
user_profiles: Dict[str, UserProfile] = {}

# Quality scorer instance
scorer = ReplyScorer()


def load_qa_history() -> dict:
    """Load Q&A history from JSON file"""
    if QA_HISTORY_PATH.exists():
        try:
            with open(QA_HISTORY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_qa_entry(question_id: str, question_text: str, answer_text: str, tweet_url: str, user_id: str) -> None:
    """Save a Q&A entry to the JSON history file"""
    history = load_qa_history()

    history[question_id] = {
        "question": question_text,
        "answer": answer_text
    }

    with open(QA_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def get_user_profile(user_id: str) -> UserProfile:
    """Get or create user profile"""
    if user_id not in user_profiles:
        user_profiles[user_id] = UserProfile()
    return user_profiles[user_id]


@app.post("/api/analyze_tweet")
def analyze(payload: TweetPayload):
    # Generate unique question ID
    question_id = str(uuid.uuid4())

    # Build question text from tweet and helper text
    question_text = f"Tweet: {payload.tweet_text}"
    if payload.helper_text:
        question_text += f"\nHelper text: {payload.helper_text}"

    # Get user profile
    user_profile = get_user_profile(payload.user_id)

    # Get model with appropriate temperature for this context
    context_model = get_model_for_context(payload.tweet_text)

    # Get style hints from user profile
    style_hints = user_profile.get_style_prompt_addition()

    prompt = f"""
    Reply to this tweet naturally, like how people actually talk on Twitter:

    Tweet: {payload.tweet_text}
    {"Additional context: " + payload.helper_text if payload.helper_text else ""}
    {style_hints}

    Examples of natural Twitter replies:
    - "this is exactly what i mean lol"
    - "wild. didnt know that"
    - "same thing happened to me last week"
    - "honestly? fair point"
    - "true but also what if..."
    - "im dying at this"
    - "no way this is real"
    - "preach"

    Keep it short and authentic. People on Twitter:
    - type quickly, not perfectly
    - use lowercase mostly
    - skip punctuation sometimes
    - aren't overly formal or corporate
    - don't over-explain
    - do not use lol, tbh...

    Just reply like you're talking to a friend. One or two sentences max.
    Answer in the same language as the tweet.
    """
    print("💬 Prompt:", prompt)

    ai = context_model.invoke(prompt)

    print("🔥 AI:", ai.content)

    # Apply forbidden words filtering (CRITICAL - was missing!)
    cleaned_reply = clean_content(ai.content)
    print("✨ Cleaned:", cleaned_reply)

    # Score the reply quality
    quality_scores = scorer.score_reply(cleaned_reply, payload.tweet_text)
    print(f"📊 Quality Score: {quality_scores['total_score']:.1f}/100")

    # Save Q&A entry to JSON file
    save_qa_entry(
        question_id=question_id,
        question_text=question_text,
        answer_text=cleaned_reply,
        tweet_url=payload.tweet_url,
        user_id=payload.user_id
    )
    print(f"💾 Saved Q&A entry with ID: {question_id}")

    return {
        "reply": cleaned_reply,
        "question_id": question_id,
        "user_id": payload.user_id,
        "style_hints": style_hints if style_hints else "default style",
        "quality_score": quality_scores["total_score"],
        "quality_feedback": scorer.get_feedback_message(quality_scores),
        "quality_breakdown": {
            "naturalness": quality_scores["naturalness"],
            "length_appropriateness": quality_scores["length_appropriateness"],
            "twitter_authenticity": quality_scores["twitter_authenticity"],
            "ai_penalty": quality_scores["ai_penalty"],
        },
    }


@app.post("/api/feedback")
def handle_feedback(payload: FeedbackPayload):
    """Update user profile based on feedback and edits"""
    user_profile = get_user_profile(payload.user_id)

    # Update profile from user edits
    if payload.user_edited_reply and payload.ai_reply:
        user_profile.update_from_reply(payload.ai_reply, payload.user_edited_reply)

    # Handle simple feedback
    if payload.feedback == "too_formal":
        user_profile.casualness_level = min(1.0, user_profile.casualness_level + 0.1)
        user_profile.capitalization_style = "lowercase"
    elif payload.feedback == "too_casual":
        user_profile.casualness_level = max(0.0, user_profile.casualness_level - 0.1)
        user_profile.capitalization_style = "casual"

    return {"status": "updated", "profile_samples": user_profile.samples_analyzed}


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
    Cleans AI-sounding words from content using AI to find better replacements.
    """

    # First pass: Check for forbidden words
    found = get_forbidden_words_in_content(content)

    if not found:
        # Just clean up the dashes and return
        content = content.replace(" — ", ", ")
        content = content.replace(" – ", ", ")
        return content

    # Use AI to find natural replacements for forbidden words
    replacement_model = ChatOllama(model="llama3.1", temperature=0.8)

    forbidden_list = ", ".join(found)

    replacement_prompt = f"""
Replace these AI/corporate words in this Twitter reply with natural, casual alternatives:

Original reply: "{content}"

Forbidden words to replace: {forbidden_list}

Rules:
- Keep the meaning the same
- Use casual, natural language people actually use on Twitter
- Don't make it longer
- Don't add emojis if they weren't there
- Match the same casual tone
- Keep it sounding authentic

Return only the modified reply, nothing else.
"""

    try:
        ai_response = replacement_model.invoke(replacement_prompt)
        cleaned = ai_response.content.strip()

        # Clean up any remaining AI-ish dashes
        cleaned = cleaned.replace(" — ", ", ")
        cleaned = cleaned.replace(" – ", ", ")

        # Check if any forbidden words remain
        remaining = get_forbidden_words_in_content(cleaned)
        if remaining:
            # If AI failed to remove all, retry once
            print(f"Retry: Still has forbidden words: {remaining}")
            return clean_content(cleaned, max_iterations - 1)

        return cleaned

    except Exception as e:
        print(f"Error in AI replacement: {e}")
        # If AI fails, just clean dashes and return original
        content = content.replace(" — ", ", ")
        content = content.replace(" – ", ", ")
        return content
