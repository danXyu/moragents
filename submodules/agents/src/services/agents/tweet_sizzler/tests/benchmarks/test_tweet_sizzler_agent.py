import logging
from typing import Any, Dict
from unittest.mock import patch

import pytest
from models.service.chat_models import AgentResponse
from services.agents.tweet_sizzler.agent import TweetSizzlerAgent

logger = logging.getLogger(__name__)


@pytest.fixture
def tweet_sizzler_agent(llm):
    config: Dict[str, Any] = {
        "name": "tweet_sizzler",
        "description": "Agent for generating and posting tweets",
    }
    return TweetSizzlerAgent(config, llm)


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_generate_tweet_success(tweet_sizzler_agent, make_chat_request):
    request = make_chat_request(content="Write a tweet about AI")

    with patch.object(tweet_sizzler_agent.tool_bound_llm, "ainvoke") as mock_invoke:
        mock_invoke.return_value = {
            "tool_calls": [
                {
                    "function": {
                        "name": "generate_tweet",
                        "arguments": {"content": "AI is transforming our world! #AI #Technology"},
                    }
                }
            ]
        }

        with patch("services.agents.tweet_sizzler.tools.generate_tweet") as mock_generate:
            mock_generate.return_value = "AI is transforming our world! #AI #Technology"
            response = await tweet_sizzler_agent._process_request(request)

            assert isinstance(response, AgentResponse)
            assert response.response_type.value == "success"
            assert "AI is transforming" in response.content


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_execute_tool_generate_tweet(tweet_sizzler_agent):
    args: Dict[str, Any] = {"content": "Test tweet content"}

    with patch("services.agents.tweet_sizzler.tools.generate_tweet") as mock_generate:
        mock_generate.return_value = (
            "Just testing the waters with this tweet, stay tuned for more excitement to come #testing"
        )
        response = await tweet_sizzler_agent._execute_tool("generate_tweet", args)

        assert isinstance(response, AgentResponse)
        assert response.response_type.value == "success"
        assert mock_generate.return_value in response.content


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_execute_tool_missing_content(tweet_sizzler_agent):
    args: Dict[str, Any] = {}
    response = await tweet_sizzler_agent._execute_tool("generate_tweet", args)

    assert isinstance(response, AgentResponse)
    assert response.response_type.value == "error"
    assert "Please provide content" in response.error_message


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_execute_unknown_tool(tweet_sizzler_agent):
    response = await tweet_sizzler_agent._execute_tool("unknown_tool", {})

    assert isinstance(response, AgentResponse)
    assert response.response_type.value == "error"
    assert "Unknown tool function" in response.error_message


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_tweet_generation_error(tweet_sizzler_agent, make_chat_request):
    request = make_chat_request(content="Write a tweet")

    with patch.object(
        tweet_sizzler_agent.tool_bound_llm,
        "ainvoke",
        side_effect=Exception("LLM Error"),
    ):
        response = await tweet_sizzler_agent._process_request(request)

        assert isinstance(response, AgentResponse)
        assert response.response_type.value == "error"
        assert "LLM Error" in response.error_message
