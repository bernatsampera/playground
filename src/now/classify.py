import re

from chonkie import SemanticChunker
from rapidfuzz import fuzz

# Keywords for detection

PYTHON_KEYWORDS = ['def', 'import', 'return', 'print', 'lambda', 'class', '#']
SQL_KEYWORDS = ['select', 'from', 'where', 'insert', 'update', 'delete', '--', 'join']

def score_keywords(keywords, text):
    return max([fuzz.token_set_ratio(k, text) for k in keywords])

def detect_type(chunk: str) -> str:
    text = chunk.strip().lower()

    python_score = score_keywords(PYTHON_KEYWORDS, text)
    sql_score = score_keywords(SQL_KEYWORDS, text)

    # Debug (optional)
    print(f"PYTHON={python_score}, SQL={sql_score}, TEXT='{chunk[:30]}...'")

    max_score = max(python_score, sql_score)

    if max_score < 60:
        return "text"
    if python_score > sql_score:
        return "python"
    else:
        return "sql"

# Main logic
def classify_sections(text: str):
      # Basic initialization with default parameters
    chunker = SemanticChunker(
        # embedding_model="minishlab/potion-base-8M",  # Default model
        threshold=0.5,                               # Similarity threshold (0-1) or (1-100) or "auto"
        chunk_size=2048,                              # Maximum tokens per chunk
        min_sentences=1,                             # Initial sentences per chunk
        delim=["\n\n"]
    )
    chunks = chunker.chunk(text)

    sentences = chunks[0].sentences

    return [
          {"type": detect_type(sentence.text), "content": sentence.text.strip()}
          for sentence in sentences
      ]


# Sample code for testing
SAMPLE_TEXT = """
# Get glossary data
glossary, rules = get_user_glossary(1, 'english', 'spanish')



-- Sample glossary table data
SELECT * FROM glossary WHERE user_id = 1 AND input_language = 'english' AND target_language = 'spanish';



# Simplified get_user_glossary function
def get_user_glossary(user_id, input_lang, target_lang):
    '''Returns (glossary_dict, formatting_rules) for user/languages'''
    return {'World History': 'Historia Universal', 'execute': 'legalizar'}, \
           ['Use Spanish address format with comma separators']



This module provides functions to get user-specific glossary terms and formatting rules
for translation processes. It also contains default English->Spanish terms for seeding new users.
""" 
results = classify_sections(SAMPLE_TEXT)

for r in results:
    print(f"[{r['type'].upper()}]\n{r['content']}\n")
