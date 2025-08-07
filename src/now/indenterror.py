

import ast
import autopep8
import textwrap


def fix_python_indentation(code_string):
    """
    Automatically fix Python code indentation using a combination of techniques
    
    Args:
        code_string (str): Python code with potential indentation issues
        
    Returns:
        str: Code with fixed indentation
    """
    # First, try to dedent the code to remove leading indentation
    try:
        dedented = textwrap.dedent(code_string)
    except:
        dedented = code_string
    
    # Then use autopep8 to fix any remaining formatting issues
    try:
        fixed = autopep8.fix_code(
            dedented, 
            options={
                'aggressive': 3,  # More aggressive fixing
                'max_line_length': 100,
                'indent_size': 4,  # Use 4 spaces for indentation
            }
        )
        return fixed
    except:
        return dedented


SAMPLE_TEXT = '''
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
'''

print("Original code:")
print(SAMPLE_TEXT)

# Fix indentation using our combined approach
fixed_code = fix_python_indentation(SAMPLE_TEXT)

print("\nFixed code:")
print(fixed_code)

# Now we can parse it without errors
try:
    tree = ast.parse(fixed_code)
    print("\n✅ Successfully parsed the fixed code!")
    print(f"AST type: {type(tree)}")
except SyntaxError as e:
    print(f"\n❌ Still has syntax errors: {e}")
