from pygments.lexers import guess_lexer, get_lexer_by_name
from pygments.util import ClassNotFound

from pygments.lexers import guess_lexer
from pygments.util import ClassNotFound

def _detect_content_type(text: str) -> str:
    """Detect programming language using Pygments with misdetection fixes."""
    lexer = guess_lexer(text)
    language = lexer.aliases[0] if lexer.aliases else lexer.name.lower()
    misdetection_fixes = {
        'teratermmacro': 'python',
        'gdscript': 'javascript',
    }
    
    if language in misdetection_fixes:
        return misdetection_fixes[language]
    return language or ""

    

print(_detect_content_type("""\
# Prompt

You are a helpful assistant that can answer questions and help with tasks.

# Code

def add(a, b):
    return a + b
"""))

print(_detect_content_type("""\
func _on_start_sim():
	var closest_car = get_closest_car()
	if closest_car:
		self.drive_to_car(closest_car)
	else:
		print("No car found")
	

func get_closest_car():
	return get_tree().get_nodes_in_group("car")[0]
	
"""))