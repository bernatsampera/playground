import warnings
import sys
import os

from .vectorstore import VectorStoreManager
from .graph import RAGGraph
from .chonkiestore import ChonkieStore

# Sample code for testing
SAMPLE_TEXT = '''
glossary, rules = get_user_glossary(user_id, input_language, target_language)

| id  | user_id | input_language | target_language | term                                 | translation                                      | is_formatting_rule |
| --- | ------- | -------------- | --------------- | ------------------------------------ | ------------------------------------------------ | ------------------ |
| 1   | 1       | english        | spanish         | World History                        | Historia Universal                               | 0                  |
| 2   | 1       | english        | spanish         | execute                              | legalizar                                        | 0                  |
| 3   | 1       | english        | spanish         | in his/her/their authorized capacity | en calidad de persona                            | 0                  |
| 4   | 1       | english        | spanish         | rule_1                               | Use Spanish address format with comma separators | 1                  |

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
        cursor.execute("""
            SELECT term, translation FROM glossary
            WHERE user_id = ? AND input_language = ? AND target_language = ? AND is_formatting_rule = FALSE
        """, (user_id, input_language, target_language))

        glossary_dict = dict(cursor.fetchall())

        # Get formatting rules
        cursor.execute("""
            SELECT translation FROM glossary
            WHERE user_id = ? AND input_language = ? AND target_language = ? AND is_formatting_rule = TRUE
        """, (user_id, input_language, target_language))

        formatting_rules = [row[0] for row in cursor.fetchall()]

        return glossary_dict, formatting_rules

    finally:
        conn.close()

matched_glossary = collect_glossary_matches(
    markdown_content,
    user_glossary,
    threshold=80
)

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


def fuzzy_match_single_term(term: str, text: str, threshold: int = 85) -> Optional[Tuple[int, int, str, int]]:
    """
    Find the best fuzzy match for a single term in text.
    
    Args:
        term: The term to search for
        text: The text to search in
        threshold: Minimum similarity threshold (0-100)
    
    Returns:
        Tuple of (start_pos, end_pos, matched_chunk, similarity_ratio) or None
    """
    # Extract potential matches from text using regex
    potential_matches = re.finditer(r'\b[\w\s,:\-/]+?\b', text, re.IGNORECASE)
    
    best_match = None
    best_ratio = 0
    
    for match in potential_matches:
        chunk = match.group().strip()
        if not chunk or len(chunk) < 2:  # Skip very short matches
            continue
            
        # Use multiple fuzzywuzzy algorithms for better matching
        ratio_ratio = fuzz.ratio(term.lower(), chunk.lower())
        partial_ratio = fuzz.partial_ratio(term.lower(), chunk.lower())
        token_sort_ratio = fuzz.token_sort_ratio(term.lower(), chunk.lower())
        token_set_ratio = fuzz.token_set_ratio(term.lower(), chunk.lower())
        
        # Use the best ratio from all algorithms
        ratio = max(ratio_ratio, partial_ratio, token_sort_ratio, token_set_ratio)
        
        if ratio >= threshold and ratio > best_ratio:
            best_ratio = ratio
            best_match = (match.start(), match.end(), chunk, ratio)
    
    return best_match

    
def fuzzy_match_multi_word(term: str, text: str, threshold: int = 85) -> Optional[Tuple[int, int, str, int]]:
    """
    Enhanced fuzzy matching for multi-word terms using sliding windows.
    
    Args:
        term: The multi-word term to search for
        text: The text to search in
        threshold: Minimum similarity threshold (0-100)
    
    Returns:
        Tuple of (start_pos, end_pos, matched_chunk, similarity_ratio) or None
    """
    words = text.split()
    term_words = term.split()
    
    if len(term_words) == 1:
        # Single word term, use the regular fuzzy_match
        return fuzzy_match_single_term(term, text, threshold)
    
    best_match = None
    best_ratio = 0
    
    # Use sliding window approach for multi-word terms
    for i in range(len(words) - len(term_words) + 1):
        window = ' '.join(words[i:i + len(term_words)])
        
        # Use multiple fuzzywuzzy algorithms
        ratio_ratio = fuzz.ratio(term.lower(), window.lower())
        partial_ratio = fuzz.partial_ratio(term.lower(), window.lower())
        token_sort_ratio = fuzz.token_sort_ratio(term.lower(), window.lower())
        token_set_ratio = fuzz.token_set_ratio(term.lower(), window.lower())
        
        ratio = max(ratio_ratio, partial_ratio, token_sort_ratio, token_set_ratio)
        
        if ratio >= threshold and ratio > best_ratio:
            # Find the actual position in the original text
            start_pos = len(' '.join(words[:i])) + (1 if i > 0 else 0)
            end_pos = start_pos + len(window)
            best_ratio = ratio
            best_match = (start_pos, end_pos, window, ratio)
    
    return best_match


''' 

warnings.filterwarnings("ignore")

def main():
    """Main execution function"""
    # Initialize vector store manager
    # vector_store_manager = VectorStoreManager()
    chonkie_store = ChonkieStore()
    chonkie_store.add_code_chunks(SAMPLE_TEXT)
    
    # Setup code chunks
    # vector_store_manager.setup_code_chunks(SAMPLE_CODE)
    # vector_store_manager.setup_semantic_chunks(SAMPLE_CODE)
    

if __name__ == "__main__":
    main() 



