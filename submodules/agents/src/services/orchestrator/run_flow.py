from typing import Dict, Any

# ------------------------------------------------------------
# 1.  Import flow + registry
from services.orchestrator.orchestration_flow import OrchestrationFlow
from services.orchestrator.registry.agent_bootstrap import bootstrap_agents

from models.service.chat_models import ChatRequest, AgentResponse


# -------------------------------------------------------------------
# STEP 2 – Run the flow (async)
# -------------------------------------------------------------------
async def run_flow(chat_request: ChatRequest):
    # 2a) set up LLM router (replace with your own wrapper)
    llm_router = "gemini/gemini-2.5-flash-preview-04-17"

    # 2b) initialize tools and agents (only registers if not already registered)
    bootstrap_agents(llm_router)

    # 2c) instantiate the flow
    flow = OrchestrationFlow(llm_model=llm_router)

    # 2d) kick off 🚀
    final_answer: Dict[str, Any] = await flow.kickoff_async(
        inputs={
            "chat_prompt": chat_request.prompt.content,
            "chat_history": [m.content[:100] for m in chat_request.chat_history],
        }
    )

    # Wrap the final answer in an AgentResponse
    return AgentResponse.success(
        content=final_answer["final_answer"],
        metadata={
            "subtask_outputs": final_answer["subtask_outputs"],
        },
    )
