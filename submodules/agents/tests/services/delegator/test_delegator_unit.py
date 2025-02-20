import pytest
from unittest.mock import Mock, patch, AsyncMock
from services.delegator.delegator import Delegator, RankAgentsOutput
from models.service.chat_models import ChatRequest, AgentResponse, ResponseType
from langchain.schema import AIMessage, HumanMessage


@pytest.fixture
def mock_llm():
    return Mock()


@pytest.fixture
def mock_embeddings():
    return Mock()


@pytest.fixture
def delegator(mock_llm, mock_embeddings):
    return Delegator(mock_llm, mock_embeddings)


@pytest.fixture
def sample_chat_request():
    return ChatRequest(
        messages=[
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there"),
            HumanMessage(content="What's the weather?"),
        ]
    )


@pytest.mark.unit
def test_build_system_prompt(delegator):
    available_agents = [
        {"name": "weather", "description": "Gets weather info"},
        {"name": "math", "description": "Does calculations"},
    ]

    prompt = delegator._build_system_prompt(available_agents)

    assert "weather: Gets weather info" in prompt
    assert "math: Does calculations" in prompt
    assert "You are Morpheus" in prompt


@pytest.mark.unit
@patch("src.stores.agent_manager_instance.get_available_agents")
def test_get_delegator_response_no_agents(mock_get_agents, delegator, sample_chat_request):
    mock_get_agents.return_value = []

    result = delegator.get_delegator_response(sample_chat_request)

    assert result == ["default"]
    assert "default" not in delegator.attempted_agents


@pytest.mark.unit
@patch("src.stores.agent_manager_instance.get_available_agents")
def test_get_delegator_response_valid_json(mock_get_agents, delegator, sample_chat_request, mock_llm):
    mock_get_agents.return_value = [{"name": "agent1", "description": "test"}]
    mock_llm.return_value = Mock(content='{"agents": ["agent1", "agent2"]}')

    result = delegator.get_delegator_response(sample_chat_request)

    assert result == ["agent1", "agent2"]
    assert delegator.selected_agents_for_request == ["agent1", "agent2"]


@pytest.mark.unit
@patch("src.stores.agent_manager_instance.get_available_agents")
def test_get_delegator_response_fallback_parser(mock_get_agents, delegator, sample_chat_request, mock_llm):
    mock_get_agents.return_value = [{"name": "agent1", "description": "test"}]
    mock_llm.return_value = Mock(content='agents: ["agent1"]')

    with patch.object(delegator.parser, "parse") as mock_parse:
        mock_parse.return_value = RankAgentsOutput(agents=["agent1"])
        result = delegator.get_delegator_response(sample_chat_request)

    assert result == ["agent1"]


@pytest.mark.unit
@pytest.mark.asyncio
@patch("src.config.load_agent_config")
async def test_try_agent_success(mock_load_config, delegator, sample_chat_request):
    mock_load_config.return_value = {"path": "test.path", "class_name": "TestAgent"}

    mock_module = Mock()
    mock_agent_class = Mock()
    mock_agent = Mock()
    mock_agent.chat = AsyncMock(return_value=AgentResponse(content="Success", response_type=ResponseType.SUCCESS))
    mock_agent_class.return_value = mock_agent
    mock_module.TestAgent = mock_agent_class

    with patch.dict("sys.modules", {"test.path": mock_module}):
        result = await delegator._try_agent("test_agent", sample_chat_request)

    assert result is not None
    assert result.content == "Success"
    assert result.response_type == ResponseType.SUCCESS


@pytest.mark.unit
@pytest.mark.asyncio
@patch("src.config.load_agent_config")
async def test_try_agent_error_response(mock_load_config, delegator, sample_chat_request):
    mock_load_config.return_value = {"path": "test.path", "class_name": "TestAgent"}

    mock_module = Mock()
    mock_agent_class = Mock()
    mock_agent = Mock()
    mock_agent.chat = AsyncMock(return_value=AgentResponse(content="Error", response_type=ResponseType.ERROR))
    mock_agent_class.return_value = mock_agent
    mock_module.TestAgent = mock_agent_class

    with patch.dict("sys.modules", {"test.path": mock_module}):
        result = await delegator._try_agent("test_agent", sample_chat_request)

    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delegate_chat_success(delegator, sample_chat_request):
    with patch.object(delegator, "get_delegator_response") as mock_get_response:
        mock_get_response.return_value = ["agent1"]
        with patch.object(delegator, "_try_agent") as mock_try:
            mock_try.return_value = AgentResponse(content="Success", response_type=ResponseType.SUCCESS)

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
    assert response.response_type == ResponseType.ERROR
    assert "All agents have been attempted" in response.error_message
