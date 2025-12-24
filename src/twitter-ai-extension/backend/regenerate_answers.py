#!/usr/bin/env python3
"""
Regenerate all answers in qa_history.json using the current tweet generation prompt.

This script reads all questions from data/qa_history.json, regenerates answers
using the get_tweet_generation_prompt() function, and writes them back.
"""

import json
from pathlib import Path

import prompts
from tweet_generation.generation import clean_content, get_model_for_context

# Path to QA history file
QA_HISTORY_PATH = Path("data/qa_history.json")


def extract_tweet_text(question: str) -> str:
    """Extract the tweet text from a question string."""
    # Questions are formatted as "Tweet: <tweet text>" or may have additional context
    if question.startswith("Tweet: "):
        # Remove "Tweet: " prefix
        return question[7:].strip()
    return question.strip()


def main():
    """Main function to regenerate all answers."""
    print("Loading QA history from:", QA_HISTORY_PATH)

    with open(QA_HISTORY_PATH, "r", encoding="utf-8") as f:
        qa_data = json.load(f)

    total = len(qa_data)
    print(f"Found {total} QA pairs to regenerate.\n")

    for i, (qa_id, entry) in enumerate(qa_data.items(), 1):
        question = entry.get("question", "")
        old_answer = entry.get("answer", "")

        # Extract tweet text from question
        tweet_text = extract_tweet_text(question)

        print(f"[{i}/{total}] Processing: {qa_id[:20]}...")
        print(f"  Tweet: {tweet_text[:60]}{'...' if len(tweet_text) > 60 else ''}")
        print(f"  Old answer: {old_answer}")

        # Generate prompt
        prompt = prompts.get_tweet_generation_prompt(
            tweet_text=tweet_text, helper_text=None, style_hints=""
        )

        # Get model with appropriate temperature
        model = get_model_for_context(tweet_text)

        # Generate new answer
        try:
            ai_response = model.invoke(prompt)
            new_answer = ai_response.content.strip()
            print(f"  AI raw: {new_answer}")

            # Apply forbidden word filtering
            cleaned_answer = clean_content(new_answer)
            print(f"  Cleaned: {cleaned_answer}")

            # Update the entry
            entry["answer"] = cleaned_answer

        except Exception as e:
            print(f"  Error generating answer: {e}")
            continue

        print()

    # Save back to file
    print(f"Saving {total} regenerated answers to:", QA_HISTORY_PATH)
    with open(QA_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(qa_data, f, indent=2, ensure_ascii=False)

    print("Done!")


if __name__ == "__main__":
    main()
