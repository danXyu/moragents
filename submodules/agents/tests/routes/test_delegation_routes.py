import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException
from models.service.chat_models import ChatRequest, AgentResponse, Prompt
from models.service.service_models import GenerateConversationTitleRequest
from routes.delegation_routes import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture
def chat_request():
    return ChatRequest(conversation_id="test-conv-id", prompt=Prompt(content="test message"))


@pytest.fixture
def title_request():
    return GenerateConversationTitleRequest(conversation_id="test-conv-id", messages_for_llm=[])


@pytest.fixture
def mock_controller():
    return Mock()


@pytest.mark.asyncio
async def test_chat_success(chat_request):
    agent_response = AgentResponse(content="test response", metadata={})

    with patch("routes.delegation_routes.DelegationController") as mock_controller_class:
        mock_controller = mock_controller_class.return_value
        mock_controller.handle_chat.return_value = JSONResponse(content={"content": "test response"})

        response = client.post("/api/v1/chat", json=chat_request.model_dump())

        assert response.status_code == 200
        assert "test response" in response.json()["content"]
        mock_controller.handle_chat.assert_called_once()


@pytest.mark.asyncio
async def test_chat_timeout(chat_request):
    with patch("routes.delegation_routes.DelegationController") as mock_controller_class:
        mock_controller = mock_controller_class.return_value
        mock_controller.handle_chat.side_effect = TimeoutError()

        response = client.post("/api/v1/chat", json=chat_request.model_dump())

        assert response.status_code == 504
        assert response.json()["detail"] == "Request timed out"


@pytest.mark.asyncio
async def test_chat_value_error(chat_request):
    with patch("routes.delegation_routes.DelegationController") as mock_controller_class:
        mock_controller = mock_controller_class.return_value
        mock_controller.handle_chat.side_effect = ValueError("Invalid input")

        response = client.post("/api/v1/chat", json=chat_request.model_dump())

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid input"


@pytest.mark.asyncio
async def test_chat_generic_error(chat_request):
    with patch("routes.delegation_routes.DelegationController") as mock_controller_class:
        mock_controller = mock_controller_class.return_value
        mock_controller.handle_chat.side_effect = Exception("Something went wrong")

        response = client.post("/api/v1/chat", json=chat_request.model_dump())

        assert response.status_code == 500
        assert response.json()["detail"] == "Something went wrong"


@pytest.mark.asyncio
async def test_generate_title_success(title_request):
    with patch("routes.delegation_routes.DelegationController") as mock_controller_class:
        mock_controller = mock_controller_class.return_value
        mock_controller.generate_conversation_title.return_value = "Test Title"

        response = client.post("/api/v1/generate-title", json=title_request.model_dump())

        assert response.status_code == 200
        assert response.json()["title"] == "Test Title"
        mock_controller.generate_conversation_title.assert_called_once()


@pytest.mark.asyncio
async def test_generate_title_timeout(title_request):
    with patch("routes.delegation_routes.DelegationController") as mock_controller_class:
        mock_controller = mock_controller_class.return_value
        mock_controller.generate_conversation_title.side_effect = TimeoutError()

        response = client.post("/api/v1/generate-title", json=title_request.model_dump())

        assert response.status_code == 504
        assert response.json()["detail"] == "Request timed out"


@pytest.mark.asyncio
async def test_generate_title_value_error(title_request):
    with patch("routes.delegation_routes.DelegationController") as mock_controller_class:
        mock_controller = mock_controller_class.return_value
        mock_controller.generate_conversation_title.side_effect = ValueError("Invalid input")

        response = client.post("/api/v1/generate-title", json=title_request.model_dump())

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid input"


@pytest.mark.asyncio
async def test_generate_title_generic_error(title_request):
    with patch("routes.delegation_routes.DelegationController") as mock_controller_class:
        mock_controller = mock_controller_class.return_value
        mock_controller.generate_conversation_title.side_effect = Exception("Something went wrong")

        response = client.post("/api/v1/generate-title", json=title_request.model_dump())

        assert response.status_code == 500
        assert response.json()["detail"] == "Something went wrong"
