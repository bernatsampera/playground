"""
Confidence Scorer for AI-generated Twitter replies.

This module uses an LLM (gemma3:12b) to analyze question-answer pairs
and assign confidence scores with reasoning, based on historical patterns.
"""

import json
import os
from typing import Dict, List, Optional, Tuple

from langchain_ollama import ChatOllama

# Import prompts from parent directory module
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import prompts


class ConfidenceScorer:
    """Scores QA pairs using LLM-based analysis of historical patterns"""

    def __init__(self, scored_history_path: Optional[str] = None):
        """
        Initialize the confidence scorer.

        Args:
            scored_history_path: Path to scored_history.json file. If None,
                uses the default path in the data/ folder.
        """
        if scored_history_path is None:
            # Path to data/ folder (sibling to confidence/ folder)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            scored_history_path = os.path.join(base_dir, "data", "scored_history.json")

        self.scored_history_path = scored_history_path
        self.model = ChatOllama(model="gemma3:12b", temperature=0.3)
        self._examples_cache: Optional[str] = None

    def _load_historical_examples(self) -> str:
        """
        Load and format historical examples for few-shot prompting.

        Returns:
            Formatted string of examples from scored_history.json
        """
        if self._examples_cache is not None:
            return self._examples_cache

        try:
            with open(self.scored_history_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            # Return empty examples if file doesn't exist
            return ""

        examples = []

        # Add approved examples
        for _, entry in data.get("approved", {}).items():
            examples.append(self._format_example(entry, "APPROVED"))

        # Add rejected examples
        for _, entry in data.get("rejected", {}).items():
            examples.append(self._format_example(entry, "REJECTED"))

        self._examples_cache = "\n\n".join(examples)
        return self._examples_cache

    def _format_example(self, entry: Dict, label: str) -> str:
        """Format a single example for prompting"""
        return f"""Example [{label}]:
Question: {entry["question"]}
Answer: {entry["answer"]}
Score: {entry.get("score", "N/A")}
Reason: {entry.get("reason", "N/A")}"""

    def score_qa_pair(
        self, question: str, answer: str, use_few_shot: bool = True
    ) -> Tuple[float, str]:
        """
        Score a single question-answer pair.

        Args:
            question: The original tweet/question text
            answer: The generated reply/answer
            use_few_shot: Whether to include historical examples in the prompt

        Returns:
            Tuple of (score: float, reason: str)
        """
        examples = self._load_historical_examples() if use_few_shot else ""

        prompt = prompts.get_qa_scoring_prompt(
            scoring_system_prompt=prompts.CONFIDENCE_SCORING_SYSTEM_PROMPT,
            question=question,
            answer=answer,
            examples=examples
        )

        try:
            response = self.model.invoke(prompt)
            result = self._parse_response(response.content)
            return result
        except Exception as e:
            # Return default score on error
            return (0.5, f"Scoring error: {str(e)}")

    def _parse_response(self, response: str) -> Tuple[float, str]:
        """
        Parse the LLM response into score and reason.

        Args:
            response: Raw LLM response string

        Returns:
            Tuple of (score: float, reason: str)
        """
        # Try to extract JSON from response
        import re

        # Look for JSON pattern
        json_match = re.search(
            r'\{[^{}]*"score"[^{}]*"reason"[^{}]*\}', response, re.DOTALL
        )
        if json_match:
            try:
                data = json.loads(json_match.group())
                score = float(data.get("score", 0.5))
                reason = str(data.get("reason", "No reason provided"))
                return (max(0.0, min(1.0, score)), reason)
            except json.JSONDecodeError:
                pass

        # Fallback: try to parse any JSON in the response
        try:
            # Clean up the response
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            data = json.loads(cleaned)
            score = float(data.get("score", 0.5))
            reason = str(data.get("reason", "No reason provided"))
            return (max(0.0, min(1.0, score)), reason)
        except (json.JSONDecodeError, ValueError):
            # Last resort: return default
            return (0.5, f"Could not parse response: {response[:100]}")

    def score_multiple_pairs(
        self, qa_pairs: List[Tuple[str, str]], use_few_shot: bool = True
    ) -> List[Tuple[float, str]]:
        """
        Score multiple question-answer pairs.

        Args:
            qa_pairs: List of (question, answer) tuples
            use_few_shot: Whether to include historical examples

        Returns:
            List of (score, reason) tuples
        """
        results = []
        for question, answer in qa_pairs:
            score, reason = self.score_qa_pair(question, answer, use_few_shot)
            results.append((score, reason))
        return results

    def score_all_from_history(
        self, qa_history_path: Optional[str] = None
    ) -> Dict[str, Dict]:
        """
        Score all QA pairs from a qa_history.json file.

        Args:
            qa_history_path: Path to qa_history.json. If None, uses default.

        Returns:
            Dictionary mapping IDs to {score, reason, question, answer}
        """
        if qa_history_path is None:
            # Path to data/ folder (sibling to confidence/ folder)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            qa_history_path = os.path.join(base_dir, "data", "qa_history.json")

        with open(qa_history_path, "r", encoding="utf-8") as f:
            qa_data = json.load(f)

        results = {}
        for qa_id, entry in qa_data.items():
            score, reason = self.score_qa_pair(entry["question"], entry["answer"])
            results[qa_id] = {
                "question": entry["question"],
                "answer": entry["answer"],
                "score": score,
                "reason": reason,
            }

        return results

    def update_scored_history(
        self, results: Dict[str, Dict], output_path: Optional[str] = None
    ) -> None:
        """
        Update scored_history.json with new results.

        This preserves existing entries and adds/updates new ones.

        Args:
            results: Dictionary of scored results from score_all_from_history
            output_path: Where to save. If None, uses scored_history_path.
        """
        if output_path is None:
            output_path = self.scored_history_path

        # Load existing data
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except FileNotFoundError:
            existing = {"approved": {}, "rejected": {}}

        # Categorize and add/update entries
        for qa_id, entry in results.items():
            score = entry["score"]
            new_entry = {
                "question": entry["question"],
                "answer": entry["answer"],
                "score": score,
                "reason": entry["reason"],
            }

            if score >= 0.7:
                existing.setdefault("approved", {})[qa_id] = new_entry
                # Remove from rejected if present
                if "rejected" in existing and qa_id in existing["rejected"]:
                    del existing["rejected"][qa_id]
            else:
                existing.setdefault("rejected", {})[qa_id] = new_entry
                # Remove from approved if present
                if "approved" in existing and qa_id in existing["approved"]:
                    del existing["approved"][qa_id]

        # Save updated data
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=4, ensure_ascii=False)


