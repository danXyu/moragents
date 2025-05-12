from crewai import Agent

from services.orchestrator.registry.agent_registry import AgentRegistry
from services.orchestrator.registry.tool_registry import ToolRegistry
from services.orchestrator.registry.tool_bootstrap import bootstrap_tools
from services.agents.crypto_data.crew_agent import crypto_data_agent


def _register_agent(
    agent_name, role, goal, backstory, tool_names=None, allow_delegation=True, verbose=False, llm=None, **kwargs
):
    """
    Helper function to register an agent with error handling.

    Args:
        agent_name: Name to register the agent under
        role: The role of the agent
        goal: The goal of the agent
        backstory: The backstory of the agent
        tool_names: List of tool names to assign to this agent
        allow_delegation: Whether this agent can delegate tasks
        verbose: Whether to enable verbose mode
        llm: Language model to use
        **kwargs: Additional arguments to pass to the Agent constructor

    Returns:
        bool: True if registration was successful, False otherwise
    """
    if agent_name in AgentRegistry.all_names():
        return True  # Agent already registered

    try:
        # Collect tools based on tool names
        tools = []
        if tool_names:
            for tool_name in tool_names:
                if tool_name in ToolRegistry.all_names():
                    tools.append(ToolRegistry.get(tool_name))
                else:
                    print(f"Warning: Tool '{tool_name}' not found in registry")

        # Create agent
        agent = Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools,
            llm=llm,
            allow_delegation=allow_delegation,
            verbose=verbose,
            **kwargs,
        )

        # Register agent
        AgentRegistry.register(agent_name, agent)
        return True
    except Exception as e:
        print(f"Failed to initialize {agent_name}: {e}")
        return False


