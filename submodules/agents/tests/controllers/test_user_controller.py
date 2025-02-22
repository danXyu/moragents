import pytest
from unittest.mock import Mock, patch
from models.service.user_models import UserModel, UserSettingModel
from models.daos.user_dao import UserDAO
from controllers.user_controller import UserController


@pytest.fixture
def mock_session():
    return Mock()


@pytest.fixture
def controller(mock_session):
    return UserController(session=mock_session)


@pytest.fixture
def mock_user_dao():
    return Mock(spec=UserDAO)


@pytest.fixture
def sample_user_dict():
    return {
        "id": 1,
        "wallet_address": "0x123",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }


@pytest.fixture
def sample_setting_dict():
    return {
        "id": 1,
        "user_id": 1,
        "settings_key": "test_key",
        "settings_value": {"test": "value"},
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }


def test_get_user_success(controller, mock_session, mock_user_dao, sample_user_dict):
    with patch("models.daos.user_dao.UserDAO", return_value=mock_user_dao):
        mock_user_dao.get_by_id.return_value = sample_user_dict

        result = controller.get_user(1)

        assert isinstance(result, UserModel)
        assert result.id == 1
        assert result.wallet_address == "0x123"
        mock_user_dao.get_by_id.assert_called_once_with(1)


def test_get_user_not_found(controller, mock_session, mock_user_dao):
    with patch("models.daos.user_dao.UserDAO", return_value=mock_user_dao):
        mock_user_dao.get_by_id.return_value = None

        result = controller.get_user(1)

        assert result is None
        mock_user_dao.get_by_id.assert_called_once_with(1)


def test_get_user_by_wallet(controller, mock_session, mock_user_dao, sample_user_dict):
    with patch("models.daos.user_dao.UserDAO", return_value=mock_user_dao):
        mock_user_dao.get_by_wallet_address.return_value = sample_user_dict

        result = controller.get_user_by_wallet("0x123")

        assert isinstance(result, UserModel)
        assert result.wallet_address == "0x123"
        mock_user_dao.get_by_wallet_address.assert_called_once_with("0x123")


def test_create_user(controller, mock_session, mock_user_dao, sample_user_dict):
    with patch("models.daos.user_dao.UserDAO", return_value=mock_user_dao):
        mock_user_dao.create.return_value = sample_user_dict

        result = controller.create_user("0x123")

        assert isinstance(result, UserModel)
        assert result.wallet_address == "0x123"
        mock_user_dao.create.assert_called_once_with("0x123")


def test_update_user(controller, mock_session, mock_user_dao, sample_user_dict):
    with patch("models.daos.user_dao.UserDAO", return_value=mock_user_dao):
        mock_user_dao.update.return_value = sample_user_dict

        result = controller.update_user(1, "0x123")

        assert isinstance(result, UserModel)
        assert result.wallet_address == "0x123"
        mock_user_dao.update.assert_called_once_with(1, "0x123")


def test_delete_user(controller, mock_session, mock_user_dao):
    with patch("models.daos.user_dao.UserDAO", return_value=mock_user_dao):
        mock_user_dao.delete.return_value = True

        result = controller.delete_user(1)

        assert result is True
        mock_user_dao.delete.assert_called_once_with(1)


def test_get_setting(controller, mock_session, mock_user_dao, sample_setting_dict):
    with patch("models.daos.user_dao.UserDAO", return_value=mock_user_dao):
        mock_user_dao.get_setting.return_value = sample_setting_dict

        result = controller.get_setting(1, "test_key")

        assert isinstance(result, UserSettingModel)
        assert result.settings_key == "test_key"
        assert result.settings_value == {"test": "value"}
        mock_user_dao.get_setting.assert_called_once_with(1, "test_key")


def test_create_setting(controller, mock_session, mock_user_dao, sample_setting_dict):
    with patch("models.daos.user_dao.UserDAO", return_value=mock_user_dao):
        mock_user_dao.create_setting.return_value = sample_setting_dict

        result = controller.create_setting(1, "test_key", {"test": "value"})

        assert isinstance(result, UserSettingModel)
        assert result.settings_key == "test_key"
        assert result.settings_value == {"test": "value"}
        mock_user_dao.create_setting.assert_called_once_with(1, "test_key", {"test": "value"})


def test_update_setting(controller, mock_session, mock_user_dao, sample_setting_dict):
    with patch("models.daos.user_dao.UserDAO", return_value=mock_user_dao):
        mock_user_dao.update_setting.return_value = sample_setting_dict

        result = controller.update_setting(1, "test_key", {"test": "value"})

        assert isinstance(result, UserSettingModel)
        assert result.settings_key == "test_key"
        assert result.settings_value == {"test": "value"}
        mock_user_dao.update_setting.assert_called_once_with(1, "test_key", {"test": "value"})


def test_delete_setting(controller, mock_session, mock_user_dao):
    with patch("models.daos.user_dao.UserDAO", return_value=mock_user_dao):
        mock_user_dao.delete_setting.return_value = True

        result = controller.delete_setting(1, "test_key")

        assert result is True
        mock_user_dao.delete_setting.assert_called_once_with(1, "test_key")


def test_context_manager(mock_session):
    with UserController(session=mock_session) as controller:
        assert controller._session == mock_session
    mock_session.close.assert_not_called()


def test_context_manager_auto_close():
    with patch("models.session.DBSessionFactory.get_instance") as mock_factory:
        mock_session = Mock()
        mock_factory.return_value.new_session.return_value = mock_session

        with UserController() as controller:
            assert controller._session == mock_session

        mock_session.close.assert_called_once()
