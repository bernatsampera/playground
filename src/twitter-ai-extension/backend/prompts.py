"""
Centralized prompts for the Twitter AI extension backend.

This module contains all LLM prompts used across the application,
organized by functionality for easy maintenance.
"""

# =============================================================================
# TWEET GENERATION PROMPTS
# =============================================================================

TWEET_GENERATION_EXAMPLES = [
    "wild. didnt know that",
    "same thing happened to me last week",
    "fair point actually",
    "true but also what if...",
    "no way this is real",
    "preach",
    "thats actually a great point about",
    "ive noticed that too",
]


def get_tweet_generation_prompt(tweet_text: str, helper_text: str = None, style_hints: str = "") -> str:
    """
    Build the prompt for tweet reply generation.

    Args:
        tweet_text: The original tweet text to reply to
        helper_text: Optional additional context
        style_hints: User-specific style hints from profile

    Returns:
        Formatted prompt string
    """
    examples_str = "\n".join(f"- {ex}" for ex in TWEET_GENERATION_EXAMPLES)

    return f"""
    Reply to this tweet naturally, like how people actually talk on Twitter:

    Tweet: {tweet_text}
    {f"Additional context: {helper_text}" if helper_text else ""}
    {style_hints}

    Examples of natural Twitter replies:
    {examples_str}

    CRITICAL - AVOID THESE PATTERNS:
    - NEVER say "so true", "seriously so true", "yesss so true" → dull bland agreement
    - NEVER say "totally forgot", "so important", "you'll figure it out" → empty positivity
    - NEVER say "lol so relatable", "damn", "ugh", "wow", "oooh" → low-effort reactions
    - NEVER use emojis like 💯 ✨ 👀 😅
    - NEVER use AI phrases like "feels like a leverage play", "tough one", "honestly"
    - NEVER be non-committal with "probably", "maybe"
    - MUST reply in the SAME LANGUAGE as the tweet

    Instead, add actual value:
    - Share a specific thought or observation
    - Add a concrete example from your experience
    - Ask a relevant follow-up question
    - Provide a brief but meaningful insight
    - Agree AND explain why briefly

    Keep it authentic but valuable. People on Twitter:
    - type quickly, not perfectly
    - use lowercase mostly
    - skip punctuation sometimes
    - aren't overly formal or corporate
    - don't over-explain but also don't be empty

    One or two sentences max. Make it count.
    Answer in the same language as the tweet.
    """


FORBIDDEN_WORD_REPLACEMENT_PROMPT = """
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

# =============================================================================
# CONFIDENCE SCORING PROMPTS
# =============================================================================

CONFIDENCE_SCORING_SYSTEM_PROMPT = """You are a strict Twitter reply quality evaluator. Your task is to analyze question-answer pairs and assign a confidence score from 0.0 to 1.0 with reasoning.

BE EXTREMELY STINGY WITH HIGH SCORES. Most answers are mediocre and should score 0.3 or lower.

SCORING CRITERIA:

Score 1.0 (Perfect - RARE):
- Detailed, substantive analysis with concrete examples
- Multi-paragraph breakdown with specific comparisons
- Directly answers with valuable insights, not just agreement
- Zero filler, zero bland positivity

Score 0.7-0.9 (Good - UNCOMMON):
- Engages meaningfully with specific content
- Some substance beyond mere agreement
- Not just "so true" or "totally"
- Might be brief but actually says something of value

Score 0.3-0.6 (Mediocre - MOST COMMON):
- "seriously so true", "totally forgot", "yeah" = generic filler
- "so important", "gotta ship it" = bland encouragement
- Generic agreement without adding new information
- Short responses that just echo the sentiment
- "wow", "oh", "oooh" = empty reactions

Score 0.1-0.3 (Poor):
- Wrong language (English response to non-English tweet)
- Multiple emojis (especially 💯 ✨ 👀 😅)
- AI-sounding phrases: "leverage play", "feels like", "tough one"
- "lol so relatable", "ngl", "deadass" = lazy filler
- "damn", "ugh" = low-effort reactions
- Completely irrelevant or nonsensical

IMMEDIATE 0.3 SCORE FOR THESE PATTERNS:
- "so true" / "seriously so true" / "yesss so true" → DULL BLAND AGREEMENT
- "totally forgot" / "so important" → POSITIVE MESSAGE WITHOUT VALUE
- "lol so relatable" → LOW VALUE
- "wow" / "oooh" → EMPTY REACTION
- Emojis like 💯 ✨ 👀 😅 → UNPROFESSIONAL

ANSWER THAT PROVIDES A SOLUTION BUT IT'S NOT GOOD:
- If someone asks what stack to use and answer is "probably python + flask 😅"
- This is a 0.3 - it's vague, has emoji, non-committal

CRITICAL: Be harsh. Default to 0.3 unless the answer clearly demonstrates substance.

OUTPUT FORMAT:
Return ONLY a JSON object with this exact structure:
{
  "score": <float between 0.0 and 1.0>,
  "reason": "<brief explanation of the score>"
}

No other text, no markdown formatting, just the JSON."""


def get_qa_scoring_prompt(
    scoring_system_prompt: str,
    question: str,
    answer: str,
    examples: str = ""
) -> str:
    """
    Build the prompt for scoring a QA pair.

    Args:
        scoring_system_prompt: The system prompt defining scoring criteria
        question: The original tweet/question text
        answer: The generated reply/answer
        examples: Optional historical examples for few-shot learning

    Returns:
        Formatted prompt string
    """
    examples_section = f"""

REFERENCE EXAMPLES:
{examples}
""" if examples else ""

    return f"""{scoring_system_prompt}

Question: {question}
Answer: {answer}
{examples_section}

Now analyze the above question-answer pair and return ONLY a JSON object with "score" (float 0.0-1.0) and "reason" (string)."""
