import React from "react";
import { Box, Text, VStack, HStack, Badge, Fade, Spinner } from "@chakra-ui/react";
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
    <Fade in={true} transition={{ enter: { duration: 0.2 } }}>
      <Box className={styles.progressContainer}>
        <VStack spacing={3} align="stretch">
          <HStack spacing={2}>
            <Spinner size="sm" color="blue.500" />
            <Text fontSize="sm" fontWeight="semibold" color="gray.400">
              {getStatusMessage()}
            </Text>
          </HStack>

          {streamingState.subtask && (
            <Fade in={true} transition={{ enter: { duration: 0.3 } }}>
              <Box
                bg="gray.800"
                p={3}
                borderRadius="md"
                borderLeft="3px solid"
                borderColor="blue.500"
                transition="all 0.3s ease-in-out"
              >
                <Text fontSize="sm" color="gray.300" fontWeight="medium">
                  Current Subtask:
                </Text>
                <Text fontSize="sm" color="white" mt={1}>
                  {streamingState.subtask}
                </Text>
              </Box>
            </Fade>
          )}

          {streamingState.agents && streamingState.agents.length > 0 && (
            <Fade in={true} transition={{ enter: { duration: 0.3, delay: 0.1 } }}>
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
            </Fade>
          )}

          {streamingState.output && streamingState.status === 'processing' && (
            <Fade in={true} transition={{ enter: { duration: 0.4, delay: 0.2 } }}>
              <Box
                bg="gray.900"
                p={3}
                borderRadius="md"
                maxHeight="150px"
                overflowY="auto"
                className={styles.outputBox}
                transition="all 0.3s ease-in-out"
              >
                <Text fontSize="xs" color="gray.400" mb={1}>
                  Result:
                </Text>
                <Text fontSize="sm" color="gray.200" whiteSpace="pre-wrap">
                  {streamingState.output}
                </Text>
              </Box>
            </Fade>
          )}
          
          {streamingState.status === 'synthesizing' && (
            <Fade in={true} transition={{ enter: { duration: 0.3 } }}>
              <Box
                bg="yellow.900"
                p={3}
                borderRadius="md"
                borderLeft="3px solid"
                borderColor="yellow.500"
              >
                <Text fontSize="sm" color="yellow.200">
                  Combining agent responses into a final answer...
                </Text>
              </Box>
            </Fade>
          )}
        </VStack>
      </Box>
    </Fade>
  );
};