import React, { useState } from "react";
import {
  Box,
  Text,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Flex,
  Divider,
  Tag,
  HStack,
  Button,
  Popover,
  PopoverTrigger,
  PopoverContent,
  PopoverBody,
  PopoverArrow,
  PopoverCloseButton,
  Circle,
  List,
  ListItem,
  ListIcon,
  useDisclosure,
} from "@chakra-ui/react";
import ReactMarkdown from "react-markdown";
import {
  CrewResponseMetadata,
  TaskSummary,
  SubtaskOutput,
  TokenUsage,
} from "@/components/Agents/Crew/CrewResponseMessage.types";
import styles from "./CrewResponseMessage.module.css";

interface CrewResponseMessageProps {
  content: string;
  metadata?: CrewResponseMetadata;
}

/**
 * Custom components for enhanced ReactMarkdown rendering
 */
const MarkdownComponents = {
  h1: (props: any) => (
    <Text fontSize="xl" fontWeight="bold" my={2} {...props} />
  ),
  h2: (props: any) => (
    <Text fontSize="lg" fontWeight="bold" my={2} {...props} />
  ),
  h3: (props: any) => (
    <Text fontSize="md" fontWeight="bold" my={2} {...props} />
  ),
  h4: (props: any) => (
    <Text fontSize="sm" fontWeight="semibold" my={2} {...props} />
  ),
  h5: (props: any) => (
    <Text fontSize="xs" fontWeight="semibold" my={1} {...props} />
  ),
  h6: (props: any) => (
    <Text fontSize="xs" fontWeight="semibold" my={1} {...props} />
  ),
  p: (props: any) => <Text mb={2} {...props} />,
  a: (props: any) => (
    <Text as="a" color="blue.500" textDecoration="underline" {...props} />
  ),
  ul: (props: any) => <Box as="ul" pl={4} mb={2} {...props} />,
  ol: (props: any) => <Box as="ol" pl={4} mb={2} {...props} />,
  li: (props: any) => <Box as="li" ml={2} mb={1} {...props} />,
  blockquote: (props: any) => (
    <Box
      borderLeftWidth={2}
      borderLeftColor="gray.200"
      pl={3}
      py={1}
      my={2}
      {...props}
    />
  ),
  code: (props: any) => {
    const { inline, className, children, ...rest } = props;
    const match = /language-(\w+)/.exec(className || "");

    return !inline ? (
      <Box
        as="pre"
        p={2}
        borderRadius="md"
        bg="gray.700"
        color="white"
        overflowX="auto"
        fontSize="xs"
        my={2}
        {...rest}
      >
        <Box as="code" className={className} {...rest}>
          {children}
        </Box>
      </Box>
    ) : (
      <Box
        as="code"
        bg="gray.100"
        p={0.5}
        borderRadius="sm"
        fontSize="xs"
        {...rest}
      >
        {children}
      </Box>
    );
  },
  table: (props: any) => (
    <Box overflowX="auto" my={2}>
      <Box
        as="table"
        width="full"
        borderWidth={1}
        borderColor="gray.200"
        {...props}
      />
    </Box>
  ),
  th: (props: any) => (
    <Box
      as="th"
      bg="gray.50"
      p={2}
      borderWidth={1}
      borderColor="gray.200"
      fontWeight="semibold"
      {...props}
    />
  ),
  td: (props: any) => (
    <Box as="td" p={2} borderWidth={1} borderColor="gray.200" {...props} />
  ),
};

/**
 * Agent count badge with popover showing all agent names
 */
const AgentBadge: React.FC<{ agents: string[] }> = ({ agents }) => {
  // Use isOpen state to control the popover
  const { isOpen, onOpen, onClose } = useDisclosure();

  if (!agents || agents.length === 0) return null;

  return (
    <Box position="absolute" top="10px" right="10px" zIndex={1}>
      <Popover
        isOpen={isOpen}
        onClose={onClose}
        placement="top-end"
        closeOnBlur={true}
        trigger="hover"
        gutter={8}
      >
        <PopoverTrigger>
          <Circle
            size="26px"
            bg="blue.400"
            color="white"
            fontSize="xs"
            fontWeight="bold"
            cursor="pointer"
            onMouseEnter={onOpen}
            onMouseLeave={onClose}
            boxShadow="0 2px 4px rgba(0, 0, 0, 0.2)"
            _hover={{ bg: "blue.300" }}
          >
            {agents.length}
          </Circle>
        </PopoverTrigger>
        <PopoverContent
          width="auto"
          minWidth="200px"
          maxWidth="320px"
          bg="gray.800"
          borderColor="gray.700"
          boxShadow="lg"
        >
          <PopoverArrow bg="gray.800" />
          <PopoverBody p={3}>
            <Text fontWeight="semibold" fontSize="sm" mb={2} color="blue.200">
              Agents involved:
            </Text>
            <List spacing={2} fontSize="sm">
              {agents.map((agent, idx) => (
                <ListItem
                  key={idx}
                  display="flex"
                  alignItems="center"
                  color="gray.100"
                  py={1}
                  borderBottom={idx < agents.length - 1 ? "1px solid" : "none"}
                  borderColor="gray.700"
                >
                  <Box
                    as="span"
                    w="6px"
                    h="6px"
                    bg="blue.400"
                    borderRadius="full"
                    mr={2}
                  ></Box>
                  {agent}
                </ListItem>
              ))}
            </List>
          </PopoverBody>
        </PopoverContent>
      </Popover>
    </Box>
  );
};

