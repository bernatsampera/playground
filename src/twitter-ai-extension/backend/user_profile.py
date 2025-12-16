from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel


class UserProfile(BaseModel):
    """User writing style profile for personalized AI replies"""

    # Punctuation patterns
    punctuation_frequency: float = 0.5  # 0-1, how often they use punctuation
    exclamation_usage: float = 0.2  # 0-1, frequency of exclamation marks
    question_usage: float = 0.3  # 0-1, frequency of questions

    # Capitalization style
    capitalization_style: str = "casual"  # casual, proper, random, lowercase
    capitalized_word_ratio: float = 0.1  # ratio of words that are capitalized

    # Language patterns
    emoji_frequency: float = 0.3  # 0-1, how often they use emojis
    abbreviation_frequency: float = 0.4  # 0-1, how often they use abbreviations (lol, brb, etc)
    slang_usage: float = 0.3  # 0-1, how much slang they use

    # Reply characteristics
    avg_reply_length: int = 15  # average word count
    sentence_fragment_ratio: float = 0.3  # ratio of replies that are fragments
    casual_opener_frequency: float = 0.2  # uses "yo", "hey", "lol" as openers

    # Common patterns
    common_exclamations: List[str] = []  # ["lol", "lmao", "haha", "wow", "omg"]
    favorite_emojis: List[str] = []  # ["😂", "👀", "🔥", "💯", "🤔"]
    frequent_abbrs: List[str] = []  # ["ngl", "tbh", "fr", "iykyk", "ikr"]
    common_starters: List[str] = []  # ["honestly", "ngl", "tbh", "lowkey"]
    common_enders: List[str] = []  # ["tbh", "fr", "imo", "ngl"]

    # Personality traits
    energy_level: float = 0.5  # 0-1, calm to energetic
    sarcasm_frequency: float = 0.1  # 0-1, how often they use sarcasm
    agreement_style: str = "direct"  # direct, enthusiastic, reserved, questioning

    # Learning metadata
    samples_analyzed: int = 0
    last_updated: datetime = datetime.now()
    edit_patterns: Dict[str, float] = {}  # Tracks how users edit AI suggestions

    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> 'UserProfile':
        """Create from dictionary"""
        if 'last_updated' in data and isinstance(data['last_updated'], str):
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return cls(**data)

    def update_from_reply(self, original_ai: str, user_modified: str) -> None:
        """Update profile based on how user modified AI suggestion"""
        # Track edit patterns
        if len(user_modified) < len(original_ai):
            self.edit_patterns["shorten"] = self.edit_patterns.get("shorten", 0) + 1
        elif len(user_modified) > len(original_ai):
            self.edit_patterns["lengthen"] = self.edit_patterns.get("lengthen", 0) + 1

        # Update average reply length
        words = len(user_modified.split())
        self.avg_reply_length = (self.avg_reply_length * self.samples_analyzed + words) / (self.samples_analyzed + 1)

        # Analyze punctuation changes
        punct_count = user_modified.count('.') + user_modified.count('!') + user_modified.count('?')
        self.punctuation_frequency = (self.punctuation_frequency * self.samples_analyzed + (punct_count / max(words, 1))) / (self.samples_analyzed + 1)

        # Check for emoji usage
        import re
        emoji_count = len(re.findall(r'[😀-🿿]', user_modified))
        self.emoji_frequency = (self.emoji_frequency * self.samples_analyzed + (1 if emoji_count > 0 else 0)) / (self.samples_analyzed + 1)

        self.samples_analyzed += 1
        self.last_updated = datetime.now()

    def get_style_prompt_addition(self) -> str:
        """Get prompt additions based on user's learned style"""
        style_hints = []

        # Punctuation hints
        if self.punctuation_frequency < 0.3:
            style_hints.append("minimal punctuation")
        elif self.punctuation_frequency > 0.7:
            style_hints.append("proper punctuation")

        # Capitalization hints
        if self.capitalization_style == "lowercase":
            style_hints.append("mostly lowercase")
        elif self.capitalization_style == "casual":
            style_hints.append("casual capitalization")

        # Emoji hints
        if self.emoji_frequency > 0.6:
            style_hints.append("use emojis sometimes")

        # Length hint
        if self.avg_reply_length < 10:
            style_hints.append("very short replies")
        elif self.avg_reply_length > 25:
            style_hints.append("longer thoughtful replies")

        # Energy hints
        if self.energy_level > 0.7:
            style_hints.append("high energy")
        elif self.energy_level < 0.3:
            style_hints.append("chill and relaxed")

        # Combine into a single style instruction
        if style_hints:
            return f"User style: {', '.join(style_hints)}."
        return ""