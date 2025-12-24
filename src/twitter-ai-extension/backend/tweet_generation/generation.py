"""
Shared tweet generation utilities.

This module contains common functions used by both the API server
and the regeneration script.
"""

import re
from langchain_ollama import ChatOllama

import prompts
from tweet_generation import forbidden_words

# Maximum iterations for forbidden word cleaning (2 tries max)
MAX_FORBIDDEN_WORDS_ITERATIONS = 2


def get_model_for_context(tweet_text: str) -> ChatOllama:
    """
    Dynamic temperature based on context and expected reply length.

    Shorter, more casual replies need higher temperature for creativity.
    Longer, more thoughtful replies can use lower temperature.
    """
    if len(tweet_text) < 100:  # Short tweet
        temp = 0.9  # More creative, varied responses
    elif len(tweet_text) < 200:  # Medium tweet
        temp = 0.8
    else:  # Long tweet
        temp = 0.7  # More focused responses

    return ChatOllama(model="gemma3:12b", temperature=temp)


def get_forbidden_words_in_content(content: str) -> list[str]:
    """Returns a list of forbidden words found in the content."""
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
    replacement_model = ChatOllama(model="gemma3:12b", temperature=0.8)

    forbidden_list = ", ".join(found)

    replacement_prompt = prompts.FORBIDDEN_WORD_REPLACEMENT_PROMPT.format(
        content=content, forbidden_list=forbidden_list
    )

    try:
        ai_response = replacement_model.invoke(replacement_prompt)
        cleaned = ai_response.content.strip()

        # Clean up any remaining AI-ish dashes
        cleaned = cleaned.replace(" — ", ", ")
        cleaned = cleaned.replace(" – ", ", ")

        # Check if any forbidden words remain
        remaining = get_forbidden_words_in_content(cleaned)
        if remaining:
            # If AI failed to remove all, retry (max 2 tries total)
            print(f"Retry: Still has forbidden words: {remaining}")
            return clean_content(cleaned, max_iterations - 1)

        return cleaned

    except Exception as e:
        print(f"Error in AI replacement: {e}")
        # If AI fails, just clean dashes and return original
        content = content.replace(" — ", ", ")
        content = content.replace(" – ", ", ")
        return content
