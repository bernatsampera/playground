# Install: pip install rapidfuzz

from rapidfuzz import fuzz, process
import re


def simple_fuzzy_glossary_match(glossary, text, threshold=80):
    """
    Simple fuzzy matching for single words AND multi-word phrases.

    Args:
        glossary: dict like {"langchain": "LangChain", "machine learning": "Machine Learning"}
        text: text to search in
        threshold: similarity threshold (0-100)

    Returns:
        dict of matches: {"found_text": "correct_form"}
    """
    matches = {}
    text_lower = text.lower()

    # Check each glossary term
    for term, correct_form in glossary.items():
        term_words = term.split()

        if len(term_words) == 1:
            # Single word matching
            words = re.findall(r"\b[\w-]+\b", text_lower)
            for word in words:
                similarity = fuzz.ratio(term.lower(), word)
                if similarity >= threshold:
                    matches[word] = correct_form
                    break  # Only match once per term
        else:
            # Multi-word phrase matching using sliding window
            text_words = text_lower.split()
            window_size = len(term_words)

            for i in range(len(text_words) - window_size + 1):
                window = " ".join(text_words[i : i + window_size])
                similarity = fuzz.ratio(term.lower(), window)

                if similarity >= threshold:
                    matches[window] = correct_form
                    break  # Only match once per term

    return matches


# Usage example
if __name__ == "__main__":
    glossary = {
        "langchain": "LangChain",
        "langgraph": "LangGraph",
        "openai": "OpenAI",
        "machine learning": "Machine Learning",
        "artificial intelligence": "Artificial Intelligence",
    }

    text = "I use langchian and openAi with machin learning for artificil inteligence"

    matches = simple_fuzzy_glossary_match(glossary, text, threshold=75)
    print("Matches found:")
    for found, correct in matches.items():
        print(f"  '{found}' -> '{correct}'")

    # Simple replacement
    corrected_text = text
    for found, correct in matches.items():
        corrected_text = re.sub(
            rf"\b{re.escape(found)}\b", correct, corrected_text, flags=re.IGNORECASE
        )

    print(f"\nOriginal: {text}")
    print(f"Corrected: {corrected_text}")
