"""
Centralized AI configuration for the Twitter AI extension.

All AI model instantiation should use this module to ensure
consistent configuration across the application.
"""

from langchain_ollama import ChatOllama

# Default model to use across the application
DEFAULT_MODEL = "gemma3:12b"

# Temperature presets for different use cases
TEMP_PRESET_CREATIVE = 0.9  # Short, casual replies
TEMP_PRESET_BALANCED = 0.8  # Medium tweets, content cleaning
TEMP_PRESET_FOCUSED = 0.7  # Longer tweets
TEMP_PRESET_PRECISE = 0.3  # Confidence scoring


def get_model(
    model: str = DEFAULT_MODEL, temperature: float = TEMP_PRESET_FOCUSED
) -> ChatOllama:
    """
    Create a ChatOllama model instance with the specified configuration.

    Args:
        model: The model name to use (defaults to gemma3:12b)
        temperature: Temperature setting (0.0-1.0)

    Returns:
        Configured ChatOllama instance
    """
    return ChatOllama(model=model, temperature=temperature)


def get_model_for_context(tweet_text: str, model: str = DEFAULT_MODEL) -> ChatOllama:
    """
    Dynamic temperature based on context and expected reply length.

    Shorter, more casual replies need higher temperature for creativity.
    Longer, more thoughtful replies can use lower temperature.

    Args:
        tweet_text: The original tweet text to analyze
        model: The model name to use (defaults to gemma3:12b)

    Returns:
        Configured ChatOllama instance with appropriate temperature
    """
    if len(tweet_text) < 100:  # Short tweet
        temp = TEMP_PRESET_CREATIVE
    elif len(tweet_text) < 200:  # Medium tweet
        temp = TEMP_PRESET_BALANCED
    else:  # Long tweet
        temp = TEMP_PRESET_FOCUSED

    return get_model(model=model, temperature=temp)


def get_confidence_scorer_model(model: str = DEFAULT_MODEL) -> ChatOllama:
    """
    Get a model configured for confidence scoring.

    Uses lower temperature for more consistent, precise scoring.

    Args:
        model: The model name to use (defaults to gemma3:12b)

    Returns:
        Configured ChatOllama instance for confidence scoring
    """
    return get_model(model=model, temperature=TEMP_PRESET_PRECISE)


def get_content_cleaning_model(model: str = DEFAULT_MODEL) -> ChatOllama:
    """
    Get a model configured for content cleaning (forbidden word removal).

    Args:
        model: The model name to use (defaults to gemma3:12b)

    Returns:
        Configured ChatOllama instance for content cleaning
    """
    return get_model(model=model, temperature=TEMP_PRESET_BALANCED)
