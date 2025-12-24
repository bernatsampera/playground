import json
import uuid
from pathlib import Path
from typing import Dict, Optional

import prompts
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_ollama import ChatOllama
from pydantic import BaseModel
from tweet_generation import ReplyScorer, UserProfile
from tweet_generation.generation import clean_content, get_model_for_context

# Path to store Q&A history
QA_HISTORY_PATH = Path("data/qa_history.json")

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


def save_qa_entry(
    question_id: str, question_text: str, answer_text: str, tweet_url: str, user_id: str
) -> None:
    """Save a Q&A entry to the JSON history file"""
    history = load_qa_history()

    history[question_id] = {"question": question_text, "answer": answer_text}

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

    # Build the prompt
    helper_text_section = f"Additional context: {payload.helper_text}" if payload.helper_text else ""
    prompt = prompts.TWEET_GENERATION_PROMPT.format(
        tweet_text=payload.tweet_text,
        helper_text=helper_text_section,
        style_hints=style_hints,
        examples_str=prompts.TWEET_GENERATION_EXAMPLES_STR,
    )
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
        user_id=payload.user_id,
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
