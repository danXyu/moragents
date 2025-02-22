import pytest
from unittest.mock import patch, Mock
from fastapi import HTTPException
from fastapi.testclient import TestClient
from models.service.user_models import UserModel, UserSettingModel

from routes.user_routes import router

client = TestClient(router)


@pytest.fixture
def mock_user_controller():
    with patch("routes.user_routes.UserController") as mock:
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

    response = client.get("/api/v1/users/1")

    assert response.status_code == 200
    assert response.json() == sample_user.model_dump()


@pytest.mark.asyncio
async def test_get_user_not_found(mock_user_controller):
    mock_controller = Mock()
    mock_controller.get_user.return_value = None
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    response = client.get("/api/v1/users/1")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_user_by_wallet_success(mock_user_controller, sample_user):
    mock_controller = Mock()
    mock_controller.get_user_by_wallet.return_value = sample_user
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    response = client.get("/api/v1/users/wallet/0x123")

    assert response.status_code == 200
    assert response.json() == sample_user.model_dump()


@pytest.mark.asyncio
async def test_list_users_success(mock_user_controller, sample_user):
    mock_controller = Mock()
    mock_controller.list_users.return_value = [sample_user]
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    response = client.get("/api/v1/users")

    assert response.status_code == 200
    assert response.json() == [sample_user.model_dump()]


@pytest.mark.asyncio
async def test_create_user_success(mock_user_controller, sample_user):
    mock_controller = Mock()
    mock_controller.create_user.return_value = sample_user
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    response = client.post("/api/v1/users?wallet_address=0x123")

    assert response.status_code == 201
    assert response.json() == sample_user.model_dump()


@pytest.mark.asyncio
async def test_update_user_success(mock_user_controller, sample_user):
    mock_controller = Mock()
    mock_controller.update_user.return_value = sample_user
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    response = client.put("/api/v1/users/1?wallet_address=0x123")

    assert response.status_code == 200
    assert response.json() == sample_user.model_dump()


@pytest.mark.asyncio
async def test_delete_user_success(mock_user_controller):
    mock_controller = Mock()
    mock_controller.delete_user.return_value = True
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    response = client.delete("/api/v1/users/1")

    assert response.status_code == 200
    assert response.json() == {"status": "success"}


@pytest.mark.asyncio
async def test_get_user_setting_success(mock_user_controller, sample_setting):
    mock_controller = Mock()
    mock_controller.get_setting.return_value = sample_setting
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    response = client.get("/api/v1/users/1/settings/test_key")

    assert response.status_code == 200
    assert response.json() == sample_setting.model_dump()


@pytest.mark.asyncio
async def test_list_user_settings_success(mock_user_controller, sample_setting):
    mock_controller = Mock()
    mock_controller.list_user_settings.return_value = [sample_setting]
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    response = client.get("/api/v1/users/1/settings")

    assert response.status_code == 200
    assert response.json() == [sample_setting.model_dump()]


@pytest.mark.asyncio
async def test_create_user_setting_success(mock_user_controller, sample_setting):
    mock_controller = Mock()
    mock_controller.create_setting.return_value = sample_setting
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    response = client.post("/api/v1/users/1/settings/test_key", json={"test": "value"})

    assert response.status_code == 201
    assert response.json() == sample_setting.model_dump()


@pytest.mark.asyncio
async def test_update_user_setting_success(mock_user_controller, sample_setting):
    mock_controller = Mock()
    mock_controller.update_setting.return_value = sample_setting
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    response = client.put("/api/v1/users/1/settings/test_key", json={"test": "value"})

    assert response.status_code == 200
    assert response.json() == sample_setting.model_dump()


@pytest.mark.asyncio
async def test_delete_user_setting_success(mock_user_controller):
    mock_controller = Mock()
    mock_controller.delete_setting.return_value = True
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    response = client.delete("/api/v1/users/1/settings/test_key")

    assert response.status_code == 200
    assert response.json() == {"status": "success"}


@pytest.mark.asyncio
async def test_error_handling(mock_user_controller):
    mock_controller = Mock()
    mock_controller.get_user.side_effect = Exception("Test error")
    mock_user_controller.return_value.__enter__.return_value = mock_controller

    response = client.get("/api/v1/users/1")

    assert response.status_code == 500
    assert "Test error" in response.json()["detail"]
