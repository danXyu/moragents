import logging
from typing import Any, Dict, List

import pyshorteners
from langchain.schema import HumanMessage, SystemMessage
from models.service.agent_core import AgentCore
from models.service.chat_models import AgentResponse, ChatRequest
from services.agents.news_agent.config import Config
from services.agents.news_agent.tools import clean_html, fetch_rss_feed, is_within_time_window

logger = logging.getLogger(__name__)


class NewsAgent(AgentCore):
    """Agent for fetching and analyzing cryptocurrency news."""

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.tools_provided = Config.tools
        self.url_shortener = pyshorteners.Shortener()

    async def _process_request(self, request: ChatRequest) -> AgentResponse:
        """Process the validated chat request for news-related queries."""
        try:
            messages = [
                SystemMessage(
                    content=(
                        "You are a news analysis agent that fetches and analyzes cryptocurrency news. "
                        "Ask for clarification if a request is ambiguous."
                    )
                ),
                *request.messages_for_llm,
            ]

            response = await self._call_llm_with_tools(messages, self.tools_provided)
            return await self._handle_llm_response(response)

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return AgentResponse.needs_info(
                content="I ran into an issue processing your request. Could you try rephrasing it?"
            )

    async def _execute_tool(self, func_name: str, args: dict) -> AgentResponse:
        """Execute the appropriate news tool based on function name."""
        try:
            if func_name == "fetch_crypto_news":
                coins = args.get("coins", [])
                if not coins:
                    return AgentResponse.needs_info(
                        content="Could you specify which cryptocurrencies you'd like news about?"
                    )

                news = self._fetch_crypto_news(coins)
                if not news:
                    return AgentResponse.success(
                        content="No relevant news found for the specified cryptocurrencies in the last 24 hours."
                    )

                response = (
                    "Here are the latest news items relevant to "
                    + "changes in price movement of the mentioned tokens in the last 24 hours:\n\n"
                )
                for index, item in enumerate(news, start=1):
                    coin_name = Config.CRYPTO_DICT.get(item["Coin"], item["Coin"])
                    short_url = self.url_shortener.tinyurl.short(item["Link"])
                    response += f"{index}. ***{coin_name} News***:\n"
                    response += f"{item['Title']}\n"
                    response += f"{item['Summary']}\n"
                    response += f"Read more: {short_url}\n\n"

                return AgentResponse.success(content=response)
            else:
                return AgentResponse.needs_info(
                    content="I don't know how to handle that type of request. "
                    + "Could you try asking about cryptocurrency news instead?"
                )

        except Exception as e:
            logger.error(f"Error executing tool {func_name}: {str(e)}", exc_info=True)
            return AgentResponse.needs_info(content="I encountered an issue fetching the news. Could you try again?")

    async def _check_relevance_and_summarize(self, title: str, content: str, coin: str) -> str:
        """Check if news is relevant and generate summary."""
        logger.info(f"Checking relevance for {coin}: {title}")
        prompt = Config.RELEVANCE_PROMPT.format(coin=coin, title=title, content=content)
        messages = [HumanMessage(content=prompt)]

        # Call LLM with empty tools list to get direct response
        response = await self._call_llm_with_tools(messages, [])

        if response.content:
            return response.content.strip()
        else:
            return "Error analyzing relevance"

    def _process_rss_feed(self, feed_url: str, coin: str) -> List[Dict[str, str]]:
        """Process RSS feed and filter relevant articles."""
        logger.info(f"Processing RSS feed for {coin}: {feed_url}")
        feed = fetch_rss_feed(feed_url)
        results = []
        for entry in (feed.entries or [])[:5]:  # Process max 5 entries
            published_time = entry.get("published") or entry.get("updated")
            if is_within_time_window(published_time):
                title = clean_html(entry.title)
                content = clean_html(entry.summary)
                logger.info(f"Checking relevance for article: {title}")
                # Use asyncio.run to call the async method from a sync context
                import asyncio

                result = asyncio.run(self._check_relevance_and_summarize(title, content, coin))
                if not result.upper().startswith("NOT RELEVANT"):
                    results.append({"Title": title, "Summary": result, "Link": entry.link})
                if len(results) >= Config.ARTICLES_PER_TOKEN:
                    break
            else:
                logger.info(f"Skipping article: {entry.title} (published: {published_time})")
        logger.info(f"Found {len(results)} relevant articles for {coin}")
        return results

    def _fetch_crypto_news(self, coins: List[str]) -> List[Dict[str, str]]:
        """Fetch and process news for specified coins."""
        logger.info(f"Fetching news for coins: {coins}")
        all_news = []
        for coin in coins:
            logger.info(f"Processing news for {coin}")
            coin_name = Config.CRYPTO_DICT.get(coin.upper(), coin)
            google_news_url = Config.GOOGLE_NEWS_BASE_URL.format(coin_name)
            results = self._process_rss_feed(google_news_url, coin_name)
            all_news.extend([{"Coin": coin, **result} for result in results[: Config.ARTICLES_PER_TOKEN]])

        logger.info(f"Total news items fetched: {len(all_news)}")
        return all_news
