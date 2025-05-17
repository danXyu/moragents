import React from "react";
import { Box, Text, VStack, HStack, Badge } from "@chakra-ui/react";
import { StreamingState } from "@/contexts/chat/types";
import styles from "./index.module.css";

interface StreamingProgressProps {
  streamingState: StreamingState;
}

export const StreamingProgress: React.FC<StreamingProgressProps> = ({ streamingState }) => {
  if (!streamingState || streamingState.status === 'idle') {
    return null;
  }

  const getStatusMessage = () => {
    if (streamingState.status === 'synthesizing') {
      return 'Synthesizing final answer...';
    }
    
    if (streamingState.output) {
      return 'Agent Response';
    } else if (streamingState.subtask) {
      return 'Processing Subtask';
    }
    
    return 'Processing...';
  };

  return (
    <Box className={styles.progressContainer}>
      <VStack spacing={3} align="stretch">
        <Text fontSize="sm" fontWeight="semibold" color="gray.400">
          {getStatusMessage()}
        </Text>

        {streamingState.subtask && (
          <Box
            bg="gray.800"
            p={3}
            borderRadius="md"
            borderLeft="3px solid"
            borderColor="blue.500"
          >
            <Text fontSize="sm" color="gray.300" fontWeight="medium">
              Current Subtask:
            </Text>
            <Text fontSize="sm" color="white" mt={1}>
              {streamingState.subtask}
            </Text>
          </Box>
        )}

        {streamingState.agents && streamingState.agents.length > 0 && (
          <HStack spacing={2} flexWrap="wrap">
            <Text fontSize="xs" color="gray.500">
              Agents:
            </Text>
            {streamingState.agents.map((agent, index) => (
              <Badge key={index} colorScheme="purple" variant="outline" fontSize="xs">
                {agent}
              </Badge>
            ))}
          </HStack>
        )}

        {streamingState.output && streamingState.status === 'processing' && (
          <Box
            bg="gray.900"
            p={3}
            borderRadius="md"
            maxHeight="150px"
            overflowY="auto"
            className={styles.outputBox}
          >
            <Text fontSize="xs" color="gray.400" mb={1}>
              Result:
            </Text>
            <Text fontSize="sm" color="gray.200" whiteSpace="pre-wrap">
              {streamingState.output}
            </Text>
          </Box>
        )}
      </VStack>
    </Box>
  );
};