# Convenience function for direct usage
def score_reply(
    tweet_text: str, reply_text: str, model_name: str = "gemma3:12b"
) -> Tuple[float, str]:
    """
    Quick function to score a single reply.

    Args:
        tweet_text: Original tweet/question
        reply_text: Generated reply/answer
        model_name: Ollama model to use

    Returns:
        Tuple of (score: float, reason: str)
    """
    scorer = ConfidenceScorer()
    if model_name != "gemma3:12b":
        scorer.model = ChatOllama(model=model_name, temperature=0.3)
    return scorer.score_qa_pair(tweet_text, reply_text)


if __name__ == "__main__":
    # Score all QA pairs from qa_history.json
    print("Confidence Scorer - Analyzing all QA pairs\n")
    print("=" * 50)

    scorer = ConfidenceScorer()

    print("Loading QA pairs from qa_history.json...")
    results = scorer.score_all_from_history()

    print(f"\nScoring complete! Processed {len(results)} pairs.\n")

    # Display results
    print("=" * 50)
    print("RESULTS:")
    print("=" * 50)

    for qa_id, entry in results.items():
        print(f"\nID: {qa_id[:20]}...")
        print(f"Score: {entry['score']}")
        print(f"Reason: {entry['reason']}")
        print(f"Q: {entry['question'][:80]}...")
        print(f"A: {entry['answer'][:60]}...")

    # Categorize by score
    approved = {k: v for k, v in results.items() if v["score"] >= 0.7}
    rejected = {k: v for k, v in results.items() if v["score"] < 0.7}

    print("\n" + "=" * 50)
    print(f"Approved (score >= 0.7): {len(approved)}")
    print(f"Rejected (score < 0.7): {len(rejected)}")
    print("=" * 50)

    scorer.update_scored_history(results)
