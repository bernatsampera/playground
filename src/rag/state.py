from typing import TypedDict, Optional

class HybridState(TypedDict):
    question: str
    rag_context: Optional[str]
    answer: Optional[str] 