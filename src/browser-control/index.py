import asyncio

from browser_use import Agent, Browser, ChatBrowserUse
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file


async def example():
    browser = Browser(
        # use_cloud=True,  # Uncomment to use a stealth browser on Browser Use Cloud
    )

    llm = ChatBrowserUse()

    agent = Agent(
        task="Find the number of stars of the browser-use repo",
        llm=llm,
        browser=browser,
    )

    history = await agent.run()
    return history


if __name__ == "__main__":
    history = asyncio.run(example())
