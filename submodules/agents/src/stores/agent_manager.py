import asyncio
import importlib
import traceback
from typing import Any, Dict, List, Optional, Tuple

from langchain.tools import StructuredTool

# from langchain_together import ChatTogether
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_ollama import ChatOllama

from config import LLM_AGENT, load_agent_configs, setup_logging
from models.service.agent_config import AgentConfig

logger = setup_logging()


class AgentManager:
    """Manages the loading, selection and activation of agents in the system."""

    def __init__(self, config: List[Dict]) -> None:
        self.active_agent: Optional[str] = None
        self.selected_agents: List[str] = []
        self.config: List[Dict] = config
        self.agents: Dict[str, Any] = {}
        self.llm: Optional[ChatOllama] = LLM_AGENT

        # Load all agents (see note on async below).
        self._load_all_agents()

        # Select all agents by default (respecting ordering from config).
        self.set_selected_agents([agent["name"] for agent in config])
        logger.info("AgentManager initialized with %d agents", len(self.selected_agents))

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------

    def reset(self) -> None:
        """Reload configuration from disk and rebuild the manager state."""
        fresh_configs = load_agent_configs()
        self.active_agent = None
        self.selected_agents = []
        self.config = fresh_configs
        self.agents.clear()

        self._load_all_agents()
        self.set_selected_agents([agent["name"] for agent in fresh_configs])
        logger.info("AgentManager reset with %d agents", len(self.selected_agents))

    def load_all_agents(self, llm: ChatOllama) -> None:  # kept for API backward‑compat
        """Sync shim around the new async‑aware loader."""
        self.llm = llm
        self._load_all_agents()

    # ---------------------------------------------------------------------
    # Internal helpers – agent loading & MCP integration
    # ---------------------------------------------------------------------

    def _load_all_agents(self) -> None:
        """Load every agent listed in ``self.config``.

        Any MCP tool discovery that needs network I/O is performed *without*
        blocking a running event‑loop (see :meth:`_fetch_mcp_tools`).
        """
        for agent_cfg in self.get_available_agents():
            self._load_agent(agent_cfg)
        logger.info("Loaded %d agents", len(self.agents))

    def _load_agent(self, agent_config: Dict) -> bool:
        """Import the agent class, optionally augment its config with tools."""
        try:
            # Try to enrich config with remote MCP tool schemas first.
            if agent_config.get("mcp_server_url"):
                self._fetch_mcp_tools(agent_config)

            module = importlib.import_module(agent_config["path"])
            agent_class = getattr(module, agent_config["class_name"])
            self.agents[agent_config["name"]] = agent_class(agent_config, self.llm)
            logger.info("Loaded agent: %s", agent_config["name"])
            return True
        except Exception as exc:  # noqa: BLE001 – want the *message* logged
            logger.error("Failed to load agent %s: %s", agent_config["name"], exc)
            logger.debug("%s", traceback.format_exc())
            return False

    # -----------------------------
    # Async MCP helpers
    # -----------------------------

    async def _gather_tools_async(self, agent_name: str, url: str) -> List[StructuredTool]:
        logger.info("Connecting to MCP server at %s for %s", url, agent_name)
        async with MultiServerMCPClient({agent_name: {"url": url, "transport": "sse"}}) as client:
            tools = client.get_tools()
            logger.info("Retrieved %d tools from MCP server for %s", len(tools), agent_name)
            return tools

    def _update_config_with_tools(self, agent_config: Dict, tools: List[StructuredTool]) -> None:
        tool_schemas: List[Dict] = []
        for tool in tools:
            try:
                schema = None
                if hasattr(tool, "args_schema") and tool.args_schema is not None:
                    if hasattr(tool.args_schema, "model_json_schema"):
                        schema = tool.args_schema.model_json_schema()
                if schema:
                    tool_schemas.append(
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": {
                                "type": "object",
                                "properties": schema.get("properties", {}),
                                "required": schema.get("required", []),
                            },
                        }
                    )
                else:
                    tool_schemas.append({"name": tool.name, "description": tool.description})
            except Exception as exc:  # noqa: BLE001
                logger.warning("Error processing tool %s: %s", getattr(tool, "name", "unknown"), exc)
                tool_schemas.append(
                    {"name": getattr(tool, "name", "unknown"), "description": getattr(tool, "description", "")}
                )

        agent_config["tools"] = tool_schemas
        logger.info(
            "Updated agent config for %s with %d tool schemas", agent_config.get("name", "unknown"), len(tool_schemas)
        )

    def _fetch_mcp_tools(self, agent_config: Dict) -> None:
        """Fetch remote tool metadata without falling foul of nested event‑loops.

        * If we are **not** currently inside an event loop, run the network
          coroutine with :pyfunc:`asyncio.run` (blocking).
        * If a loop *is* already running (e.g. FastAPI, Jupyter), schedule the
          coroutine as a background task and return immediately.
        """
        agent_name = agent_config["name"]
        mcp_url = agent_config["mcp_server_url"]

        async def job():
            tools = await self._gather_tools_async(agent_name, mcp_url)
            self._update_config_with_tools(agent_config, tools)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # No loop: safe to block synchronously
            asyncio.run(job())
        else:
            # Already inside an event loop – fire‑and‑forget.  If you *need*
            # to await results synchronously, refactor your caller to async.
            loop.create_task(job())

    # ---------------------------------------------------------------------
    #                            PUBLIC API
    # ---------------------------------------------------------------------

    def get_active_agent(self) -> Optional[str]:
        return self.active_agent

    def set_active_agent(self, agent_name: Optional[str]) -> None:
        self.active_agent = agent_name

    def clear_active_agent(self) -> None:
        self.active_agent = None

    def get_available_agents(self) -> List[Dict]:
        return self.config

    def get_selected_agents(self) -> List[str]:
        return self.selected_agents

    def set_selected_agents(self, agent_names: List[str]) -> None:
        valid_names = {agent["name"] for agent in self.config}
        invalid_names = [name for name in agent_names if name not in valid_names]
        if invalid_names:
            raise ValueError(f"Invalid agent names provided: {invalid_names}")
        self.selected_agents = agent_names
        if self.active_agent not in agent_names:
            self.clear_active_agent()

    def get_agent_config(self, agent_name: str) -> Optional[Dict]:
        return next((agent for agent in self.config if agent["name"] == agent_name), None)

    def get_agent(self, agent_name: str) -> Optional[Any]:
        return self.agents.get(agent_name)

    def get_agent_by_command(self, command: str) -> Optional[str]:
        for agent in self.config:
            if agent["command"] == command:
                return agent["name"]
        return None

    def parse_command(self, message: str) -> Tuple[Optional[str], str]:
        if not message.startswith("/"):
            return None, message
        parts = message[1:].split(maxsplit=1)
        command = parts[0]
        remainder = parts[1] if len(parts) > 1 else ""
        return self.get_agent_by_command(command), remainder

    # ---------------------------------------------------------------------
    # Dynamic MCP agent creation (mostly unchanged except async tweaks)
    # ---------------------------------------------------------------------

    async def create_mcp_agent(self, agent_data: Dict) -> Dict:
        agent_name = agent_data["human_readable_name"].replace(" ", "_").lower()

        tools = await self._gather_tools_async(agent_name, agent_data["mcp_server_url"])
        self._update_config_with_tools(agent_data, tools)  # temporary dict

        agent_config = AgentConfig(
            path="services.agents.mcp_agent.agent",
            name=agent_name,
            class_name="MCPAgent",
            description=agent_data["description"],
            delegator_description=agent_data["delegator_description"],
            human_readable_name=agent_data["human_readable_name"],
            command=agent_data["command"],
            upload_required=agent_data.get("upload_required", False),
            is_enabled=agent_data.get("is_enabled", True),
            tools=agent_data["tools"],
            mcp_server_url=agent_data["mcp_server_url"],
        ).model_dump()

        self.config.append(agent_config)
        self._load_agent(agent_config)
        if agent_name not in self.selected_agents:
            self.selected_agents.append(agent_name)
        logger.info("Created new MCP agent: %s", agent_name)
        return agent_config


# -------------------------------------------------------------------------
# Module‑level singleton (unchanged)
# -------------------------------------------------------------------------

# agent_configs = load_agent_configs()
# logger.info("Loaded %d agents from configuration", len(agent_configs))
agent_manager_instance = AgentManager([])
