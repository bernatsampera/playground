# Twitter AI Extension - Backend Testing Guide

## Quick Overview

This backend has 3 main testing workflows:
1. **Regenerate Answers** - Re-create all answers in `qa_history.json`
2. **Confidence Scoring** - Score QA pairs and categorize them
3. **Quality Scoring** - Check if replies sound natural

---

## Workflow 1: Regenerate Answers

**Purpose:** Re-generate ALL answers in `qa_history.json` using the latest prompt.

**File:** `regenerate_answers.py`

**Run:**
```bash
cd backend
uv run regenerate_answers.py
```

**What it does:**
- Reads all questions from `data/qa_history.json`
- Generates new answers using `prompts.get_tweet_generation_prompt()`
- Applies forbidden word filtering (max 2 retries)
- Overwrites `data/qa_history.json` with new answers

**Output example:**
```
Loading QA history from: data/qa_history.json
Found 11 QA pairs to regenerate.

[1/11] Processing: 503cf4f4-4eb4-4f87-af7b...
  Tweet: Day 89/90
Launched the app on a cycling sub...
  Old answer: ugh that sucks. it's always a sh...
  AI raw: damn that's rough. launching never goe...
  Cleaned: that's rough. launching never goes as p...

Saving 11 regenerated answers to: data/qa_history.json
Done!
```

---

## Workflow 2: Confidence Scoring

**Purpose:** Score all QA pairs and separate into "approved" (good) vs "rejected" (bad).

**File:** `confidence/confidence_scorer.py`

**Run:**
```bash
cd backend
uv run confidence/confidence_scorer.py
```

**What it does:**
- Reads all QA pairs from `data/qa_history.json`
- Scores each (0.0 to 1.0) using LLM analysis
- Categorizes: score >= 0.7 = approved, score < 0.7 = rejected
- Saves results to `data/scored_history.json`

**Output example:**
```
Confidence Scorer - Analyzing all QA pairs

==================================================
Loading QA pairs from qa_history.json...

Scoring complete! Processed 11 pairs.

==================================================
RESULTS:
==================================================

ID: 503cf4f4-4eb4-4f87-af7b...
Score: 0.7
Reason: Good answer, but could be more specific...
Q: Tweet: Day 89/90
Launched the app on a cycling sub...
A: ugh that sucks. it's always a sh...

==================================================
Approved (score >= 0.7): 2
Rejected (score < 0.7): 9
==================================================
```

**Output file:** `data/scored_history.json`
```json
{
  "approved": {
    "qa-id-1": {
      "question": "...",
      "answer": "...",
      "score": 1.0,
      "reason": "Perfect answer, very detailed and specific."
    }
  },
  "rejected": {
    "qa-id-2": {
      "question": "...",
      "answer": "...",
      "score": 0.3,
      "reason": "Uses damn and uses emojis."
    }
  }
}
```

---

## Workflow 3: Interactive Testing (Single Reply)

**Purpose:** Test a single tweet and get a reply + quality score.

**File:** `server.py` (FastAPI server)

**Run:**
```bash
cd backend
uv run -m uvicorn server:app --reload
```

**Test via API:**
```bash
curl -X POST http://localhost:8000/api/analyze_tweet \
  -H "Content-Type: application/json" \
  -d '{
    "tweet_text": "Building in public is overrated.",
    "tweet_url": "https://twitter.com/user/status/123"
  }'
```

**Response:**
```json
{
  "reply": "fair point actually. lots of people just doing it for the clout",
  "question_id": "...",
  "quality_score": 75.0,
  "quality_feedback": "Good natural tone",
  "quality_breakdown": {
    "naturalness": 25,
    "length_appropriateness": 18,
    "twitter_authenticity": 27,
    "ai_penalty": 5
  }
}
```

---

## Testing Cycle (Recommended)

When tweaking prompts or logic:

1. **Edit** `prompts.py` or `tweet_generation/forbidden_words.py`

2. **Regenerate answers:**
   ```bash
   uv run regenerate_answers.py
   ```

3. **Score the results:**
   ```bash
   uv run confidence/confidence_scorer.py
   ```

4. **Review** `data/scored_history.json`:
   - Check approved vs rejected counts
   - Read reasons for low scores
   - Iterate on prompts

5. **Manual review** of `data/qa_history.json`:
   - Open the file
   - Check if answers sound natural
   - Add good/bad examples to `data/example_scores.json`

---

## Files Reference

| File | Purpose |
|------|---------|
| `regenerate_answers.py` | Regenerate ALL answers |
| `confidence/confidence_scorer.py` | Score QA pairs |
| `server.py` | FastAPI API server |
| `prompts.py` | **Edit this to change prompts** |
| `tweet_generation/forbidden_words.py` | **Edit this to add/remove forbidden words** |
| `data/qa_history.json` | Input for scoring, output of regeneration |
| `data/scored_history.json` | Output of confidence scoring |
| `data/example_scores.json` | Reference examples for scoring |

---

## Quick Commands

```bash
# Regenerate all answers
uv run regenerate_answers.py

# Score all QA pairs
uv run confidence/confidence_scorer.py

# Start API server
uv run -m uvicorn server:app --reload
```
