```py
glossary, rules = get_user_glossary(user_id, input_language, target_language)
```

```md
| id  | user_id | input_language | target_language | term                                 | translation                                      | is_formatting_rule |
| --- | ------- | -------------- | --------------- | ------------------------------------ | ------------------------------------------------ | ------------------ |
| 1   | 1       | english        | spanish         | World History                        | Historia Universal                               | 0                  |
| 2   | 1       | english        | spanish         | execute                              | legalizar                                        | 0                  |
| 3   | 1       | english        | spanish         | in his/her/their authorized capacity | en calidad de persona                            | 0                  |
| 4   | 1       | english        | spanish         | rule_1                               | Use Spanish address format with comma separators | 1                  |
```

```py
def get_user_glossary(user_id: int, input_language: str, target_language: str) -> Tuple[Dict[str, str], List[str]]:
    """
    Get user's glossary terms and formatting rules for a language pair.

    Args:
        user_id: User ID
        input_language: Input language code (e.g., 'english')
        target_language: Target language code (e.g., 'spanish')

    Returns:
        Tuple of (glossary_dict, formatting_rules_list)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    print(f"🔍 Glossary: {user_id} {input_language} {target_language}")


    try:
        # Get glossary terms
        cursor.execute('''
            SELECT term, translation FROM glossary
            WHERE user_id = ? AND input_language = ? AND target_language = ? AND is_formatting_rule = FALSE
        ''', (user_id, input_language, target_language))

        glossary_dict = dict(cursor.fetchall())

        # Get formatting rules
        cursor.execute('''
            SELECT translation FROM glossary
            WHERE user_id = ? AND input_language = ? AND target_language = ? AND is_formatting_rule = TRUE
        ''', (user_id, input_language, target_language))

        formatting_rules = [row[0] for row in cursor.fetchall()]

        return glossary_dict, formatting_rules

    finally:
        conn.close()
```

```py
matched_glossary = collect_glossary_matches(
    markdown_content,
    user_glossary,
    threshold=80
)
```

```py
def collect_glossary_matches(text: str, glossary: Dict[str, str], threshold: int = 80) -> Dict[str, str]:
    """
    Find and collect glossary matches from the text using fuzzy matching.

    Args:
        text: The text to search in
        glossary: Dictionary of terms to translations
        threshold: Minimum similarity threshold (0-100)

    Returns:
        Dictionary of matched chunks to their translations
    """
    matches = {}
    seen_chunks = set()

    for term, translation in glossary.items():
        if ' ' in term:
            match = fuzzy_match_multi_word(term, text, threshold=threshold)
        else:
            match = fuzzy_match_single_term(term, text, threshold=threshold)

        if not match:
            continue

        _, _, matched_chunk, ratio = match
        matched_chunk = matched_chunk.strip()

        # Avoid duplicates
        if matched_chunk.lower() in seen_chunks:
            continue

        matches[matched_chunk] = translation
        seen_chunks.add(matched_chunk.lower())

    return matches
```
