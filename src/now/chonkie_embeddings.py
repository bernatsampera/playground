from chonkie import LateChunker, SDPMChunker, SemanticChunker

# Basic initialization with default parameters
chunker = SemanticChunker(
    # embedding_model="minishlab/potion-base-8M",  # Default model
    threshold=0.5,                               # Similarity threshold (0-1) or (1-100) or "auto"
    chunk_size=2048,                              # Maximum tokens per chunk
    min_sentences=1,                             # Initial sentences per chunk
    delim=["\n\n"]
)



text = """
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

chunks = chunker.chunk(text)

sentences = chunks[0].sentences

for sentence in sentences:
    print("--------------START------------------")
    print(f"Sentence text: {sentence.text}")
    print(f"Token count: {sentence.token_count}")
    # print(f"Number of sentences: {len(chunk.sentences)}")
    print("--------------END------------------")