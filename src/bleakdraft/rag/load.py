import warnings
import sys
import os

from .vectorstore import VectorStoreManager
from .graph import RAGGraph
from .chonkiestore import ChonkieStore

# Sample code for testing
SAMPLE_TEXT = """
# Get glossary data
glossary, rules = get_user_glossary(1, 'english', 'spanish')



-- Sample data table data
SELECT * FROM data WHERE user_id = 5 AND input_language = 'data' AND target_language = 'data';



# Simplified get_user_glossary function
def get_user_glossary(user_id, input_lang, target_lang):
    '''Returns (glossary_dict, formatting_rules) for user/languages'''
    return {'World History': 'Historia Universal', 'execute': 'legalizar'}, \
           ['Use Spanish address format with comma separators']


What can be spoken about about the persons that are in earth
""" 

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



