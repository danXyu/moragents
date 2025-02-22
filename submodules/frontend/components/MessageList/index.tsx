import React, { FC, useRef, useEffect, useState } from "react";
import { Box, VStack } from "@chakra-ui/react";
import { ChatMessage } from "@/services/types";
import { MessageItem } from "@/components/MessageItem";
import { LoadingIndicator } from "@/components/LoadingIndicator";
import PrefilledOptions from "@/components/ChatInput/PrefilledOptions";

type MessageListProps = {
  messages: ChatMessage[];
  isLoading: boolean;
  isSidebarOpen: boolean;
  onSubmit: (message: string, file: File | null) => Promise<void>;
  disabled: boolean;
};

export const MessageList: FC<MessageListProps> = ({
  messages,
  isLoading,
  isSidebarOpen,
  onSubmit,
  disabled,
}) => {
  const lastMessageRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (messages.length > 0 && lastMessageRef.current && containerRef.current) {
      const lastMessage = lastMessageRef.current;
      const container = containerRef.current;
      const scrollPosition = lastMessage.offsetTop - container.offsetTop;
      container.scrollTop = scrollPosition;
    }
  }, [messages]);

  const handlePrefilledSelect = async (selectedMessage: string) => {
    if (isSubmitting || disabled) return;
    try {
      setIsSubmitting(true);
      await onSubmit(selectedMessage, null);
    } catch (error) {
      console.error("Error submitting prefilled message:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Box
      position="relative"
      display="flex"
      flexDirection="column"
      height="calc(100vh - 120px)"
      maxHeight="calc(100vh - 120px)"
      mb={4}
    >
      {/* Scrollable messages container */}
      <Box
        ref={containerRef}
        flex="1 1 auto"
        overflowY="auto"
        overflowX="hidden"
        position="relative"
        pb={4} // Add padding to prevent overlap with PrefilledOptions
        sx={{
          "&::-webkit-scrollbar": { width: "4px" },
          "&::-webkit-scrollbar-track": { background: "#000" },
          "&::-webkit-scrollbar-thumb": {
            background: "#333",
            borderRadius: "2px",
          },
        }}
      >
        <VStack spacing={0} width="100%" align="stretch">
          {messages.map((message, index) => (
            <div
              ref={index === messages.length - 1 ? lastMessageRef : undefined}
              key={index}
            >
              <MessageItem message={message} />
            </div>
          ))}
          {isLoading && (
            <Box width="100%" py={4}>
              <LoadingIndicator />
            </Box>
          )}
        </VStack>
      </Box>

      {/* PrefilledOptions container */}
      <Box width="100%" bg="black" mt="auto" position="relative" zIndex={1}>
        <PrefilledOptions
          onSelect={handlePrefilledSelect}
          isSidebarOpen={isSidebarOpen}
          onExpandChange={(isExpanded: boolean) => {
            if (isExpanded && containerRef.current) {
              containerRef.current.scrollTop =
                containerRef.current.scrollHeight;
            }
          }}
        />
      </Box>
    </Box>
  );
};
