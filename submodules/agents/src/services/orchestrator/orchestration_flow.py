"""
CrewAI Flow that:
1. Summarises recent chat.
2. Lets an LLM break the user prompt into sub‑tasks (structured output).
3. Lets the same LLM map each sub‑task to the best agent (structured output).
4. Runs sub‑crews in parallel.
5. Synthesises the final answer.
"""

from __future__ import annotations
import logging
from typing import Dict, List, Any
from asyncio import gather

from crewai.flow.flow import Flow, start, listen
from crewai import Crew, Task, Process, LLM

from .utils import parse_llm_structured_output
from .registry.agent_registry import AgentRegistry
from .orchestration_state import (
    OrchestrationState,
    SubtaskOutput,
    Telemetry,
    ProcessingTime,
    TokenUsage,
    AssignmentPlan,
    SubtaskPlan,
)

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------- #
# Flow implementation
# --------------------------------------------------------------------- #
class OrchestrationFlow(Flow[OrchestrationState]):
    def __init__(self, llm_model: str = "gemini/gemini-2.5-flash-preview-04-17"):
        super().__init__()
        self.llm_model = llm_model

    # 1️⃣  Summarise recent chat -----------------------------------------
    @start()
    def initialise(self) -> None:
        print(f"Initialising flow with state: {self.state}")
        chat_prompt = self.state.chat_prompt
        chat_history = self.state.chat_history
        self.state.chat_prompt = chat_prompt

        history_text = "\n".join(chat_history)
        llm = LLM(model=self.llm_model)
        resp = llm.call("Summarise the following dialogue in ≤4 sentences.\n" + history_text)
        self.state.chat_history_summary = resp.strip()

    # 2️⃣  Sub‑task planning (LLM function‑call, structured) -------------
    @listen(initialise)
    def create_subtasks(self):
        prompt = (
            "You are an expert project planner. "
            "Break the user's goal into minimal action-oriented subtasks. "
            "Prioritize quality over quantity. We want as few high quality subtasks as possible."
            "Return ONLY valid JSON matching the SubtaskPlan schema.\n"
            f"Goal: {self.state.chat_prompt}\n\nChat history summary: {self.state.chat_history_summary}"
        )
        llm = LLM(model=self.llm_model, response_format=SubtaskPlan)
        plan = llm.call(prompt)
        plan = parse_llm_structured_output(plan, SubtaskPlan, logger, "SubtaskPlan")
        logger.info(f"READ THIS Subtask plan: {plan}")
        self.state.subtasks = plan.subtasks

    # 3️⃣  Agent assignment (LLM decides, structured) --------------------
    @listen(create_subtasks)
    def assign_agents(self):
        agent_descriptions = AgentRegistry.llm_choice_payload()
        prompt = (
            "You are a senior project manager. "
            "You have a pool of specialised agents:\n"
            f"{agent_descriptions}\n"
            "Given these subtasks, pick the set of best agents for each. "
            "A given subtask might need multiple agents to complete. "
            "Return ONLY valid JSON matching the AssignmentPlan schema.\n"
            f"Subtasks: {self.state.subtasks}"
        )
        llm = LLM(model=self.llm_model, response_format=AssignmentPlan)
        mapping = llm.call(prompt)
        mapping = parse_llm_structured_output(mapping, AssignmentPlan, logger, "AssignmentPlan")
        logger.info(f"READ THIS Assignment plan: {mapping}")
        self.state.assignments = mapping.assignments

    # 4️⃣  Run each sub‑task in parallel ----------------------------------
    @listen(assign_agents)
    async def run_sub_crews(self):
        import time

        async def _execute(subtask: str, agents: List[str]) -> SubtaskOutput:
            # Get all agents assigned to this subtask
            crew_agents = [AgentRegistry.get(agent_name) for agent_name in agents]

            # Early exit if no agents were found
            if not crew_agents:
                logger.error(f"No agents found for subtask: {subtask}")
                return SubtaskOutput(
                    subtask=subtask,
                    output="Error: No agents available to execute this task",
                    agents=agents,
                    telemetry=Telemetry(
                        processing_time=ProcessingTime(start_time=time.time(), end_time=time.time(), duration=0)
                    ),
                )

            # Track processing time
            start_time = time.time()

            crew = Crew(
                agents=crew_agents,
                tasks=[
                    Task(
                        description=subtask,
                        expected_output="Concise result",
                        agent=crew_agents[0],
                    )
                ],
                process=Process.sequential,
                manager_llm=self.llm_model,
                verbose=False,
            )

            result = await crew.kickoff_async()
            end_time = time.time()

            # Extract token usage if available
            token_usage = TokenUsage()
            if result.token_usage:
                token_usage.total_tokens = result.token_usage.total_tokens
                token_usage.prompt_tokens = result.token_usage.prompt_tokens
                token_usage.completion_tokens = result.token_usage.completion_tokens
                token_usage.cached_prompt_tokens = result.token_usage.cached_prompt_tokens

            # Create processing time tracking
            processing_time = ProcessingTime(start_time=start_time, end_time=end_time, duration=end_time - start_time)

            # Create telemetry object
            telemetry = Telemetry(token_usage=token_usage, processing_time=processing_time)

            # Return structured output
            return SubtaskOutput(subtask=subtask, output=str(result.raw), agents=agents, telemetry=telemetry)

        coros = [_execute(assignment.subtask, assignment.agents) for assignment in self.state.assignments]
        self.state.subtask_outputs = await gather(*coros)

    # 5️⃣  Synthesise final answer ---------------------------------------
    @listen(run_sub_crews)
    def synthesise(self) -> Dict[str, Any]:
        prompt = (
            "Combine the following sub‑task results into one clear answer for the user."
            "\n\nUser prompt:\n"
            f"{self.state.chat_prompt}\n\n"
            "Sub‑task outputs:\n"
        )
        for subtask_output in self.state.subtask_outputs:
            prompt += f"\n### {subtask_output.subtask}\n{subtask_output.output}\n"

        llm = LLM(model=self.llm_model)
        resp = llm.call(prompt)
        self.state.final_answer = resp.strip()

        return {
            "final_answer": self.state.final_answer,
            "subtask_outputs": self.state.subtask_outputs,
        }
