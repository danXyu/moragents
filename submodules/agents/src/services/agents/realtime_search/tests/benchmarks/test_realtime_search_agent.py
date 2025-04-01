import logging
from unittest.mock import Mock, patch

import pytest
from bs4 import BeautifulSoup
from langchain.schema import SystemMessage
from models.service.chat_models import AgentResponse, ChatRequest
from services.agents.realtime_search.agent import RealtimeSearchAgent
from services.agents.realtime_search.config import Config

logger = logging.getLogger(__name__)


@pytest.fixture
def realtime_search_agent():
    config = {
        "name": "realtime_search",
        "description": "Agent for real-time web searches",
    }
    llm = Mock()
    return RealtimeSearchAgent(config=config, llm=llm)


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_web_search_success(realtime_search_agent, make_chat_request):
    request = make_chat_request(
        content="Search for latest news about AI", agent_name="realtime_search"
    )

    mock_results = """
    Result:
    Latest breakthrough in AI technology announced
    Scientists develop new machine learning model
    """

    with patch.object(realtime_search_agent.tool_bound_llm, "invoke") as mock_invoke:
        mock_invoke.return_value = "Here are the latest AI developments..."

        response = await realtime_search_agent._process_request(request)

        assert isinstance(response, AgentResponse)
        assert response.response_type.value == "success"
        assert "latest AI developments" in response.content

        # Verify correct messages were passed
        expected_messages = [
            SystemMessage(
                content=(
                    "You are a real-time web search agent that helps find current information. "
                    "Ask for clarification if a request is ambiguous."
                )
            ),
            *request.messages_for_llm,
        ]
        mock_invoke.assert_called_once_with(expected_messages)


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_web_search_no_results(realtime_search_agent):
    search_term = "nonexistent topic"

    with patch.object(
        realtime_search_agent, "_perform_search_with_web_scraping"
    ) as mock_search:
        mock_search.return_value = AgentResponse.needs_info(
            content="I couldn't find any results for that search. Could you try rephrasing it?"
        )

        response = await realtime_search_agent._execute_tool(
            "perform_web_search", {"search_term": search_term}
        )

        assert isinstance(response, AgentResponse)
        assert response.response_type.value == "needs_info"
        assert "try rephrasing" in response.content


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_web_search_error_handling(realtime_search_agent):
    search_term = "test search"

    with patch.object(
        realtime_search_agent, "_perform_search_with_web_scraping"
    ) as mock_search:
        mock_search.side_effect = Exception("Search failed")

        response = await realtime_search_agent._execute_tool(
            "perform_web_search", {"search_term": search_term}
        )

        assert isinstance(response, AgentResponse)
        assert response.response_type.value == "error"
        assert "Search failed" in response.error_message


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_unknown_tool(realtime_search_agent):
    response = await realtime_search_agent._execute_tool("unknown_function", {})

    assert isinstance(response, AgentResponse)
    assert response.response_type.value == "error"
    assert "Unknown tool" in response.error_message


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_empty_search_term(realtime_search_agent):
    response = await realtime_search_agent._execute_tool(
        "perform_web_search", {"search_term": ""}
    )

    assert isinstance(response, AgentResponse)
    assert response.response_type.value == "needs_info"
    assert "provide a search term" in response.content
