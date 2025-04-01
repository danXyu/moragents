import logging
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest
from models.service.chat_models import AgentResponse, ChatRequest
from services.agents.token_swap.agent import TokenSwapAgent
from services.agents.token_swap.models import SwapQuoteResponse, TransactionResponse
from services.agents.token_swap.tools import (
    InsufficientFundsError,
    SwapNotPossibleError,
    TokenNotFoundError,
)
from services.agents.token_swap.utils.tool_types import SwapToolType

logger = logging.getLogger(__name__)


@pytest.fixture
def token_swap_agent(llm):
    config: Dict[str, Any] = {
        "name": "token_swap",
        "description": "Agent for handling token swaps",
        "APIBASEURL": "https://api.1inch.io/v5.0/",
    }
    return TokenSwapAgent(config, llm)


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_swap_success(token_swap_agent, make_chat_request):
    request = make_chat_request(
        content="Swap 1 ETH for USDT",
        agent_name="token_swap",
        chain_id="1",
        wallet_address="0x123",
    )

    mock_swap_result = SwapQuoteResponse(
        fromToken={"symbol": "ETH"},
        toToken={"symbol": "USDT"},
        toAmount="1000000000000000000",
        formatted_response="Successfully quoted swap of 1 ETH for USDT",
    )

    with patch("services.agents.token_swap.tools.swap_coins") as mock_swap:
        mock_swap.return_value = mock_swap_result

        response = await token_swap_agent._execute_tool(
            SwapToolType.SWAP_TOKENS.value,
            {"source_token": "ETH", "destination_token": "USDT", "amount": "1.0"},
        )

        assert isinstance(response, AgentResponse)
        assert response.response_type.value == "success"
        assert response.action_type == "swap"
        assert response.metadata == mock_swap_result.model_dump()


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_swap_insufficient_funds(token_swap_agent):
    with patch("services.agents.token_swap.tools.swap_coins") as mock_swap:
        mock_swap.side_effect = InsufficientFundsError("Insufficient funds")

        response = await token_swap_agent._execute_tool(
            SwapToolType.SWAP_TOKENS.value,
            {"source_token": "ETH", "destination_token": "USDT", "amount": "1000.0"},
        )

        assert isinstance(response, AgentResponse)
        assert response.response_type.value == "error"
        assert "Insufficient funds" in response.error_message


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_swap_token_not_found(token_swap_agent):
    with patch("services.agents.token_swap.tools.swap_coins") as mock_swap:
        mock_swap.side_effect = TokenNotFoundError("Token not found")

        response = await token_swap_agent._execute_tool(
            SwapToolType.SWAP_TOKENS.value,
            {"source_token": "INVALID", "destination_token": "USDT", "amount": "1.0"},
        )

        assert isinstance(response, AgentResponse)
        assert response.response_type.value == "error"
        assert "Token not found" in response.error_message


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_get_transaction_status(token_swap_agent):
    mock_tx_response = TransactionResponse(
        status="success",
        tx_hash="0x123",
        tx_type="swap",
        formatted_response="Transaction 0x123 was successful",
    )

    with patch("services.agents.token_swap.tools.get_transaction_status") as mock_status:
        mock_status.return_value = mock_tx_response

        response = await token_swap_agent._execute_tool(
            SwapToolType.GET_TRANSACTION_STATUS.value,
            {"tx_hash": "0x123", "chain_id": "1", "wallet_address": "0xwallet"},
        )

        assert isinstance(response, AgentResponse)
        assert response.response_type.value == "success"
        assert response.action_type == "transaction_status"
        assert response.metadata == mock_tx_response.model_dump()


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_missing_parameters(token_swap_agent):
    response = await token_swap_agent._execute_tool(
        SwapToolType.SWAP_TOKENS.value,
        {"source_token": "ETH"},  # Missing destination_token and amount
    )

    assert isinstance(response, AgentResponse)
    assert response.response_type.value == "needs_info"
    assert "Please provide the following information" in response.content


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_unknown_tool(token_swap_agent):
    response = await token_swap_agent._execute_tool("unknown_tool", {})

    assert isinstance(response, AgentResponse)
    assert response.response_type.value == "error"
    assert "Unknown tool" in response.error_message
