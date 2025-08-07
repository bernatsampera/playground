from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from collections import defaultdict
import chromadb

data = [
    {"id": 1, "key": "chroma:document", "string_value": "class State(TypedDict): \n    text_1: str\n    text_2: str"},
    {"id": 1, "key": "type", "string_value": "python"},
    {"id": 2, "key": "chroma:document", "string_value": "def create_interrupt_payload(text: str) -> dict: \n    return {""text_to_revise"": text}"},
    {"id": 2, "key": "type", "string_value": "python"},
    {"id": 3, "key": "chroma:document", "string_value": "def process_human_input(state: State, text_key: str) -> dict: \n    value = interrupt(create_interrupt_payload(state[text_key])) \n    return {text_key: value}"},
    {"id": 3, "key": "type", "string_value": "python"},
]

# Initialize Ollama model
llm = ChatOllama(model="llama3.1", temperature=0)

# Group entries by Id
documents = defaultdict(list)
for entry in data:
    documents[entry["id"]].append((entry["key"], entry["string_value"]))

# Step 1: Analyze content using AI
analyze_prompt = PromptTemplate(
    input_variables=["document_id", "content"],
    template="Analyze the following document (ID: {document_id}) and extract key concepts as a comma-separated list. Focus on the main purpose or functionality described in the content. Do not include details not present in the provided text.\n\nContent: {content}"
)

concepts = {}
for doc_id, entries in documents.items():
    content = " ".join([entry[1] for entry in entries if entry[0] == "chroma:document"])
    if content:
        chain = analyze_prompt | llm
        result = chain.invoke({"document_id": doc_id, "content": content})
        concepts[doc_id] = result.content.strip().split(", ")

# Step 2: Generate summary with inline references using AI, ensuring no repeated references
summary_prompt = PromptTemplate(
    input_variables=["concepts"],
    template="""
    Generate a concise summary of the topic based on the following key concepts from multiple documents. 
    Integrate references to document IDs inline within the text (e.g., [Ref: Document 1]),ensuring each document ID is referenced only once. 
    Ensure the summary is accurate, cohesive, and only based on the provided concepts.\n\nConcepts: {concepts}


    Explain the summary in a way that is easy to understand and follow. and the refereneces just appear one single time.
    """
)

# Format concepts for prompt
concepts_str = "\n".join([f"Document {doc_id}: {', '.join(doc_concepts)}" for doc_id, doc_concepts in concepts.items()])
chain = summary_prompt | llm
summary = chain.invoke({"concepts": concepts_str})

# Output the summary
print(summary.content.strip())

