import feedparser
from langchain.chat_models import init_chat_model

# 1. CONFIGURATION: Your "Newspaper" Sources
# You can swap these for ESPN/NBA feeds later easily.
rss_sources = [
    "https://news.ycombinator.com/rss",  # HackerNews
    "https://dev.to/feed",  # Dev.to
    "https://openai.com/blog/rss.xml",  # OpenAI Blog
    "https://react.dev/feed.xml",  # React Blog
]

llm = init_chat_model("ollama:gemma3:12b")


def get_smart_news():
    print("1. Harvesting RSS feeds...")

    # A list to hold the raw candidates
    candidates = []

    # 2. THE HARVESTER: Fetch data from sources
    for url in rss_sources:
        feed = feedparser.parse(url)
        # We only take the top 5 from each to keep the context window small
        for entry in feed.entries[:5]:
            candidates.append(
                {
                    "title": entry.title,
                    "link": entry.link,
                    # Some feeds don't have summaries, so we handle that
                    "summary_raw": entry.get("summary", entry.title),
                }
            )

    print(f"   Collected {len(candidates)} raw headlines.")

    # 3. THE EDITOR: Prepare the prompt for the AI
    # We create a text block representing all news items to send to the LLM
    candidates_text = "\n".join(
        [
            f"ID: {i} | Title: {c['title']} | Context: {c['summary_raw']}"
            for i, c in enumerate(candidates)
        ]
    )

    return candidates_text


# Run it
if __name__ == "__main__":
    final_stories = get_smart_news()

    print("\n--- YOUR SMART FEED ---")
    print(final_stories)
