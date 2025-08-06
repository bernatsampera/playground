import ast
import re
import tokenize
import io
from typing import List, Dict, Any
from chonkie import SemanticChunker


class PythonCodeParser:
    """Extract and chunk Python code from mixed content."""
    
    def __init__(self, mixed_text: str):
        self.python_code, self.ignored_content = self._extract_python_code(mixed_text)
        self.source_lines = self.python_code.splitlines()
        
        # Initialize semantic chunker
        self.chunker = SemanticChunker(
            threshold=0.5,
            chunk_size=512,
            min_sentences=1,
            delim=["\n\n", "\n"]
        )
    
    def _extract_python_code(self, text: str) -> tuple[str, str]:
        """Extract valid Python code and return ignored content separately."""
        lines = text.splitlines()
        valid_lines = []
        ignored_lines = []
        
        # Filter out markdown tables and invalid syntax
        for line in lines:
            if re.match(r'^\s*\|.*\|\s*$', line) or re.match(r'^\s*[\|\-\s]+\s*$', line):
                ignored_lines.append(line)
                continue
            valid_lines.append(line)
        
        clean_text = '\n'.join(valid_lines)
        
        # Validate using tokenizer
        try:
            list(tokenize.generate_tokens(io.StringIO(clean_text).readline))
            return clean_text, '\n'.join(ignored_lines)
        except tokenize.TokenError:
            # Line-by-line validation
            python_lines = []
            invalid_lines = []
            
            for line in valid_lines:
                if not line.strip():
                    python_lines.append(line)
                    continue
                try:
                    list(tokenize.generate_tokens(io.StringIO(line).readline))
                    python_lines.append(line)
                except (tokenize.TokenError, IndentationError):
                    invalid_lines.append(line)
            
            all_ignored = ignored_lines + invalid_lines
            return '\n'.join(python_lines), '\n'.join(all_ignored)
    
    def _extract_code_block(self, node: Any) -> str:
        """Extract code block for a given AST node."""
        start = node.lineno - 1
        end = node.end_lineno
        return "\n".join(self.source_lines[start:end])
    
    def extract_functions_and_classes(self) -> tuple[List[str], str]:
        """Extract functions/classes and return remaining code."""
        if not self.python_code.strip():
            return [], ""
            
        tree = ast.parse(self.python_code)
        functions_classes = []
        extracted_lines = set()
        
        # Extract functions and classes
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                functions_classes.append(self._extract_code_block(node))
                # Track extracted lines
                start, end = node.lineno - 1, node.end_lineno
                extracted_lines.update(range(start, end))
        
        # Collect remaining code
        remaining_lines = [
            line for i, line in enumerate(self.source_lines) 
            if i not in extracted_lines
        ]
        
        return functions_classes, '\n'.join(remaining_lines).strip()
    
    def create_all_chunks(self) -> List[Dict[str, Any]]:
        """Create semantic chunks from all extracted content."""
        chunks = []
        
        # Extract functions/classes and remaining code
        functions_classes, remaining_code = self.extract_functions_and_classes()
        
        # Add function/class chunks
        for i, func_class in enumerate(functions_classes):
            if func_class.strip():
                chunks.append({
                    'type': 'function_or_class',
                    'content': func_class,
                    'index': i
                })
        
        # Chunk remaining Python code
        if remaining_code.strip():
            remaining_chunks = self.chunker.chunk(remaining_code)
            for i, chunk in enumerate(remaining_chunks):
                chunks.append({
                    'type': 'remaining_code',
                    'content': chunk.text,
                    'index': i
                })
        
        # Chunk ignored content
        if self.ignored_content.strip():
            ignored_chunks = self.chunker.chunk(self.ignored_content)
            for i, chunk in enumerate(ignored_chunks):
                chunks.append({
                    'type': 'ignored_content',
                    'content': chunk.text,
                    'index': i
                })
        
        return chunks


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

''' 



def main():
    """Demo the PythonCodeParser functionality."""
    print("=== Python Code Parser Demo ===")
    
    # Parse mixed content
    parser = PythonCodeParser(SAMPLE_TEXT)
    
    print("\n1. Extracted Python Code:")
    print(parser.python_code)
    
    print("\n2. Ignored Content:")
    print(parser.ignored_content)
    
    # Get functions/classes and remaining code
    functions_classes, remaining_code = parser.extract_functions_and_classes()
    
    print(f"\n3. Found {len(functions_classes)} functions/classes")
    print("\n4. Remaining Code:")
    print(remaining_code)
    
    # Create all semantic chunks
    all_chunks = parser.create_all_chunks()
    
    print(f"\n5. All Chunks ({len(all_chunks)} total):")
    for chunk in all_chunks:
        print("--------------START------------------")
        print(f"\n--- {chunk['type'].upper()} #{chunk['index']} ---")
        print(chunk['content'])
        # print(chunk['content'][:200] + "..." if len(chunk['content']) > 200 else chunk['content'])
        print("--------------END------------------")

if __name__ == "__main__":
    main()