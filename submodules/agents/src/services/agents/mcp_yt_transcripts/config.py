from models.service.agent_config import AgentConfig


class Config:
    """Configuration for MCP YouTube Transcripts Agent."""

    # *************
    # AGENT CONFIG
    # *************

    agent_config = AgentConfig(
        path="services.agents.mcp_agent.agent",
        class_name="MCPAgent",
        description="Provides access to YouTube video transcripts and subtitles through a simple interface.",
        delegator_description=(
            "A specialized agent that extracts transcripts from YouTube videos. "
            "This agent excels at retrieving captions and subtitles from YouTube content in multiple languages. "
            "Use this agent when you need to analyze video content, get information from YouTube videos without watching them, "
            "or need text versions of spoken content. The agent supports multiple video URL formats and "
            "can retrieve transcripts in different languages when available."
        ),
        human_readable_name="YouTube Transcripts",
        command="youtube-transcript",
        upload_required=False,
        is_enabled=True,
        mcp_server_url="https://mcp-server-4317ea48-cb55-4a12-8b2b-fb6a89478c92.supermachine.app",
        name="youtube_transcripts",
        # Note: The actual tools will be fetched at runtime from the MCP server
        # using the MultiServerMCPClient in the agent_manager.py
        # The tools below are placeholders and will be replaced with actual tools
        # fetched from the MCP server when the agent is initialized
        tools=[],
    )
