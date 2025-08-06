```py
# Get glossary data
glossary, rules = get_user_glossary(1, 'english', 'spanish')
```

```sql
-- Sample glossary table data
SELECT * FROM glossary WHERE user_id = 1 AND input_language = 'english' AND target_language = 'spanish';
```

```py
# Simplified get_user_glossary function
def get_user_glossary(user_id, input_lang, target_lang):
    """Returns (glossary_dict, formatting_rules) for user/languages"""
    return {'World History': 'Historia Universal', 'execute': 'legalizar'}, \
           ['Use Spanish address format with comma separators']
```

```py
# Simplified matching
matched_glossary = {'World History': 'Historia Universal'}  # Mock matches
```
