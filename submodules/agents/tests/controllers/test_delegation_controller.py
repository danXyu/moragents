import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from models.service.chat_models import ChatRequest, AgentResponse, ChatMessage, Prompt
from models.service.service_models import GenerateConversationTitleRequest
from services.delegator.delegator import Delegator
from agents.tests.controllers.test_delegation_controller import DelegationController
from langchain.schema import AIMessage, HumanMessage


@pytest.fixture
def mock_delegator():
    return Mock(spec=Delegator)


@pytest.fixture
def controller(mock_delegator):
    return DelegationController(delegator=mock_delegator)


@pytest.fixture
def chat_request():
    return ChatRequest(conversation_id="test-conv-id", prompt=Prompt(content="test message"))


@pytest.fixture
def agent_response():
    return AgentResponse(content="test response", metadata={})


@pytest.mark.asyncio
async def test_handle_chat_delegator_flow(controller, chat_request, agent_response, mock_delegator):
    # Setup
    mock_delegator.delegate_chat.return_value = ("test_agent", agent_response)

    # Execute
    response = await controller.handle_chat(chat_request)

    # Verify
    assert response.status_code == 200
    response_data = response.body.decode()
    assert "test response" in response_data
    mock_delegator.delegate_chat.assert_called_once_with(chat_request)


@pytest.mark.asyncio
async def test_handle_chat_command_flow(controller, chat_request, agent_response):
    # Setup
    chat_request.prompt.content = "/test_agent test message"
    mock_agent = Mock()
    mock_agent.chat.return_value = agent_response

    with patch("stores.agent_manager_instance.parse_command", return_value=("test_agent", "test message")), patch(
        "stores.agent_manager_instance.get_agent", return_value=mock_agent
    ):

        # Execute
        response = await controller.handle_chat(chat_request)

        # Verify
        assert response.status_code == 200
        response_data = response.body.decode()
        assert "test response" in response_data
        mock_agent.chat.assert_called_once()


@pytest.mark.asyncio
async def test_handle_chat_agent_not_found(controller, chat_request):
    # Setup
    chat_request.prompt.content = "/nonexistent_agent test message"

    with patch(
        "stores.agent_manager_instance.parse_command", return_value=("nonexistent_agent", "test message")
    ), patch("stores.agent_manager_instance.get_agent", return_value=None):

        # Execute and verify
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_chat(chat_request)
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_handle_chat_invalid_response(controller, chat_request, mock_delegator):
    # Setup
    mock_delegator.delegate_chat.return_value = ("test_agent", "invalid response type")

    # Execute and verify
    with pytest.raises(HTTPException) as exc_info:
        await controller.handle_chat(chat_request)
    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_handle_chat_timeout(controller, chat_request, mock_delegator):
    # Setup
    mock_delegator.delegate_chat.side_effect = TimeoutError()

    # Execute and verify
    with pytest.raises(HTTPException) as exc_info:
        await controller.handle_chat(chat_request)
    assert exc_info.value.status_code == 504


@pytest.mark.asyncio
async def test_generate_conversation_title(controller):
    # Setup
    request = GenerateConversationTitleRequest(
        messages_for_llm=[HumanMessage(content="Hello"), AIMessage(content="Hi there")]
    )

    with patch("config.LLM_DELEGATOR.invoke") as mock_invoke:
        mock_invoke.return_value.content = "Test Conversation Title"

        # Execute
        title = await controller.generate_conversation_title(request)

        # Verify
        assert title == "Test Conversation Title"
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
async def test_generate_conversation_title_failure(controller):
    # Setup
    request = GenerateConversationTitleRequest(
        messages_for_llm=[HumanMessage(content="Hello"), AIMessage(content="Hi there")]
    )

    with patch("config.LLM_DELEGATOR.invoke", side_effect=Exception("Test error")):
        # Execute and verify
        with pytest.raises(HTTPException) as exc_info:
            await controller.generate_conversation_title(request)
        assert exc_info.value.status_code == 500
