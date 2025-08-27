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
                extracted_lines.update(range(start, end)) # type: ignore
        
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
