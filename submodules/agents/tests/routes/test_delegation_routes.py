from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from submodules.agents.src.routes.chat_routes import router

from src.models.service.chat_models import ChatMessage, ChatRequest
from src.models.service.service_models import GenerateConversationTitleRequest
from src.services.delegator.delegator import Delegator

app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture
def chat_request():
    return ChatRequest(
        conversation_id="test-conv-id",
        prompt=ChatMessage(role="user", content="test message"),
        chain_id="1",
        wallet_address="0x123",
    )


@pytest.fixture
def title_request():
    return GenerateConversationTitleRequest(conversation_id="test-conv-id", messages_for_llm=[])


@pytest.fixture
def mock_delegator():
    return Mock(spec=Delegator)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_chat_success(chat_request):
    response_content = {"content": "test response"}
    mock_response = JSONResponse(content=response_content)

    with patch("src.routes.delegation_routes.DelegationController") as mock_controller_class, patch(
        "src.routes.delegation_routes.logger"
    ) as mock_logger:
        mock_controller = mock_controller_class.return_value
        mock_controller.handle_chat = AsyncMock(return_value=mock_response)

        response = client.post("/api/v1/chat", json=chat_request.model_dump())

        assert response.status_code == 200
        assert response.json() == response_content

        mock_logger.info.assert_called_once_with(
            f"Received chat request for conversation {chat_request.conversation_id}"
        )
        mock_controller_class.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_chat_timeout(chat_request):
    with patch("src.routes.delegation_routes.Delegator"), patch(
        "src.routes.delegation_routes.DelegationController"
    ) as mock_controller_class, patch("src.routes.delegation_routes.logger") as mock_logger:
        mock_controller = mock_controller_class.return_value
        mock_controller.handle_chat = AsyncMock(side_effect=TimeoutError())

        response = client.post("/api/v1/chat", json=chat_request.model_dump())

        assert response.status_code == 504
        assert response.json()["detail"] == "Request timed out"
        mock_logger.error.assert_called_once_with("Chat request timed out")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_chat_value_error(chat_request):
    error_msg = "Invalid input"
    with patch("src.routes.delegation_routes.Delegator"), patch(
        "src.routes.delegation_routes.DelegationController"
    ) as mock_controller_class, patch("src.routes.delegation_routes.logger") as mock_logger:
        mock_controller = mock_controller_class.return_value
        mock_controller.handle_chat = AsyncMock(side_effect=ValueError(error_msg))

        response = client.post("/api/v1/chat", json=chat_request.model_dump())

        assert response.status_code == 400
        assert response.json()["detail"] == error_msg
        mock_logger.error.assert_called_once_with(f"Input formatting error: {error_msg}")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_chat_generic_error(chat_request):
    error_msg = "Something went wrong"
    with patch("src.routes.delegation_routes.Delegator"), patch(
        "src.routes.delegation_routes.DelegationController"
    ) as mock_controller_class, patch("src.routes.delegation_routes.logger") as mock_logger:
        mock_controller = mock_controller_class.return_value
        mock_controller.handle_chat = AsyncMock(side_effect=Exception(error_msg))

        response = client.post("/api/v1/chat", json=chat_request.model_dump())

        assert response.status_code == 500
        assert response.json()["detail"] == error_msg
        mock_logger.error.assert_called_once_with(f"Error in chat route: {error_msg}", exc_info=True)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_title_success(title_request):
    title = "Test Title"
    with patch("src.routes.delegation_routes.DelegationController") as mock_controller_class, patch(
        "src.routes.delegation_routes.logger"
    ) as mock_logger:
        mock_controller = mock_controller_class.return_value
        mock_controller.generate_conversation_title = AsyncMock(return_value=title)

        response = client.post("/api/v1/generate-title", json=title_request.model_dump())

        assert response.status_code == 200
        assert response.json()["title"] == title

        mock_logger.info.assert_called_once_with(
            f"Received title generation request for conversation {title_request.conversation_id}"
        )
        mock_controller_class.assert_called_once_with()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_title_timeout(title_request):
    with patch("src.routes.delegation_routes.DelegationController") as mock_controller_class, patch(
        "src.routes.delegation_routes.logger"
    ) as mock_logger:
        mock_controller = mock_controller_class.return_value
        mock_controller.generate_conversation_title = AsyncMock(side_effect=TimeoutError())

        response = client.post("/api/v1/generate-title", json=title_request.model_dump())

        assert response.status_code == 504
        assert response.json()["detail"] == "Request timed out"
        mock_logger.error.assert_called_once_with("Title generation request timed out")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_title_value_error(title_request):
    error_msg = "Invalid input"
    with patch("src.routes.delegation_routes.DelegationController") as mock_controller_class, patch(
        "src.routes.delegation_routes.logger"
    ) as mock_logger:
        mock_controller = mock_controller_class.return_value
        mock_controller.generate_conversation_title = AsyncMock(side_effect=ValueError(error_msg))

        response = client.post("/api/v1/generate-title", json=title_request.model_dump())

        assert response.status_code == 400
        assert response.json()["detail"] == error_msg
        mock_logger.error.assert_called_once_with(f"Input formatting error: {error_msg}")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_title_generic_error(title_request):
    error_msg = "Something went wrong"
    with patch("src.routes.delegation_routes.DelegationController") as mock_controller_class, patch(
        "src.routes.delegation_routes.logger"
    ) as mock_logger:
        mock_controller = mock_controller_class.return_value
        mock_controller.generate_conversation_title = AsyncMock(side_effect=Exception(error_msg))

        response = client.post("/api/v1/generate-title", json=title_request.model_dump())

        assert response.status_code == 500
        assert response.json()["detail"] == error_msg
        mock_logger.error.assert_called_once_with(f"Error in generate title route: {error_msg}", exc_info=True)
