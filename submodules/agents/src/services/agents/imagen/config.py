from langchain.schema import SystemMessage
from models.service.agent_config import AgentConfig


class Config:
    """Configuration for Image Generation Agent."""

    # *************
    # AGENT CONFIG
    # *************

    agent_config = AgentConfig(
        path="services.agents.imagen.agent",
        class_name="ImagenAgent",
        description="Use your imagination! Create or generate images based on your prompt",
        delegator_description="Specializes EXCLUSIVELY in generating visual content like charts, infographics, token logos, "
        "or explanatory diagrams. ONLY use when the user explicitly requests image creation or visual "
        "representation of data.",
        human_readable_name="Image Generator",
        command="imagen",
        upload_required=False,
    )

    # *************
    # SYSTEM MESSAGE
    # *************

    system_message = SystemMessage(
        content=(
            "You are an image generation assistant. "
            "Help users create images by understanding their prompts "
            "and generating appropriate images."
        )
    )

    # *************
    # TOOLS CONFIG
    # *************

    tools = []  # No tools needed for image generation

    # *************
    # API CONFIG
    # *************

    CHROME_BINARY = "/usr/bin/chromium"
    CHROME_DRIVER = "/usr/bin/chromedriver"
    FLUX_AI_URL = "https://fluxai.pro/fast-flux"
    PAGE_LOAD_TIMEOUT = 30  # seconds
    ELEMENT_WAIT_TIMEOUT = 30  # seconds
