from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from langchain.schema import AIMessage, HumanMessage
from src.controllers.chat_controller import ChatController
from src.models.service.chat_models import AgentResponse, ChatMessage, ChatRequest
from src.models.service.service_models import GenerateConversationTitleRequest
from src.services.delegator.delegator import Delegator


@pytest.fixture
def mock_delegator():
    return Mock(spec=Delegator)


@pytest.fixture
def controller(mock_delegator):
    return ChatController(delegator=mock_delegator)


@pytest.fixture
def chat_request():
    return ChatRequest(
        conversation_id="test-conv-id",
        prompt=ChatMessage(role="user", content="test message"),
        chain_id="1",
        wallet_address="0x123",
    )


@pytest.fixture
def agent_response():
    return AgentResponse.success(content="test response")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_chat_agent_not_found(controller, chat_request):
    # Setup
    chat_request.prompt.content = "/nonexistent_agent test message"

    with patch(
        "src.stores.agent_manager.agent_manager_instance.parse_command",
        return_value=("nonexistent_agent", "test message"),
    ), patch("src.stores.agent_manager.agent_manager_instance.get_agent", return_value=None), patch(
        "src.stores.agent_manager.agent_manager_instance.set_active_agent"
    ):
        # Execute and verify
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_chat(chat_request)
        assert exc_info.value.status_code == 400


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_chat_invalid_response(controller, chat_request, mock_delegator):
    # Setup
    mock_delegator.delegate_chat = AsyncMock(return_value=("test_agent", "invalid response type"))

    with patch("src.stores.agent_manager.agent_manager_instance.parse_command", return_value=(None, None)), patch(
        "src.stores.agent_manager.agent_manager_instance.clear_active_agent"
    ):
        # Execute and verify
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_chat(chat_request)
        assert exc_info.value.status_code == 500


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_chat_timeout(controller, chat_request, mock_delegator):
    # Setup
    mock_delegator.delegate_chat = AsyncMock(side_effect=TimeoutError())

    with patch("src.stores.agent_manager.agent_manager_instance.parse_command", return_value=(None, None)), patch(
        "src.stores.agent_manager.agent_manager_instance.clear_active_agent"
    ):
        # Execute and verify
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_chat(chat_request)
        assert exc_info.value.status_code == 504


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_conversation_title(controller):
    # Setup
    request = GenerateConversationTitleRequest(
        messages_for_llm=[HumanMessage(content="Hello"), AIMessage(content="Hi there")]
    )

    mock_llm = Mock()
    mock_llm.invoke = Mock(return_value=AIMessage(content="Test Conversation Title"))

    with patch("src.controllers.chat_controller.LLM_DELEGATOR", mock_llm):
        # Execute
        title = await controller.generate_conversation_title(request)

        # Verify
        assert title == "Test Conversation Title"
        mock_llm.invoke.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_conversation_title_failure(controller):
    # Setup
    request = GenerateConversationTitleRequest(
        messages_for_llm=[HumanMessage(content="Hello"), AIMessage(content="Hi there")]
    )

    mock_llm = Mock()
    mock_llm.invoke = Mock(side_effect=Exception("Test error"))

    with patch("src.controllers.chat_controller.LLM_DELEGATOR", mock_llm):
        # Execute and verify
        with pytest.raises(HTTPException) as exc_info:
            await controller.generate_conversation_title(request)
        assert exc_info.value.status_code == 500