def bootstrap_agents(llm):
    """
    Register all default agents with the AgentRegistry.
    Only registers each agent if it hasn't already been registered.

    Args:
        llm: The language model to use for the agents
    """
    # Initialize tools first
    bootstrap_tools()

    # ======== RESEARCH & SEARCH AGENTS ========
    # General web researcher
    _register_agent(
        agent_name="research_agent",
        role="Web Research Specialist",
        goal="Find, verify and summarise information from the public internet",
        backstory="OSINT wizard who never misses a relevant source.",
        tool_names=["brave_search"],
        llm=llm,
    )

    # Document analyzer
    _register_agent(
        agent_name="document_analyzer",
        role="Document Analysis Expert",
        goal="Extract, search, and analyze information from various document formats",
        backstory="A specialist in document analysis with expertise in extracting insights from different file formats. "
        "Combines technical knowledge with analytical skills to process text-based information efficiently.",
        tool_names=["txt_search", "pdf_search"],
        llm=llm,
    )

    # ======== SOCIAL MEDIA AGENTS ========
    # Instagram specialist
    _register_agent(
        agent_name="instagram_agent",
        role="Instagram Data Specialist",
        goal="Extract and analyze content from Instagram profiles, posts, and hashtags",
        backstory="A social media expert specializing in Instagram data extraction and analysis. Skilled at gathering "
        "profiles, posts, comments, and engagement metrics from Instagram.",
        tool_names=["instagram_scraper"],
        llm=llm,
    )

    # TikTok specialist
    _register_agent(
        agent_name="tiktok_agent",
        role="TikTok Content Analyst",
        goal="Extract and analyze trending content, user data, and engagement patterns from TikTok",
        backstory="A social media analyst who specializes in TikTok's unique content ecosystem. Expert at identifying "
        "trends, analyzing video engagement, and extracting valuable insights from short-form video content.",
        tool_names=["tiktok_scraper"],
        llm=llm,
    )

    # Twitter/X analyst
    _register_agent(
        agent_name="twitter_analyst",
        role="Twitter/X Data Specialist",
        goal="Extract, monitor, and analyze Twitter/X conversations, trends, and user activity",
        backstory="A social listening expert who specializes in Twitter/X analytics. Skilled at extracting valuable "
        "signals from the noise of social conversations and identifying meaningful patterns.",
        tool_names=["twitter_scraper"],
        llm=llm,
    )

    # Social media intelligence agent
    _register_agent(
        agent_name="social_media_intelligence",
        role="Cross-Platform Social Media Analyst",
        goal="Analyze and compare trends, sentiments, and content across multiple social media platforms",
        backstory="A comprehensive social media intelligence expert who understands the unique characteristics of "
        "different platforms and can synthesize insights across them. Specializes in cross-platform analysis "
        "to form a complete picture of online conversations.",
        tool_names=[
            "instagram_scraper",
            "tiktok_scraper",
            "twitter_scraper",
            "facebook_posts_scraper",
            "reddit_scraper",
            "youtube_comments_scraper",
        ],
        llm=llm,
    )

    # ======== BUSINESS INTELLIGENCE AGENTS ========
    # Business data analyst
    _register_agent(
        agent_name="business_analyst",
        role="Business Intelligence Specialist",
        goal="Gather and analyze comprehensive business information from various sources",
        backstory="A meticulous business analyst who excels at gathering intelligence on companies, market trends, "
        "and competitive landscapes. Combines data from multiple sources to create detailed business "
        "profiles and insights.",
        tool_names=["google_places_scraper", "contact_info_scraper", "apollo_io_scraper", "similarweb_scraper"],
        llm=llm,
    )

    # LinkedIn intelligence agent
    _register_agent(
        agent_name="linkedin_intelligence",
        role="Professional Network Analyst",
        goal="Extract and analyze professional profiles, job market trends, and company information",
        backstory="An expert in professional networking intelligence who specializes in analyzing LinkedIn profiles, "
        "job postings, and professional connections. Skilled at identifying talent patterns, company growth "
        "signals, and industry movements.",
        tool_names=["linkedin_profile_scraper", "glassdoor_jobs_scraper", "indeed_scraper"],
        llm=llm,
    )

    # ======== E-COMMERCE & RETAIL AGENTS ========
    # E-commerce analyst
    _register_agent(
        agent_name="ecommerce_analyst",
        role="E-Commerce Intelligence Specialist",
        goal="Analyze product listings, pricing strategies, and consumer sentiment in online marketplaces",
        backstory="A retail intelligence expert who specializes in e-commerce analysis. Skilled at extracting product "
        "data, pricing information, and customer reviews to provide competitive insights and market trends.",
        tool_names=["amazon_product_crawler"],
        llm=llm,
    )

    # ======== TRAVEL & HOSPITALITY AGENTS ========
    # Travel intelligence agent
    _register_agent(
        agent_name="travel_intelligence",
        role="Travel & Hospitality Analyst",
        goal="Analyze travel destinations, accommodations, and traveler sentiment",
        backstory="A travel industry expert who specializes in analyzing destination popularity, accommodation quality, "
        "and traveler experiences. Provides comprehensive insights on travel trends and hospitality performance.",
        tool_names=["tripadvisor_reviews_scraper", "tripadvisor_scraper", "booking_reviews_scraper"],
        llm=llm,
    )

    # ======== REAL ESTATE AGENTS ========
    # Real estate market analyst
    _register_agent(
        agent_name="real_estate_analyst",
        role="Real Estate Market Specialist",
        goal="Analyze property listings, market trends, and location value",
        backstory="A real estate intelligence expert who specializes in property market analysis. Skilled at extracting "
        "and interpreting property listing data to identify market trends, pricing patterns, and investment "
        "opportunities.",
        tool_names=["zillow_scraper"],
        llm=llm,
    )

    # ======== MULTIMEDIA AGENTS ========
    # YouTube content analyst
    _register_agent(
        agent_name="youtube_analyst",
        role="YouTube Content Intelligence Specialist",
        goal="Extract and analyze content, trends, and audience engagement on YouTube",
        backstory="A video content expert who specializes in YouTube analytics. Skilled at extracting insights from "
        "video content, comments, and channel performance to identify content trends and audience preferences.",
        tool_names=["youtube_video_search", "youtube_channel_search", "youtube_comments_scraper"],
        llm=llm,
    )

    # ======== WEB SCRAPING SPECIALIST ========
    # Advanced web extraction specialist
    _register_agent(
        agent_name="web_extraction_specialist",
        role="Advanced Web Content Extraction Expert",
        goal="Extract structured data from any website, including dynamic and complex web applications",
        backstory="A web scraping virtuoso who can extract data from even the most challenging websites. Combines "
        "multiple scraping technologies to overcome anti-scraping measures and extract valuable information "
        "from any online source.",
        tool_names=["spider_scraper", "selenium_scraper", "website_search", "article_extractor_smart"],
        llm=llm,
    )

    # ======== CREATIVE & CONTENT AGENTS ========
    # Visual content creator
    _register_agent(
        agent_name="visual_content_creator",
        role="AI Visual Content Creator",
        goal="Generate and analyze visual content to enhance communication and marketing materials",
        backstory="A creative professional who specializes in AI-generated visual content. Combines artistic "
        "sensibility with technical expertise to create compelling images and extract information from "
        "visual sources.",
        tool_names=["dalle", "vision"],
        llm=llm,
    )

    # ======== PROGRAMMING & DEVELOPMENT AGENTS ========
    # Code assistant
    _register_agent(
        agent_name="code_assistant",
        role="Programming & Development Assistant",
        goal="Write, execute, and explain code to solve technical problems",
        backstory="A versatile programmer who can write efficient code in Python to solve complex problems. Combines "
        "technical expertise with clear explanations to make programming accessible and effective.",
        tool_names=["code_interpreter", "code_docs_search"],
        llm=llm,
    )

    # Crypto data agent (using existing implementation)
    if "crypto_data_agent" not in AgentRegistry.all_names():
        AgentRegistry.register("crypto_data_agent", crypto_data_agent)
