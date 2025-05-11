import React from "react";
import {
  Box,
  Text,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Flex,
  Badge,
  Divider,
} from "@chakra-ui/react";
import ReactMarkdown from "react-markdown";
import {
  CrewResponseMetadata,
  TaskSummary,
} from "@/components/Agents/Crew/CrewResponseMessage.types";
import styles from "./CrewResponseMessage.module.css";

interface CrewResponseMessageProps {
  content: string;
  metadata?: CrewResponseMetadata;
}

/**
 * Renders a response from the BasicOrchestrator crew with metadata
 * about the contributing agents and task summaries.
 */
const CrewResponseMessage: React.FC<CrewResponseMessageProps> = ({
  content,
  metadata,
}) => {
  if (!metadata) {
    // If no metadata, just render the content as markdown
    return <ReactMarkdown>{content}</ReactMarkdown>;
  }

  return (
    <Box className={styles.crewResponseContainer}>
      {/* Main content */}
      <Box mb={4}>
        <ReactMarkdown>{content}</ReactMarkdown>
      </Box>

      {/* Metadata section */}
      <Accordion allowToggle mb={2} className={styles.metadataAccordion}>
        <AccordionItem border="none">
          <h2>
            <AccordionButton>
              <Box flex="1" textAlign="left" fontSize="sm">
                <Text fontSize="lg" fontWeight="medium">
                  Orchestration Details
                </Text>
              </Box>
              <AccordionIcon />
            </AccordionButton>
          </h2>
          <AccordionPanel pb={4}>
            {/* Contributing Agents */}
            {metadata.contributing_agents && (
              <Box mb={3}>
                <Text fontSize="sm" fontWeight="medium" mb={1}>
                  Contributing Agents:
                </Text>
                <Flex className={styles.badgeContainer}>
                  {metadata.contributing_agents.map(
                    (agent: string, index: number) => (
                      <span key={index} className={styles.badge}>
                        {agent}
                      </span>
                    )
                  )}
                </Flex>
              </Box>
            )}

            {/* Token Usage */}
            {metadata.token_usage && (
              <Box mb={3}>
                <Text fontSize="sm" fontWeight="medium" mb={1}>
                  Token Usage:
                </Text>
                <Text fontSize="xs">
                  Input: {metadata.token_usage.prompt_tokens || 0} | Output:{" "}
                  {metadata.token_usage.completion_tokens || 0} | Total:{" "}
                  {metadata.token_usage.total_tokens || 0}
                </Text>
              </Box>
            )}

            {/* Task Summaries */}
            {metadata.task_summaries && metadata.task_summaries.length > 0 && (
              <Box>
                <Text fontSize="sm" fontWeight="medium" mb={1}>
                  Task Summaries:
                </Text>
                {metadata.task_summaries.map(
                  (task: TaskSummary, index: number) => (
                    <Box key={index} className={styles.summaryBox}>
                      <Text className={styles.task} fontWeight="medium">
                        Task {task.task_index + 1}
                      </Text>
                      <Divider my={1} />
                      <Text className={styles.taskPreview}>
                        {task.output_preview}
                      </Text>
                    </Box>
                  )
                )}
              </Box>
            )}
          </AccordionPanel>
        </AccordionItem>
      </Accordion>
    </Box>
  );
};

export default CrewResponseMessage;
