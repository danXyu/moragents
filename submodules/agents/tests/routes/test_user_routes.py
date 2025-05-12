from unittest.mock import Mock, patch

import pytest
from agents.src.models.service.user_service_models import UserModel, UserSettingModel
from agents.src.routes.user_routes import router
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture
def mock_user_controller():
    with patch("agents.src.routes.user_routes.UserController") as mock:
        yield mock


@pytest.fixture
def sample_user():
    return UserModel(id=1, wallet_address="0x123")


@pytest.fixture
def sample_setting():
    return UserSettingModel(id=1, user_id=1, settings_key="test_key", settings_value={"test": "value"})


@pytest.mark.asyncio
async def test_get_user_success(mock_user_controller, sample_user):
    mock_controller = Mock()
    mock_controller.get_user.return_value = sample_user
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    with patch("agents.src.routes.user_routes.logger") as mock_logger:
        response = client.get("/api/v1/users/1")

        assert response.status_code == 200
        assert response.json() == sample_user.model_dump()
        mock_logger.info.assert_called_once_with("Received request to get user 1")


@pytest.mark.asyncio
async def test_get_user_not_found(mock_user_controller):
    mock_controller = Mock()
    mock_controller.get_user.return_value = None
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    with patch("agents.src.routes.user_routes.logger") as mock_logger:
        response = client.get("/api/v1/users/1")

        assert response.status_code == 404
        assert response.json()["detail"] == "User 1 not found"
        mock_logger.info.assert_called_once_with("Received request to get user 1")


@pytest.mark.asyncio
async def test_get_user_by_wallet_success(mock_user_controller, sample_user):
    mock_controller = Mock()
    mock_controller.get_user_by_wallet.return_value = sample_user
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    with patch("agents.src.routes.user_routes.logger") as mock_logger:
        response = client.get("/api/v1/users/wallet/0x123")

        assert response.status_code == 200
        assert response.json() == sample_user.model_dump()
        mock_logger.info.assert_called_once_with("Received request to get user by wallet 0x123")


@pytest.mark.asyncio
async def test_list_users_success(mock_user_controller, sample_user):
    mock_controller = Mock()
    mock_controller.list_users.return_value = [sample_user]
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    with patch("agents.src.routes.user_routes.logger") as mock_logger:
        response = client.get("/api/v1/users")

        assert response.status_code == 200
        assert response.json() == [sample_user.model_dump()]
        mock_logger.info.assert_called_once_with("Received request to list all users")


@pytest.mark.asyncio
async def test_create_user_success(mock_user_controller, sample_user):
    mock_controller = Mock()
    mock_controller.create_user.return_value = sample_user
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    with patch("agents.src.routes.user_routes.logger") as mock_logger:
        response = client.post("/api/v1/users", params={"wallet_address": "0x123"})

        assert response.status_code == 201
        assert response.json() == sample_user.model_dump()
        mock_logger.info.assert_called_once_with("Received request to create user with wallet 0x123")


@pytest.mark.asyncio
async def test_update_user_success(mock_user_controller, sample_user):
    mock_controller = Mock()
    mock_controller.update_user.return_value = sample_user
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    with patch("agents.src.routes.user_routes.logger") as mock_logger:
        response = client.put("/api/v1/users/1", params={"wallet_address": "0x123"})

        assert response.status_code == 200
        assert response.json() == sample_user.model_dump()
        mock_logger.info.assert_called_once_with("Received request to update user 1")


@pytest.mark.asyncio
async def test_delete_user_success(mock_user_controller):
    mock_controller = Mock()
    mock_controller.delete_user.return_value = True
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    with patch("agents.src.routes.user_routes.logger") as mock_logger:
        response = client.delete("/api/v1/users/1")

        assert response.status_code == 200
        assert response.json() == {"status": "success"}
        mock_logger.info.assert_called_once_with("Received request to delete user 1")


@pytest.mark.asyncio
async def test_get_user_setting_success(mock_user_controller, sample_setting):
    mock_controller = Mock()
    mock_controller.get_setting.return_value = sample_setting
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    with patch("agents.src.routes.user_routes.logger") as mock_logger:
        response = client.get("/api/v1/users/1/settings/test_key")

        assert response.status_code == 200
        assert response.json() == sample_setting.model_dump()
        mock_logger.info.assert_called_once_with("Received request to get setting test_key for user 1")


@pytest.mark.asyncio
async def test_list_user_settings_success(mock_user_controller, sample_setting):
    mock_controller = Mock()
    mock_controller.list_user_settings.return_value = [sample_setting]
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    with patch("agents.src.routes.user_routes.logger") as mock_logger:
        response = client.get("/api/v1/users/1/settings")

        assert response.status_code == 200
        assert response.json() == [sample_setting.model_dump()]
        mock_logger.info.assert_called_once_with("Received request to list settings for user 1")


@pytest.mark.asyncio
async def test_create_user_setting_success(mock_user_controller, sample_setting):
    mock_controller = Mock()
    mock_controller.create_setting.return_value = sample_setting
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    with patch("agents.src.routes.user_routes.logger") as mock_logger:
        response = client.post("/api/v1/users/1/settings/test_key", json={"test": "value"})

        assert response.status_code == 201
        assert response.json() == sample_setting.model_dump()
        mock_logger.info.assert_called_once_with("Received request to create setting test_key for user 1")


@pytest.mark.asyncio
async def test_update_user_setting_success(mock_user_controller, sample_setting):
    mock_controller = Mock()
    mock_controller.update_setting.return_value = sample_setting
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    with patch("agents.src.routes.user_routes.logger") as mock_logger:
        response = client.put("/api/v1/users/1/settings/test_key", json={"test": "value"})

        assert response.status_code == 200
        assert response.json() == sample_setting.model_dump()
        mock_logger.info.assert_called_once_with("Received request to update setting test_key for user 1")


@pytest.mark.asyncio
async def test_delete_user_setting_success(mock_user_controller):
    mock_controller = Mock()
    mock_controller.delete_setting.return_value = True
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    with patch("agents.src.routes.user_routes.logger") as mock_logger:
        response = client.delete("/api/v1/users/1/settings/test_key")

        assert response.status_code == 200
        assert response.json() == {"status": "success"}
        mock_logger.info.assert_called_once_with("Received request to delete setting test_key for user 1")


@pytest.mark.asyncio
async def test_error_handling(mock_user_controller):
    mock_controller = Mock()
    mock_controller.get_user.side_effect = Exception("Test error")
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    with patch("agents.src.routes.user_routes.logger") as mock_logger:
        response = client.get("/api/v1/users/1")

        assert response.status_code == 500
        assert response.json()["detail"] == "Test error"
        mock_logger.info.assert_called_once_with("Received request to get user 1")
        mock_logger.error.assert_called_once_with("Error getting user: Test error", exc_info=True)
