from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.models.service.chat_models import AgentResponse, ChatMessage, ChatRequest, ResponseType
from src.services.delegator.delegator import Delegator


@pytest.fixture
def mock_llm():
    return Mock()


@pytest.fixture
def delegator(mock_llm):
    with patch("src.services.delegator.delegator.LLM_DELEGATOR", mock_llm):
        return Delegator(mock_llm)


@pytest.fixture
def sample_chat_request():
    return ChatRequest(
        conversation_id="test_conv",
        prompt=ChatMessage(role="user", content="What's the weather?", agentName="base"),
        chain_id="1",
        wallet_address="0x123",
        chat_history=[
            ChatMessage(role="user", content="Hello", agentName="base"),
            ChatMessage(role="assistant", content="Hi there", agentName="base"),
        ],
    )


@pytest.mark.unit
def test_build_system_prompt(delegator):
    available_agents = [
        {"name": "weather", "delegator_description": "Gets weather info"},
        {"name": "math", "delegator_description": "Does calculations"},
    ]

    with patch("src.services.delegator.delegator.get_system_prompt") as mock_get_prompt:
        mock_get_prompt.return_value = "You are Morpheus\n- weather: Gets weather info\n- math: Does calculations"
        prompt = mock_get_prompt(available_agents)

        assert "weather: Gets weather info" in prompt
        assert "math: Does calculations" in prompt
        assert "You are Morpheus" in prompt


@pytest.mark.unit
@patch("src.services.delegator.delegator.agent_manager_instance.get_available_agents")
def test_get_delegator_response_no_agents(mock_get_agents, delegator, sample_chat_request):
    mock_get_agents.return_value = []

    result = delegator.get_delegator_response(sample_chat_request)

    assert result == ["default"]
    assert "default" not in delegator.attempted_agents


@pytest.mark.unit
@patch("src.services.delegator.delegator.agent_manager_instance.get_available_agents")
def test_get_delegator_response_valid_json(mock_get_agents, delegator, sample_chat_request, mock_llm):
    mock_get_agents.return_value = [{"name": "agent1", "delegator_description": "test"}]
    mock_llm.return_value = Mock(content='{"agents": ["agent1", "agent2"]}')

    result = delegator.get_delegator_response(sample_chat_request)

    assert result == ["agent1", "agent2"]
    assert delegator.selected_agents_for_request == ["agent1", "agent2"]


@pytest.mark.unit
@patch("src.services.delegator.delegator.agent_manager_instance.get_available_agents")
def test_get_delegator_response_fallback_parser(mock_get_agents, delegator, sample_chat_request, mock_llm):
    mock_get_agents.return_value = [{"name": "agent1", "delegator_description": "test"}]
    mock_llm.return_value = Mock(content='{"agents": ["agent1"]}')

    result = delegator.get_delegator_response(sample_chat_request)

    assert result == ["agent1"]


@pytest.mark.unit
@pytest.mark.asyncio
@patch("src.services.delegator.delegator.load_agent_config")
async def test_try_agent_success(mock_load_config, delegator, sample_chat_request):
    mock_load_config.return_value = {"path": "test.path", "class_name": "TestAgent"}

    mock_module = Mock()
    mock_agent_class = Mock()
    mock_agent = Mock()
    mock_agent.chat = AsyncMock(return_value=AgentResponse.success(content="Success"))
    mock_agent_class.return_value = mock_agent
    mock_module.TestAgent = mock_agent_class

    with patch.dict("sys.modules", {"test.path": mock_module}):
        result = await delegator._try_agent("test_agent", sample_chat_request)

    assert result is not None
    assert result.content == "Success"
    assert result.response_type == ResponseType.SUCCESS


@pytest.mark.unit
@pytest.mark.asyncio
@patch("src.services.delegator.delegator.load_agent_config")
async def test_try_agent_error_response(mock_load_config, delegator, sample_chat_request):
    mock_load_config.return_value = {"path": "test.path", "class_name": "TestAgent"}

    mock_module = Mock()
    mock_agent_class = Mock()
    mock_agent = Mock()
    error_response = AgentResponse.error(error_message="Error occurred")
    mock_agent.chat = AsyncMock(return_value=error_response)
    mock_agent_class.return_value = mock_agent
    mock_module.TestAgent = mock_agent_class

    with patch.dict("sys.modules", {"test.path": mock_module}):
        result = await delegator._try_agent("test_agent", sample_chat_request)

    assert result is not None
    assert result.response_type == ResponseType.ERROR
    assert result.error_message == "Error occurred"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delegate_chat_success(delegator, sample_chat_request):
    with patch.object(delegator, "get_delegator_response") as mock_get_response:
        mock_get_response.return_value = ["agent1"]
        with patch.object(delegator, "_try_agent") as mock_try:
            mock_try.return_value = AgentResponse.success(content="Success")

            agent_name, response = await delegator.delegate_chat(sample_chat_request)

    assert agent_name == "agent1"
    assert response.content == "Success"
    assert "agent1" in delegator.attempted_agents


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delegate_chat_all_agents_fail(delegator, sample_chat_request):
    with patch.object(delegator, "get_delegator_response") as mock_get_response:
        mock_get_response.return_value = ["agent1", "agent2"]
        with patch.object(delegator, "_try_agent") as mock_try:
            mock_try.return_value = None

            agent_name, response = await delegator.delegate_chat(sample_chat_request)

    assert agent_name is None
    assert response.error_message == "All agents have been attempted without success"
    assert "agent1" in delegator.attempted_agents
    assert "agent2" in delegator.attempted_agents
