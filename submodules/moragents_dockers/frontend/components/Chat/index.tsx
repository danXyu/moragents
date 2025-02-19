import React, { FC, useState } from "react";
import { Flex, Box, useBreakpointValue } from "@chakra-ui/react";
import { MessageList } from "@/components/MessageList";
import { ChatInput } from "@/components/ChatInput";
import { LoadingIndicator } from "@/components/LoadingIndicator";
import { useChatContext } from "@/contexts/chat/useChatContext";

export const Chat: FC<{ isSidebarOpen?: boolean }> = ({
  isSidebarOpen = false,
}) => {
  const { state, sendMessage } = useChatContext();
  const { messages, currentConversationId, isLoading } = state;
  // Add local loading state to ensure loading indicator persists during transitions
  const [localLoading, setLocalLoading] = useState(false);

  const currentMessages = messages[currentConversationId] || [];
  const isMobile = useBreakpointValue({ base: true, md: false });

  // Combined loading state - show loading if either global or local loading is true
  const showLoading = isLoading || localLoading;

  const handleSubmit = async (message: string, file: File | null) => {
    try {
      setLocalLoading(true);
      await sendMessage(message, file);

      // Add a small delay to ensure loading indicator stays visible
      // until UI fully updates with the new messages
      setTimeout(() => {
        setLocalLoading(false);
      }, 200);
    } catch (error) {
      console.error("Error sending message:", error);
      setLocalLoading(false);
    }
  };

  return (
    <Box position="relative" height="100%" width="100%">
      <Flex
        direction="column"
        height="100%"
        width="100%"
        transition="all 0.3s ease-in-out"
        mt={2}
        paddingLeft={isMobile ? "5%" : isSidebarOpen ? "30%" : "20%"}
        paddingRight={isMobile ? "5%" : isSidebarOpen ? "20%" : "20%"}
        ml="auto"
        mr="auto"
      >
        <MessageList messages={currentMessages} />
        {showLoading && <LoadingIndicator />}
        <ChatInput
          onSubmit={handleSubmit}
          hasMessages={currentMessages.length > 1}
          disabled={showLoading}
          isSidebarOpen={isSidebarOpen}
        />
      </Flex>
    </Box>
  );
};
