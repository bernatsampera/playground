import re
from typing import Dict, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_ollama import ChatOllama
from pydantic import BaseModel
from quality_scorer import ReplyScorer
from user_profile import UserProfile

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

    return ChatOllama(model="llama3.1", temperature=temp)


# Default model instance
model = ChatOllama(model="llama3.1", temperature=0.7)

# In-memory user profile storage (use proper DB in production)
user_profiles: Dict[str, UserProfile] = {}

# Quality scorer instance
scorer = ReplyScorer()


def get_user_profile(user_id: str) -> UserProfile:
    """Get or create user profile"""
    if user_id not in user_profiles:
        user_profiles[user_id] = UserProfile()
    return user_profiles[user_id]


@app.post("/api/analyze_tweet")
def analyze(payload: TweetPayload):
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

    return {
        "reply": cleaned_reply,
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


forbidden_words = [
    # Original words
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
    "what no one's talking about",
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
    "here's how it works",
    "let's break it down",
    "the beauty of",
    "the power of",
    "in the wild",
    "in the real world",
    "from the ground up",
    "under the hood",
    "makes it easier than ever",
    "you'll be surprised by",
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
    # Corporate jargon
    "synergy",
    "paradigm",
    "ecosystem",
    "holistic",
    "proactive",
    "paradigm shift",
    "best practices",
    "actionable insights",
    "thought leader",
    "thought leadership",
    "circle back",
    "touch base",
    "low-hanging fruit",
    "quick win",
    "pain point",
    "value-add",
    "mission-critical",
    "bleeding edge",
    "vertical",
    "horizontal",
    "space",
    "deliverable",
    "stakeholder",
    "bandwidth",
    "ping",
    "align",
    "alignment",
    "deep dive",
    "30,000 foot view",
    "boil the ocean",
    "let's take this offline",
    "action item",
    "core competency",
    "moving forward",
    "at the end of the day",
    "win-win",
    "push the envelope",
    # AI-written phrases
    "in conclusion",
    "it's worth noting",
    "it's important to remember",
    "keep in mind",
    "don't forget",
    "make sure",
    "always remember",
    "it's crucial",
    "it's vital",
    "it's essential",
    "it's imperative",
    "moreover",
    "furthermore",
    "additionally",
    "in addition",
    "on the other hand",
    "however",
    "nevertheless",
    "nonetheless",
    "therefore",
    "thus",
    "hence",
    "consequently",
    "as a result",
    "due to",
    "owing to",
    "in light of",
    "given that",
    "considering that",
    "with that in mind",
    "that being said",
    "having said that",
    "all things considered",
    "at the end of the day",
    "when all is said and done",
    "ultimately",
    "in the final analysis",
    "to sum up",
    "to summarize",
    "in summary",
    "in closing",
    "finally",
    "lastly",
    "above all",
    "most importantly",
    "it cannot be overstated",
    "it should be emphasized",
    "it should be noted",
    "it bears repeating",
    "it's worth mentioning",
    "it's worth emphasizing",
    # Overly formal/academic
    "heretofore",
    "herewith",
    "henceforth",
    "wherewithal",
    "thence",
    "thusly",
    "whence",
    "whereas",
    "wherein",
    "whereby",
    "hereafter",
    "thereafter",
    "aforementioned",
    "aforethought",
    "heretofore",
    "notwithstanding",
    "albeit",
    "alas",
    "ergo",
    "ipso facto",
    "de facto",
    "status quo",
    "modus operandi",
    "quid pro quo",
    "raison d'être",
    "tour de force",
    "piece de resistance",
    "en masse",
    "vox populi",
    "ad nauseam",
    "ad infinitum",
    "per se",
    "vice versa",
    "et cetera",
    "et al",
    "ibid",
    "op cit",
    "loc cit",
    "viz",
    "ie",
    "eg",
    "cf",
    "qv",
    "sic",
    "stet",
    "nd",
    "vs",
    # Marketing hype
    "disruptive",
    "disruption",
    "future-proof",
    "game changer",
    "change the game",
    "revolutionary",
    "breakthrough",
    "pioneering",
    "visionary",
    "trailblazing",
    "epic",
    "mind-blowing",
    "jaw-dropping",
    "insane",
    "crazy",
    "unreal",
    "unbelievable",
    "incredible",
    "amazing",
    "awesome",
    "fantastic",
    "wonderful",
    "spectacular",
    "magnificent",
    "marvelous",
    "superb",
    "outstanding",
    "exceptional",
    "extraordinary",
    "remarkable",
    "phenomenal",
    "stunning",
    "breathtaking",
    "awe-inspiring",
    # Filler phrases
    "basically",
    "actually",
    "literally",
    "honestly",
    "truthfully",
    "frankly",
    "candidly",
    "genuinely",
    "sincerely",
    "truly",
    "really",
    "very",
    "quite",
    "rather",
    "somewhat",
    "somehow",
    "some way",
    "in some way",
    "in any way",
    "in any case",
    "in either case",
    "in that case",
    "in this case",
    "in many cases",
    "in most cases",
    "in all cases",
    "in every case",
    "in no case",
    "in some cases",
    "in certain cases",
    "in particular cases",
    "in special cases",
    "in rare cases",
    "in unusual cases",
    "in extreme cases",
    "in normal cases",
    "in typical cases",
    "in standard cases",
    "in general cases",
    "in specific cases",
    "in concrete cases",
    "in abstract cases",
    "in theoretical cases",
    "in practical cases",
    "in real cases",
    "in hypothetical cases",
    "in possible cases",
    "in impossible cases",
    "in likely cases",
    "in unlikely cases",
    "in probable cases",
    "in improbable cases",
]
