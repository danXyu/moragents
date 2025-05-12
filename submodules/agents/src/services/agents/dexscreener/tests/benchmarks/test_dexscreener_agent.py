import logging
from typing import Any, Dict
from unittest.mock import patch

import pytest

from models.service.chat_models import AgentResponse
from services.agents.dexscreener.agent import DexScreenerAgent
from services.agents.dexscreener.models import BoostedTokenResponse, DexPairSearchResponse, TokenProfileResponse
from services.agents.dexscreener.tool_types import DexScreenerToolType

logger = logging.getLogger(__name__)


@pytest.fixture
def dex_agent(llm):
    config: Dict[str, Any] = {
        "name": "dexscreener",
        "description": "Agent for DexScreener API interactions",
    }
    return DexScreenerAgent(config, llm)


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_search_dex_pairs_success(dex_agent, make_chat_request):
    mock_response = DexPairSearchResponse(
        pairs=[
            {
                "baseToken": {"symbol": "ETH"},
                "quoteToken": {"symbol": "USDC"},
                "dexId": "uniswap",
                "chainId": "ethereum",
                "priceUsd": "1850.45",
                "priceChange": {"h24": 2.5},
                "volume": {"h24": 1000000},
                "liquidity": {"usd": 5000000},
                "txns": {"h24": {"buys": 100, "sells": 50}},
                "url": "https://dexscreener.com/eth/pair",
            }
        ],
        formatted_response="Found ETH/USDC pair on Uniswap",
    )

    with patch("services.agents.dexscreener.tools.search_dex_pairs") as mock_search:
        mock_search.return_value = mock_response

        response = await dex_agent._execute_tool(DexScreenerToolType.SEARCH_DEX_PAIRS.value, {"query": "ETH/USDC"})

        assert isinstance(response, AgentResponse)
        assert response.response_type.value == "success"
        assert response.action_type == DexScreenerToolType.SEARCH_DEX_PAIRS.value
        assert response.metadata == mock_response.model_dump()


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_get_latest_token_profiles(dex_agent, make_chat_request):
    mock_response = TokenProfileResponse(
        tokens=[
            {
                "tokenAddress": "0x123",
                "description": "Test Token",
                "icon": "https://icon.url",
                "url": "https://dexscreener.com/token",
                "links": [{"type": "website", "url": "https://test.com"}],
            }
        ],
        formatted_response="Latest token profiles",
    )

    with patch("services.agents.dexscreener.tools.get_latest_token_profiles") as mock_profiles:
        mock_profiles.return_value = mock_response

        response = await dex_agent._execute_tool(
            DexScreenerToolType.GET_LATEST_TOKEN_PROFILES.value,
            {"chain_id": "ethereum"},
        )

        assert isinstance(response, AgentResponse)
        assert response.response_type.value == "success"
        assert response.action_type == DexScreenerToolType.GET_LATEST_TOKEN_PROFILES.value
        assert response.metadata == mock_response.model_dump()


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_get_boosted_tokens(dex_agent, make_chat_request):
    mock_response = BoostedTokenResponse(
        tokens=[
            {
                "tokenAddress": "0x456",
                "description": "Boosted Token",
                "url": "https://dexscreener.com/boosted",
                "links": [],
            }
        ],
        formatted_response="Latest boosted tokens",
    )

    with patch("services.agents.dexscreener.tools.get_latest_boosted_tokens") as mock_boosted:
        mock_boosted.return_value = mock_response

        response = await dex_agent._execute_tool(
            DexScreenerToolType.GET_LATEST_BOOSTED_TOKENS.value,
            {"chain_id": "ethereum"},
        )

        assert isinstance(response, AgentResponse)
        assert response.response_type.value == "success"
        assert response.action_type == DexScreenerToolType.GET_LATEST_BOOSTED_TOKENS.value
        assert response.metadata == mock_response.model_dump()


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_error_handling(dex_agent, make_chat_request):
    with patch("services.agents.dexscreener.tools.search_dex_pairs") as mock_search:
        mock_search.side_effect = Exception("API Error")

        response = await dex_agent._execute_tool(DexScreenerToolType.SEARCH_DEX_PAIRS.value, {"query": "invalid"})

        assert isinstance(response, AgentResponse)
        assert response.response_type.value == "error"
        assert "API Error" in response.error_message


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_unknown_tool(dex_agent, make_chat_request):
    response = await dex_agent._execute_tool("unknown_tool", {})

    assert isinstance(response, AgentResponse)
    assert response.response_type.value == "error"
    assert "Unknown tool" in response.error_message
