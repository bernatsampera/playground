"""
Centralized prompts for the Twitter AI extension backend.

This module contains all LLM prompts used across the application,
organized by functionality for easy maintenance.
"""

# =============================================================================
# TWEET GENERATION PROMPTS
# =============================================================================

TWEET_GENERATION_PROMPT = """<task>
Reply to this tweet naturally, like how people actually talk on Twitter.
</task>

<input>
Tweet: {tweet_text}
{helper_text}
{style_hints}
</input>

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
- DO NOT AGREE AND explain why briefly
- Be hyperbolic and over the top
</recommended_behaviors>

<style_guidelines>
Keep it authentic but valuable. People on Twitter:
- be hyperbolic and exagerated
- it's ok to rage bait
- type quickly, not perfectly
- use lowercase mostly
- skip punctuation sometimes
- aren't overly formal or corporate
- don't over-explain but also don't be empty
- Never end in small questions without meaning like "what do you think?" or "do you agree?" or "you know"
- do some grammatical mistakes
- Never add asterisks to words
</style_guidelines>

<constraints>
- One or two sentences max
- Make it count
- Answer in the same language as the tweet (never use "¡" or "¿" at the beginning of sentence)
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
- Strong take with personality: contrarian, challenging, or hyperbolic
- Concrete example or personal experience shared
- Direct engagement with the tweet's content
- Zero filler, zero bland agreement
- Matches the tweet's language
</score_1_0>

<score_0_7_0_9>
<level>Good - UNCOMMON</level>
- Has a take or opinion, not just agreement
- Adds some value beyond echoing sentiment
- Might be brief but actually says something
- Human-sounding tone
</score_0_7_0_9>

<score_0_3_0_6>
<level>Mediocre - MOST COMMON</level>
- "so true", "totally", "yeah", "same" = generic agreement
- "that sucks", "sorry to hear" = empty sympathy
- Generic advice without substance
- Being overly polite/PC when edge would be better
- Just echoing the tweet's sentiment
</score_0_3_0_6>

<score_0_1_0_3>
<level>Poor</level>
- Wrong language (English response to non-English tweet)
- Emojis: 💯 ✨ 👀 😅
- AI-sounding: "honestly", "basically", "actually", "probably", "maybe"
- Corporate: "furthermore", "leverage", "utilize"
- Empty reactions: "damn", "ugh", "wow", "oooh"
- Completely irrelevant or nonsensical
</score_0_1_0_3>
</scoring_criteria>

<immediate_0_3_patterns>
IMMEDIATE 0.3 SCORE FOR:
- "so true" / "seriously so true" / "totally" / "same"
- "lol so relatable"
- "that sucks, sorry to hear" or generic sympathy
- Emojis like 💯 ✨ 👀 😅
- Non-committal: "probably", "maybe"
</immediate_0_3_patterns>

<what_we_want>
REWARD: Hot takes, contrarian views, challenging the OP, hyperbole ("wild", "insane", "criminal"), concrete examples, calling things out directly, having actual opinions
PENALIZE: Being neutral, safe, overly polite, generic agreement, empty positivity
</what_we_want>

<critical_reminder>
CRITICAL: Be harsh. Default to 0.3 unless the answer has a real take or adds genuine value.
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
