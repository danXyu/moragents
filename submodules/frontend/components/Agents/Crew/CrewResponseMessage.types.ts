/**
 * Types for token usage information from the LLM.
 */
export interface TokenUsage {
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
}

/**
 * Types for task summary information from each agent task.
 */
export interface TaskSummary {
  task_index: number;
  output_length: number;
  output_preview: string;
}

/**
 * Metadata structure for crew responses as returned by BasicOrchestrator.
 */
export interface CrewResponseMetadata {
  /**
   * Indicates if the response was produced through agent collaboration
   */
  collaboration?: string;

  /**
   * List of agents that contributed to the response
   */
  contributing_agents?: string[];

  /**
   * Token usage statistics from the LLM
   */
  token_usage?: TokenUsage;

  /**
   * Summaries of each task executed by the crew
   */
  task_summaries?: TaskSummary[];

  /**
   * Any additional metadata fields
   */
  [key: string]: any;
}