/**
 * Component for displaying a subtask output with a truncation toggle
 */
const TruncatableTaskOutput: React.FC<{
  content: string;
  maxLines?: number;
}> = ({ content, maxLines = 4 }) => {
  const [expanded, setExpanded] = useState(false);

  const toggleExpanded = () => setExpanded(!expanded);

  return (
    <Box>
      <Box
        className={`${styles.taskOutput} ${expanded ? "" : styles.truncated}`}
        style={{ WebkitLineClamp: expanded ? "unset" : maxLines }}
        borderRadius="md"
        pt={1}
      >
        <ReactMarkdown components={MarkdownComponents}>{content}</ReactMarkdown>
      </Box>

      <Button
        size="xs"
        variant="ghost"
        onClick={toggleExpanded}
        mt={1}
        color="blue.300"
        fontWeight="medium"
        borderRadius="md"
        _hover={{ bg: "rgba(66, 153, 225, 0.12)" }}
        leftIcon={
          <Box as="span" fontSize="xs">
            {expanded ? "▲" : "▼"}
          </Box>
        }
      >
        {expanded ? "Show less" : "Show more"}
      </Button>
    </Box>
  );
};

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
    return (
      <ReactMarkdown components={MarkdownComponents}>{content}</ReactMarkdown>
    );
  }

  const formatTokens = (tokens?: TokenUsage) => {
    if (!tokens) return "N/A";
    return `Tokens In: ${tokens.prompt_tokens || 0} | Tokens Out: ${
      tokens.completion_tokens || 0
    } | Total Tokens: ${tokens.total_tokens || 0}`;
  };

  const formatTime = (time?: number) => {
    if (!time) return "N/A";
    return `${time.toFixed(2)}s`;
  };

  return (
    <Box className={styles.crewResponseContainer}>
      {/* Main content */}
      <Box mb={4}>
        <ReactMarkdown components={MarkdownComponents}>{content}</ReactMarkdown>
      </Box>

      {/* Metadata section */}
      <Accordion allowToggle mb={2} className={styles.metadataAccordion}>
        <AccordionItem border="none">
          <h2>
            <AccordionButton>
              <Box flex="1" textAlign="left" fontSize="sm">
                <Text fontSize="lg" fontWeight="medium">
                  Research & Orchestration
                </Text>
              </Box>
              <AccordionIcon />
            </AccordionButton>
          </h2>
          <AccordionPanel pb={4}>
            {/* Subtask Outputs */}
            {metadata.subtask_outputs &&
              metadata.subtask_outputs.length > 0 && (
                <Box>
                  <Text fontSize="sm" fontWeight="medium" mb={2}>
                    Here are all of the tasks that were completed:
                  </Text>
                  {metadata.subtask_outputs.map(
                    (subtask: SubtaskOutput, idx: number) => {
                      // Handle both formats (key/value or subtask/output)
                      const taskDescription =
                        subtask.subtask || subtask.key || "";
                      const taskOutput = subtask.output || subtask.value || "";

                      return (
                        <Box
                          key={idx}
                          mb={4}
                          className={styles.summaryBox}
                          position="relative"
                        >
                          {/* Agent count badge */}
                          {subtask.agents && (
                            <AgentBadge agents={subtask.agents} />
                          )}

                          {/* Task description */}
                          <Text
                            className={styles.task}
                            fontWeight="semibold"
                            mb={2}
                            pr={10} // Add padding to prevent overlap with the agent badge
                          >
                            {taskDescription}
                          </Text>

                          {/* Telemetry for this subtask */}
                          {subtask.telemetry && (
                            <HStack
                              fontSize="2xs"
                              spacing={3}
                              mb={2}
                              p={1.5}
                              bg="rgba(0, 0, 0, 0.2)"
                              borderRadius="md"
                              color="gray.400"
                            >
                              {subtask.telemetry.token_usage && (
                                <Flex align="center">
                                  <Text
                                    fontWeight="medium"
                                    color="gray.300"
                                    mr={1}
                                  >
                                    Tokens:
                                  </Text>
                                  <Text>
                                    {formatTokens(
                                      subtask.telemetry.token_usage
                                    )}
                                  </Text>
                                </Flex>
                              )}
                              {subtask.telemetry.processing_time?.duration && (
                                <Flex align="center">
                                  <Text
                                    fontWeight="medium"
                                    color="gray.300"
                                    mr={1}
                                  >
                                    Time:
                                  </Text>
                                  <Text>
                                    {formatTime(
                                      subtask.telemetry.processing_time.duration
                                    )}
                                  </Text>
                                </Flex>
                              )}
                            </HStack>
                          )}

                          <Divider my={2} borderColor="gray.700" />
                          <TruncatableTaskOutput content={taskOutput} />
                        </Box>
                      );
                    }
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
