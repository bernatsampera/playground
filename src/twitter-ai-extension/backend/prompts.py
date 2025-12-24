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

TWEET_GENERATION_EXAMPLES_STR = "\n".join(f"- {ex}" for ex in TWEET_GENERATION_EXAMPLES)

TWEET_GENERATION_PROMPT = """<task>
Reply to this tweet naturally, like how people actually talk on Twitter.
</task>

<input>
Tweet: {tweet_text}
{helper_text}
{style_hints}
</input>

<examples>
Examples of natural Twitter replies:
{examples_str}
</examples>

<rules>
<forbidden_patterns>
- NEVER say "so true", "seriously so true", "yesss so true" → dull bland agreement
- NEVER say "totally forgot", "so important", "you'll figure it out" → empty positivity
- NEVER say "lol so relatable", "damn", "ugh", "wow", "oooh" → low-effort reactions
- NEVER use emojis like 💯 ✨ 👀 😅
- NEVER use AI phrases like "feels like a leverage play", "tough one", "honestly"
- NEVER be non-committal with "probably", "maybe"
- MUST reply in the SAME LANGUAGE as the tweet
</forbidden_patterns>

<recommended_behaviors>
Instead, add actual value:
- Share a specific thought or observation
- Add a concrete example from your experience
- Ask a relevant follow-up question
- Provide a brief but meaningful insight
- Agree AND explain why briefly
</recommended_behaviors>

<style_guidelines>
Keep it authentic but valuable. People on Twitter:
- type quickly, not perfectly
- use lowercase mostly
- skip punctuation sometimes
- aren't overly formal or corporate
- don't over-explain but also don't be empty
- Never end in small questions without meaning like "what do you think?" or "do you agree?" or "you know"
</style_guidelines>

<constraints>
- One or two sentences max
- Make it count
- Answer in the same language as the tweet
</constraints>
</rules>"""


FORBIDDEN_WORD_REPLACEMENT_PROMPT = """<task>
Replace these AI/corporate words in this Twitter reply with natural, casual alternatives.
</task>

<input>
Original reply: "{content}"

Forbidden words to replace: {forbidden_list}
</input>

<rules>
- Keep the meaning the same
- Use casual, natural language people actually use on Twitter
- Don't make it longer
- Don't add emojis if they weren't there
- Match the same casual tone
- Keep it sounding authentic
</rules>

<output_format>
Return only the modified reply, nothing else.
</output_format>"""

# =============================================================================
# CONFIDENCE SCORING PROMPTS
# =============================================================================

CONFIDENCE_SCORING_SYSTEM_PROMPT = """<role>
You are a strict Twitter reply quality evaluator. Your task is to analyze question-answer pairs and assign a confidence score from 0.0 to 1.0 with reasoning.
</role>

<critical_principle>
BE EXTREMELY STINGY WITH HIGH SCORES. Most answers are mediocre and should score 0.3 or lower.
</critical_principle>

<scoring_criteria>
<score_1_0>
<level>Perfect - RARE</level>
- Detailed, substantive analysis with concrete examples
- Multi-paragraph breakdown with specific comparisons
- Directly answers with valuable insights, not just agreement
- Zero filler, zero bland positivity
</score_1_0>

<score_0_7_0_9>
<level>Good - UNCOMMON</level>
- Engages meaningfully with specific content
- Some substance beyond mere agreement
- Not just "so true" or "totally"
- Might be brief but actually says something of value
</score_0_7_0_9>

<score_0_3_0_6>
<level>Mediocre - MOST COMMON</level>
- "seriously so true", "totally forgot", "yeah" = generic filler
- "so important", "gotta ship it" = bland encouragement
- Generic agreement without adding new information
- Short responses that just echo the sentiment
- "wow", "oh", "oooh" = empty reactions
</score_0_3_0_6>

<score_0_1_0_3>
<level>Poor</level>
- Wrong language (English response to non-English tweet)
- Multiple emojis (especially 💯 ✨ 👀 😅)
- AI-sounding phrases: "leverage play", "feels like", "tough one"
- "lol so relatable", "ngl", "deadass" = lazy filler
- "damn", "ugh" = low-effort reactions
- Completely irrelevant or nonsensical
</score_0_1_0_3>
</scoring_criteria>

<immediate_0_3_patterns>
IMMEDIATE 0.3 SCORE FOR THESE PATTERNS:
- "so true" / "seriously so true" / "yesss so true" → DULL BLAND AGREEMENT
- "totally forgot" / "so important" → POSITIVE MESSAGE WITHOUT VALUE
- "lol so relatable" → LOW VALUE
- "wow" / "oooh" → EMPTY REACTION
- Emojis like 💯 ✨ 👀 😅 → UNPROFESSIONAL
</immediate_0_3_patterns>

<edge_cases>
ANSWER THAT PROVIDES A SOLUTION BUT IT'S NOT GOOD:
- If someone asks what stack to use and answer is "probably python + flask 😅"
- This is a 0.3 - it's vague, has emoji, non-committal
</edge_cases>

<critical_reminder>
CRITICAL: Be harsh. Default to 0.3 unless the answer clearly demonstrates substance.
</critical_reminder>

<output_format>
Return ONLY a JSON object with this exact structure:
{{
  "score": <float between 0.0 and 1.0>,
  "reason": "<brief explanation of the score>"
}}

No other text, no markdown formatting, just the JSON.
</output_format>"""


def get_qa_scoring_prompt(
    scoring_system_prompt: str, question: str, answer: str, examples: str = ""
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
    examples_section = (
        f"""

<reference_examples>
REFERENCE EXAMPLES:
{examples}
</reference_examples>
"""
        if examples
        else ""
    )

    return f"""{scoring_system_prompt}

<input>
Question: {question}
Answer: {answer}
</input>
{examples_section}

<instruction>
Now analyze the above question-answer pair and return ONLY a JSON object with "score" (float 0.0-1.0) and "reason" (string).
</instruction>"""
