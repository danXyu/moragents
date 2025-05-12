"""
CrewAI Flow that:
1. Summarises recent chat.
2. Lets an LLM break the user prompt into sub‑tasks (structured output).
3. Lets the same LLM map each sub‑task to the best agent (structured output).
4. Runs sub‑crews in parallel.
5. Synthesises the final answer.
"""

from __future__ import annotations

import logging
from asyncio import TimeoutError, gather, wait_for
from typing import Any, Dict, List

from crewai import LLM, Crew, Process, Task
from crewai.flow.flow import Flow, listen, start

from .orchestration_state import (
    AssignmentPlan,
    OrchestrationState,
    ProcessingTime,
    SubtaskOutput,
    SubtaskPlan,
    Telemetry,
    TokenUsage,
)
from .registry.agent_registry import AgentRegistry
from .utils import parse_llm_structured_output

logger = logging.getLogger(__name__)

# Constants to control execution flow
MAX_SUBTASKS = 5  # Limit number of subtasks to prevent excessive complexity
SUBTASK_TIMEOUT = 180  # Maximum time (seconds) to wait for a subtask to complete
DEFAULT_TASK_OUTPUT = "Unable to complete this task within the allowed constraints."


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
            "Prioritize quality over quantity. We want as few high quality subtasks as possible. "
            "Each subtask must be specific, clear, and directly actionable. "
            "Return ONLY valid JSON matching the SubtaskPlan schema.\n"
            f"Goal: {self.state.chat_prompt}\n\nChat history summary: {self.state.chat_history_summary}"
        )
        llm = LLM(model=self.llm_model, response_format=SubtaskPlan)
        plan = llm.call(prompt)
        plan = parse_llm_structured_output(plan, SubtaskPlan, logger, "SubtaskPlan")

        # Limit number of subtasks to prevent complexity
        if plan and plan.subtasks and len(plan.subtasks) > MAX_SUBTASKS:
            plan.subtasks = plan.subtasks[:MAX_SUBTASKS]

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
            "Prefer more specific agents over generalists. "
            "Assemble complementary crews where each agent contributes unique strengths. "
            "Each crew should contain 1-3 agents with relevant skills for the subtask. "
            "Return ONLY valid JSON matching the AssignmentPlan schema.\n"
            f"Subtasks: {self.state.subtasks}"
        )
        llm = LLM(model=self.llm_model, response_format=AssignmentPlan)
        mapping = llm.call(prompt)
        mapping = parse_llm_structured_output(mapping, AssignmentPlan, logger, "AssignmentPlan")

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

            # Enhance the subtask description with direct guidance, original chat prompt, summarized chat history
            enhanced_subtask = (
                f"Original user prompt: {self.state.chat_prompt}\n"
                f"Summary of chat history: {self.state.chat_history_summary}\n\n"
                f"Subtask: {subtask}\n\n"
                "IMPORTANT INSTRUCTIONS:\n"
                "1. Complete this task with the fewest possible steps\n"
                "2. Use your tools directly and efficiently\n"
                "3. Avoid unnecessary reasoning loops\n"
                "4. Focus only on the specific task - do not expand the scope\n"
                "5. Return a clear, concise answer without additional questions\n"
                "6. Do not use the same tool more than once"
            )

            # Track processing time
            start_time = time.time()

            crew = Crew(
                agents=crew_agents,
                tasks=[
                    Task(
                        description=enhanced_subtask,
                        expected_output="Concise result focusing only on the requested information",
                        agent=crew_agents[0],
                    )
                ],
                process=Process.sequential,
                manager_llm=self.llm_model,
                verbose=False,
            )

            try:
                # Add timeout to prevent hanging tasks
                result = await wait_for(crew.kickoff_async(), timeout=SUBTASK_TIMEOUT)

                end_time = time.time()

                # Extract token usage if available
                token_usage = TokenUsage()
                if result.token_usage:
                    token_usage.total_tokens = result.token_usage.total_tokens
                    token_usage.prompt_tokens = result.token_usage.prompt_tokens
                    token_usage.completion_tokens = result.token_usage.completion_tokens
                    token_usage.cached_prompt_tokens = result.token_usage.cached_prompt_tokens

                # Create processing time tracking
                processing_time = ProcessingTime(
                    start_time=start_time, end_time=end_time, duration=end_time - start_time
                )

                # Create telemetry object
                telemetry = Telemetry(token_usage=token_usage, processing_time=processing_time)

                # Check if result contains error messages about iteration limits
                output_str = str(result.raw)
                if "Maximum iterations reached" in output_str or "iteration limit" in output_str:
                    logger.warning(f"Task hit iteration limit: {subtask}")
                    output_str = f"Partial result (hit iteration limit): {output_str}"

                # Return structured output
                return SubtaskOutput(subtask=subtask, output=output_str, agents=agents, telemetry=telemetry)

            except TimeoutError:
                # Handle timeout
                end_time = time.time()
                processing_time = ProcessingTime(
                    start_time=start_time, end_time=end_time, duration=end_time - start_time
                )
                telemetry = Telemetry(processing_time=processing_time)

                logger.warning(f"Task timed out: {subtask}")
                return SubtaskOutput(
                    subtask=subtask,
                    output=f"This task could not be completed within the allotted time. "
                    f"Partial information: {DEFAULT_TASK_OUTPUT}",
                    agents=agents,
                    telemetry=telemetry,
                )

            except Exception as e:
                # Handle any other exceptions
                end_time = time.time()
                processing_time = ProcessingTime(
                    start_time=start_time, end_time=end_time, duration=end_time - start_time
                )
                telemetry = Telemetry(processing_time=processing_time)

                logger.error(f"Error executing task '{subtask}': {str(e)}")
                return SubtaskOutput(
                    subtask=subtask,
                    output=f"Error executing this task: {str(e)}. {DEFAULT_TASK_OUTPUT}",
                    agents=agents,
                    telemetry=telemetry,
                )

        coros = [_execute(assignment.subtask, assignment.agents) for assignment in self.state.assignments]
        self.state.subtask_outputs = await gather(*coros)

    # 5️⃣  Synthesise final answer ---------------------------------------
    @listen(run_sub_crews)
    def synthesise(self) -> Dict[str, Any]:
        prompt = (
            "Combine the following sub‑task results into one clear answer for the user. "
            "If some sub-tasks failed or produced limited results, focus on the successful ones. "
            "Always provide the most helpful answer possible with the available information. "
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
