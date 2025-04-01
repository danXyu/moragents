import logging
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest
from models.service.chat_models import AgentResponse, ChatRequest
from services.agents.rugcheck.agent import RugcheckAgent
from services.agents.rugcheck.tool_types import RugcheckToolType
from services.agents.rugcheck.tools import (
    fetch_most_viewed,
    fetch_most_voted,
    fetch_token_report,
)

logger = logging.getLogger(__name__)


@pytest.fixture
def rugcheck_agent(llm):
    config: Dict[str, Any] = {
        "name": "rugcheck",
        "description": "Agent for analyzing token safety",
    }
    return RugcheckAgent(config, llm)


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_token_report_success(rugcheck_agent, make_chat_request):
    request = make_chat_request(content="Analyze token BONK")

    with patch.object(rugcheck_agent.tool_bound_llm, "invoke") as mock_invoke:
        mock_invoke.return_value = {
            "tool_calls": [
                {
                    "function": {
                        "name": RugcheckToolType.GET_TOKEN_REPORT.value,
                        "arguments": {"identifier": "BONK"},
                    }
                }
            ]
        }

        with patch("services.agents.rugcheck.tools.resolve_token_identifier") as mock_resolve:
            mock_resolve.return_value = "BONK123"

            with patch("services.agents.rugcheck.tools.fetch_token_report") as mock_fetch:
                mock_fetch.return_value.formatted_response = "Token Analysis Report\nOverall Risk Score: 85"
                mock_fetch.return_value.model_dump.return_value = {
                    "score": 85,
                    "risks": [
                        {
                            "name": "Liquidity Risk",
                            "description": "Low liquidity detected",
                            "score": 60,
                        }
                    ],
                }

                response = await rugcheck_agent._process_request(request)

                assert isinstance(response, AgentResponse)
                assert response.response_type.value == "success"
                assert "Token Analysis Report" in response.content
                assert "Overall Risk Score: 85" in response.content


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_most_viewed_success(rugcheck_agent):
    with patch("services.agents.rugcheck.tools.fetch_most_viewed") as mock_fetch:
        mock_fetch.return_value.formatted_response = "Most Viewed Tokens\nToken1: 1000 visits"
        mock_fetch.return_value.model_dump.return_value = {
            "tokens": [
                {
                    "mint": "mint123",
                    "metadata": {"name": "Token1", "symbol": "TK1"},
                    "visits": 1000,
                    "user_visits": 500,
                }
            ]
        }

        response = await rugcheck_agent._execute_tool(RugcheckToolType.GET_MOST_VIEWED.value, {})

        assert isinstance(response, AgentResponse)
        assert response.response_type.value == "success"
        assert "Most Viewed Tokens" in response.content
        assert "Token1" in response.content


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_most_voted_success(rugcheck_agent):
    with patch("services.agents.rugcheck.tools.fetch_most_voted") as mock_fetch:
        mock_fetch.return_value.formatted_response = "Most Voted Tokens\nToken1: 100 upvotes"
        mock_fetch.return_value.model_dump.return_value = {
            "tokens": [{"mint": "mint123", "up_count": 100, "vote_count": 150}]
        }

        response = await rugcheck_agent._execute_tool(RugcheckToolType.GET_MOST_VOTED.value, {})

        assert isinstance(response, AgentResponse)
        assert response.response_type.value == "success"
        assert "Most Voted Tokens" in response.content


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_invalid_token_identifier(rugcheck_agent):
    with patch("services.agents.rugcheck.tools.resolve_token_identifier") as mock_resolve:
        mock_resolve.return_value = None

        response = await rugcheck_agent._execute_tool(
            RugcheckToolType.GET_TOKEN_REPORT.value, {"identifier": "INVALID_TOKEN"}
        )

        assert isinstance(response, AgentResponse)
        assert response.response_type.value == "error"
        assert "Could not resolve token identifier" in response.error_message


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_unknown_tool(rugcheck_agent):
    response = await rugcheck_agent._execute_tool("unknown_function", {})

    assert isinstance(response, AgentResponse)
    assert response.response_type.value == "error"
    assert "Unknown tool function" in response.error_message


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_api_error_handling(rugcheck_agent):
    with patch("services.agents.rugcheck.tools.resolve_token_identifier") as mock_resolve:
        mock_resolve.return_value = "mint123"

        with patch("services.agents.rugcheck.tools.fetch_token_report") as mock_fetch:
            mock_fetch.side_effect = Exception("API Error")

            response = await rugcheck_agent._execute_tool(
                RugcheckToolType.GET_TOKEN_REPORT.value, {"identifier": "TOKEN"}
            )

            assert isinstance(response, AgentResponse)
            assert response.response_type.value == "error"
            assert "Failed to get token report" in response.error_message
