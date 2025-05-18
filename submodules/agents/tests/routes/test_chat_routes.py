import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from src.models.service.chat_models import ChatMessage, ChatRequest
from src.models.service.service_models import GenerateConversationTitleRequest
from src.routes.chat_routes import router

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
        use_research=False,
        request_id=None,
    )


@pytest.fixture
def streaming_chat_request():
    return ChatRequest(
        conversation_id="test-conv-id",
        prompt=ChatMessage(role="user", content="test message"),
        chain_id="1",
        wallet_address="0x123",
        use_research=True,
        request_id=None,
    )


@pytest.fixture
def title_request():
    return GenerateConversationTitleRequest(conversation_id="test-conv-id", messages_for_llm=[])


@pytest.mark.unit
def test_chat_success(chat_request):
    response_content = {"content": "test response"}
    mock_response = JSONResponse(content=response_content)

    with patch("src.routes.chat_routes.ChatController") as mock_controller_class, patch(
        "src.routes.chat_routes.logger"
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
def test_chat_http_exception(chat_request):
    error_msg = "Not found"

    with patch("src.routes.chat_routes.ChatController") as mock_controller_class:
        mock_controller = mock_controller_class.return_value
        mock_controller.handle_chat = AsyncMock(side_effect=HTTPException(status_code=404, detail=error_msg))

        response = client.post("/api/v1/chat", json=chat_request.model_dump())

        assert response.status_code == 404
        assert response.json()["detail"] == error_msg


@pytest.mark.unit
def test_chat_timeout(chat_request):
    with patch("src.routes.chat_routes.ChatController") as mock_controller_class, patch(
        "src.routes.chat_routes.logger"
    ) as mock_logger:
        mock_controller = mock_controller_class.return_value
        mock_controller.handle_chat = AsyncMock(side_effect=TimeoutError())

        response = client.post("/api/v1/chat", json=chat_request.model_dump())

        assert response.status_code == 504
        assert response.json()["detail"] == "Request timed out"
        mock_logger.error.assert_called_once_with("Chat request timed out")


@pytest.mark.unit
def test_chat_value_error(chat_request):
    error_msg = "Invalid input"
    with patch("src.routes.chat_routes.ChatController") as mock_controller_class, patch(
        "src.routes.chat_routes.logger"
    ) as mock_logger:
        mock_controller = mock_controller_class.return_value
        mock_controller.handle_chat = AsyncMock(side_effect=ValueError(error_msg))

        response = client.post("/api/v1/chat", json=chat_request.model_dump())

        assert response.status_code == 400
        assert response.json()["detail"] == error_msg
        mock_logger.error.assert_called_once_with(f"Input formatting error: {error_msg}")


@pytest.mark.unit
def test_chat_generic_error(chat_request):
    error_msg = "Something went wrong"
    with patch("src.routes.chat_routes.ChatController") as mock_controller_class, patch(
        "src.routes.chat_routes.logger"
    ) as mock_logger:
        mock_controller = mock_controller_class.return_value
        mock_controller.handle_chat = AsyncMock(side_effect=Exception(error_msg))

        response = client.post("/api/v1/chat", json=chat_request.model_dump())

        assert response.status_code == 500
        assert response.json()["detail"] == error_msg
        mock_logger.error.assert_called_once_with(f"Error in chat route: {error_msg}", exc_info=True)


@pytest.mark.unit
def test_chat_stream_non_research_mode(chat_request):
    response = client.post("/api/v1/chat/stream", json=chat_request.model_dump())
    assert response.status_code == 400
    assert response.json()["detail"] == "Streaming is only supported for research mode"


@pytest.mark.unit
def test_chat_stream_success(streaming_chat_request):
    # Mock the EventSourceResponse to avoid SSE streaming issues
    mock_event_response = MagicMock()
    mock_event_response.headers = {"content-type": "text/event-stream"}

    with patch("src.routes.chat_routes.ChatController") as mock_controller_class, patch(
        "src.routes.chat_routes.uuid.uuid4"
    ) as mock_uuid, patch("src.routes.chat_routes.logger") as mock_logger, patch(
        "src.routes.chat_routes.EventSourceResponse", return_value=mock_event_response
    ) as mock_sse, patch(
        "src.routes.chat_routes.asyncio.create_task"
    ) as mock_create_task:
        mock_uuid.return_value = "test-uuid"
        mock_controller = mock_controller_class.return_value
        mock_controller.handle_chat = AsyncMock()

        client.post("/api/v1/chat/stream", json=streaming_chat_request.model_dump())

        # Since we're mocking EventSourceResponse, check that it was called
        mock_sse.assert_called_once()
        mock_create_task.assert_called_once()

        mock_logger.info.assert_called_with(
            f"Received streaming chat request for conversation {streaming_chat_request.conversation_id}"
        )
        mock_controller_class.assert_called_once()


@pytest.mark.unit
def test_get_stream():
    request_id = str(uuid.uuid4())
    mock_event_response = MagicMock()
    mock_event_response.headers = {"content-type": "text/event-stream"}

    with patch("src.routes.chat_routes.EventSourceResponse", return_value=mock_event_response) as mock_sse:
        client.get(f"/api/v1/chat/stream/{request_id}")
        mock_sse.assert_called_once()


@pytest.mark.unit
def test_generate_title_success(title_request):
    title = "Test Title"
    with patch("src.routes.chat_routes.ChatController") as mock_controller_class, patch(
        "src.routes.chat_routes.logger"
    ) as mock_logger:
        mock_controller = mock_controller_class.return_value
        mock_controller.generate_conversation_title = AsyncMock(return_value=title)

        response = client.post("/api/v1/generate-title", json=title_request.model_dump())

        assert response.status_code == 200
        assert response.json()["title"] == title

        mock_logger.info.assert_called_once_with(
            f"Received title generation request for conversation {title_request.conversation_id}"
        )
        mock_controller_class.assert_called_once()


@pytest.mark.unit
def test_generate_title_http_exception(title_request):
    error_msg = "Not found"

    with patch("src.routes.chat_routes.ChatController") as mock_controller_class:
        mock_controller = mock_controller_class.return_value
        mock_controller.generate_conversation_title = AsyncMock(
            side_effect=HTTPException(status_code=404, detail=error_msg)
        )

        response = client.post("/api/v1/generate-title", json=title_request.model_dump())

        assert response.status_code == 404
        assert response.json()["detail"] == error_msg


@pytest.mark.unit
def test_generate_title_timeout(title_request):
    with patch("src.routes.chat_routes.ChatController") as mock_controller_class, patch(
        "src.routes.chat_routes.logger"
    ) as mock_logger:
        mock_controller = mock_controller_class.return_value
        mock_controller.generate_conversation_title = AsyncMock(side_effect=TimeoutError())

        response = client.post("/api/v1/generate-title", json=title_request.model_dump())

        assert response.status_code == 504
        assert response.json()["detail"] == "Request timed out"
        mock_logger.error.assert_called_once_with("Title generation request timed out")


@pytest.mark.unit
def test_generate_title_value_error(title_request):
    error_msg = "Invalid input"
    with patch("src.routes.chat_routes.ChatController") as mock_controller_class, patch(
        "src.routes.chat_routes.logger"
    ) as mock_logger:
        mock_controller = mock_controller_class.return_value
        mock_controller.generate_conversation_title = AsyncMock(side_effect=ValueError(error_msg))

        response = client.post("/api/v1/generate-title", json=title_request.model_dump())

        assert response.status_code == 400
        assert response.json()["detail"] == error_msg
        mock_logger.error.assert_called_once_with(f"Input formatting error: {error_msg}")


@pytest.mark.unit
def test_generate_title_generic_error(title_request):
    error_msg = "Something went wrong"
    with patch("src.routes.chat_routes.ChatController") as mock_controller_class, patch(
        "src.routes.chat_routes.logger"
    ) as mock_logger:
        mock_controller = mock_controller_class.return_value
        mock_controller.generate_conversation_title = AsyncMock(side_effect=Exception(error_msg))

        response = client.post("/api/v1/generate-title", json=title_request.model_dump())

        assert response.status_code == 500
        assert response.json()["detail"] == error_msg
        mock_logger.error.assert_called_once_with(f"Error in generate title route: {error_msg}", exc_info=True)
