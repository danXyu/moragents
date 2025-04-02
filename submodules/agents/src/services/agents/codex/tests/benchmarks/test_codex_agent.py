import logging
from typing import Any, Dict
from unittest.mock import patch

import pytest
from models.service.chat_models import AgentResponse
from services.agents.codex.agent import CodexAgent
from services.agents.codex.models import NftSearchResponse, TopHoldersResponse, TopTokensResponse
from services.agents.codex.utils.tool_types import CodexToolType

logger = logging.getLogger(__name__)


@pytest.fixture
def codex_agent(llm):
    config: Dict[str, Any] = {"name": "codex", "description": "Agent for Codex.io API"}
    return CodexAgent(config=config, llm=llm)


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_list_top_tokens_success(codex_agent, make_chat_request):
    request = make_chat_request(content="List top tokens", agent_name="codex")

    with patch("services.agents.codex.tools.list_top_tokens") as mock_tokens:
        mock_response = TopTokensResponse(formatted_response="Top tokens list")
        mock_tokens.return_value = mock_response

        response = await codex_agent._process_request(request)

        assert isinstance(response, AgentResponse)
        assert response.response_type.value == "success"
        assert response.content == "Top tokens list"
        assert response.action_type == CodexToolType.LIST_TOP_TOKENS.value


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_get_top_holders_success(codex_agent, make_chat_request):
    request = make_chat_request(content="Get top holders for Bitcoin on Ethereum", agent_name="codex")

    with patch("services.agents.codex.tools.get_top_holders_percent") as mock_holders:
        mock_response = TopHoldersResponse(formatted_response="Top holders data")
        mock_holders.return_value = mock_response

        response = await codex_agent._process_request(request)

        assert isinstance(response, AgentResponse)
        assert response.response_type.value == "success"
        assert response.content == "Top holders data"
        assert response.action_type == CodexToolType.GET_TOP_HOLDERS_PERCENT.value


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_search_nfts_success(codex_agent, make_chat_request):
    request = make_chat_request(content="Search for BAYC NFTs", agent_name="codex")

    with patch("services.agents.codex.tools.search_nfts") as mock_search:
        mock_response = NftSearchResponse(formatted_response="NFT search results")
        mock_search.return_value = mock_response

        response = await codex_agent._process_request(request)

        assert isinstance(response, AgentResponse)
        assert response.response_type.value == "success"
        assert response.content == "NFT search results"
        assert response.action_type == CodexToolType.SEARCH_NFTS.value


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_top_holders_missing_token(codex_agent, make_chat_request):
    request = make_chat_request(content="Get top holders on Ethereum", agent_name="codex")

    response = await codex_agent._process_request(request)

    assert isinstance(response, AgentResponse)
    assert response.response_type.value == "needs_info"
    assert "Please specify both the token name and network" in response.content


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_top_holders_missing_network(codex_agent, make_chat_request):
    request = make_chat_request(content="Get top holders for Bitcoin", agent_name="codex")

    response = await codex_agent._process_request(request)

    assert isinstance(response, AgentResponse)
    assert response.response_type.value == "needs_info"
    assert "Please specify the network" in response.content


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_top_holders_invalid_network(codex_agent, make_chat_request):
    request = make_chat_request(content="Get top holders for Bitcoin on InvalidNetwork", agent_name="codex")

    response = await codex_agent._process_request(request)

    assert isinstance(response, AgentResponse)
    assert response.response_type.value == "needs_info"
    assert "Please specify a valid network" in response.content


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_unknown_tool(codex_agent, make_chat_request):
    request = make_chat_request(content="Do something invalid", agent_name="codex")

    response = await codex_agent._process_request(request)

    assert isinstance(response, AgentResponse)
    assert response.response_type.value == "error"
    assert "Unknown tool" in response.content
