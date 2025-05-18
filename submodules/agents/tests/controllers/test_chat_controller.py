from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from langchain.schema import AIMessage, HumanMessage
from src.controllers.chat_controller import ChatController
from src.models.service.chat_models import AgentResponse, ChatMessage, ChatRequest
from src.models.service.service_models import GenerateConversationTitleRequest


@pytest.fixture
def controller():
    return ChatController()


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
        "src.controllers.chat_controller.agent_manager_instance.parse_command",
        return_value=("nonexistent_agent", "test message"),
    ), patch("src.controllers.chat_controller.agent_manager_instance.get_agent", return_value=None), patch(
        "src.controllers.chat_controller.agent_manager_instance.set_active_agent"
    ):
        # Execute and verify
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_chat(chat_request)
        assert exc_info.value.status_code == 404


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_chat_invalid_response(controller, chat_request):
    # Setup - mock the delegation function to return invalid type
    mock_invalid_response = "invalid response type"

    with patch(
        "src.controllers.chat_controller.run_delegation", return_value=("test_agent", mock_invalid_response)
    ), patch("src.controllers.chat_controller.agent_manager_instance.parse_command", return_value=(None, None)), patch(
        "src.controllers.chat_controller.agent_manager_instance.clear_active_agent"
    ):
        # Execute and verify
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_chat(chat_request)
        assert exc_info.value.status_code == 500


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_chat_timeout(controller, chat_request):
    # Setup - mock the delegation function to raise timeout
    with patch("src.controllers.chat_controller.run_delegation", side_effect=TimeoutError()), patch(
        "src.controllers.chat_controller.agent_manager_instance.parse_command", return_value=(None, None)
    ), patch("src.controllers.chat_controller.agent_manager_instance.clear_active_agent"):
        # Execute and verify
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_chat(chat_request)
        # Timeout should be handled as generic 500 error
        assert exc_info.value.status_code == 500


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_chat_delegator_flow(controller, chat_request, agent_response):
    # Setup - test the delegator flow
    chat_request.use_research = False

    # Ensure the AgentResponse class is correctly mocked
    with patch(
        "src.controllers.chat_controller.agent_manager_instance.parse_command", return_value=(None, None)
    ), patch("src.controllers.chat_controller.agent_manager_instance.clear_active_agent"), patch(
        "src.controllers.chat_controller.run_delegation", return_value=("test_agent", agent_response)
    ) as mock_delegate, patch(
        "src.controllers.chat_controller.isinstance",
        return_value=True,  # Mock isinstance to always return True for our AgentResponse
    ):
        # Execute
        response = await controller.handle_chat(chat_request)

        # Verify
        assert response.status_code == 200
        mock_delegate.assert_called_once_with(chat_request)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_chat_orchestrator_flow(controller, chat_request, agent_response):
    # Setup - test the orchestrator flow
    chat_request.use_research = True

    with patch(
        "src.controllers.chat_controller.agent_manager_instance.parse_command", return_value=(None, None)
    ), patch("src.controllers.chat_controller.agent_manager_instance.clear_active_agent"), patch(
        "src.controllers.chat_controller.run_orchestration", return_value=("crew_agent", agent_response)
    ) as mock_orchestrate, patch(
        "src.controllers.chat_controller.isinstance",
        return_value=True,  # Mock isinstance to always return True for our AgentResponse
    ):
        # Execute
        response = await controller.handle_chat(chat_request)

        # Verify
        assert response.status_code == 200
        mock_orchestrate.assert_called_once_with(chat_request)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_conversation_title(controller):
    # Setup
    request = GenerateConversationTitleRequest(
        conversation_id="test-conv-id", messages_for_llm=[HumanMessage(content="Hello"), AIMessage(content="Hi there")]
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
        conversation_id="test-conv-id", messages_for_llm=[HumanMessage(content="Hello"), AIMessage(content="Hi there")]
    )

    mock_llm = Mock()
    mock_llm.invoke = Mock(side_effect=Exception("Test error"))

    with patch("src.controllers.chat_controller.LLM_DELEGATOR", mock_llm):
        # Execute and verify
        with pytest.raises(HTTPException) as exc_info:
            await controller.generate_conversation_title(request)
        assert exc_info.value.status_code == 500
