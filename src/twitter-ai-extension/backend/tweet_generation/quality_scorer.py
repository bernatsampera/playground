import re
from typing import List, Dict


class ReplyScorer:
    """Scores AI-generated replies for naturalness and quality"""

    def __init__(self):
        # Patterns that indicate natural language
        self.natural_patterns = [
            r'\b(lol|lmao|rofl)\b',  # Laughter
            r'\b(omg|wtf|wth)\b',   # Exclamations
            r'\b(ngl|tbh|fr|iykyk|ikr|ngl)\b',  # Abbreviations
            r'\b(lowkey|highkey)\b',  # Slang
            r'\b(vibing|vibe)\b',    # Casual language
            r'\b(legit|deadass)\b',  # Emphatic slang
            r'\b(yo|hey|yo yo)\b',   # Casual greetings
            r'\b(wild|crazy|insane)\b',  # Informal intensifiers
            r'\b(bet|bet)\b',        # Agreement
            r'\b(periodt|period)\b',  # Emphasis
            r'\b(slay|slaying)\b',   # Modern slang
            r'\b(bro|fam|dude)\b',   # Casual address
            r'\b(no way|hell yeah|hell no)\b',  # Informal responses
            r'\b(bc|cuz|cause)\b',   # Casual because
            r'\b(u|ur|r)\b',         # Text speak
        ]

        # Patterns that indicate AI/formal language
        self.ai_patterns = [
            r'\b(furthermore|moreover|additionally)\b',
            r'\b(in conclusion|to summarize|in summary)\b',
            r'\b(it should be noted|it is worth noting)\b',
            r'\b(the aforementioned|the aforementioned)\b',
            r'\b(hence|thus|therefore)\b',
            r'\b(nevertheless|nonetheless|however)\b',
            r'\b(utilize|leverage|optimize)\b',
            r'\b(seamless|innovative|powerful)\b',
            r'\b(amazing|wonderful|fantastic)\b',
        ]

        # Twitter-specific natural patterns
        self.twitter_patterns = [
            r'^\s*\.',  # Starting with just a period
            r'\s+',     # Extra spaces (common on mobile)
            r'(?<!\w)(i|I)(?!\w)\b',  # Standalone 'i' without capitalization
            r'[.!?]{3,}',  # Multiple punctuation marks
            r'\b\d{1,2}[a-zA-Z]{2,}\b',  # 2day, 4get, etc
        ]

    def score_reply(self, reply: str, original_tweet: str) -> Dict[str, float]:
        """Generate quality scores for a reply"""
        scores = {
            'naturalness': 0.0,
            'length_appropriateness': 0.0,
            'twitter_authenticity': 0.0,
            'ai_penalty': 0.0,
            'total_score': 0.0
        }

        # 1. Natural language patterns (max 30 points)
        natural_score = 0
        for pattern in self.natural_patterns:
            matches = len(re.findall(pattern, reply, re.IGNORECASE))
            natural_score += min(matches * 5, 15)  # Cap at 15 points per pattern
        scores['naturalness'] = min(natural_score, 30) / 30

        # 2. Length appropriateness (max 20 points)
        tweet_length = len(original_tweet.split())
        reply_length = len(reply.split())

        if reply_length <= 5:  # Very short, good for Twitter
            length_score = 20
        elif reply_length <= 15:  # Good short reply
            length_score = 15
        elif reply_length <= 30:  # Medium length
            length_score = 10
        else:  # Too long
            length_score = max(0, 10 - (reply_length - 30))
        scores['length_appropriateness'] = length_score / 20

        # 3. Twitter authenticity (max 30 points)
        twitter_score = 0

        # Check for lowercase usage
        if not reply[0].isupper() if reply else False:
            twitter_score += 5

        # Check for casual patterns
        for pattern in self.twitter_patterns:
            if re.search(pattern, reply):
                twitter_score += 5

        # Bonus for very casual features
        if re.search(r'[.]{2,}', reply):  # Multiple periods
            twitter_score += 5
        if re.search(r'\b(lol|haha|lmao)\b', reply, re.IGNORECASE):
            twitter_score += 5

        scores['twitter_authenticity'] = min(twitter_score, 30) / 30

        # 4. AI language penalty (subtract up to 20 points)
        ai_penalty = 0
        for pattern in self.ai_patterns:
            matches = len(re.findall(pattern, reply, re.IGNORECASE))
            ai_penalty += matches * 10
        scores['ai_penalty'] = min(ai_penalty, 20) / 20

        # 5. Calculate total score (0-100)
        base_score = (scores['naturalness'] * 30 +
                     scores['length_appropriateness'] * 20 +
                     scores['twitter_authenticity'] * 30)

        scores['total_score'] = max(0, base_score - (scores['ai_penalty'] * 20))

        return scores

    def get_feedback_message(self, scores: Dict[str, float]) -> str:
        """Generate feedback based on scores"""
        total = scores['total_score']

        if total >= 80:
            return "Great! Sounds very natural."
        elif total >= 60:
            if scores['ai_penalty'] > 0.3:
                return "A bit formal, try removing some corporate words."
            elif scores['length_appropriateness'] < 0.5:
                return "Could be shorter for Twitter."
            else:
                return "Good, but could be more casual."
        else:
            feedback = []
            if scores['naturalness'] < 0.3:
                feedback.append("add some slang or abbreviations")
            if scores['twitter_authenticity'] < 0.3:
                feedback.append("use more casual punctuation")
            if scores['length_appropriateness'] < 0.3:
                feedback.append("make it shorter")
            return f"Try to {', '.join(feedback)}."

    def is_reply_good(self, scores: Dict[str, float]) -> bool:
        """Quick check if reply meets minimum quality threshold"""
        return scores['total_score'] >= 70