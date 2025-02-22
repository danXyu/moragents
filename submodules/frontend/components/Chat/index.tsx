import React, { FC, useState } from "react";
import { Box, useBreakpointValue } from "@chakra-ui/react";
import { MessageList } from "@/components/MessageList";
import { ChatInput } from "@/components/ChatInput";
import { useChatContext } from "@/contexts/chat/useChatContext";

export const Chat: FC<{ isSidebarOpen?: boolean }> = ({
  isSidebarOpen = false,
}) => {
  const { state, sendMessage } = useChatContext();
  const { messages, currentConversationId, isLoading } = state;
  const [localLoading, setLocalLoading] = useState(false);

  const currentMessages = messages[currentConversationId] || [];
  const isMobile = useBreakpointValue({ base: true, md: false });
  const showLoading = isLoading || localLoading;

  const handleSubmit = async (message: string, file: File | null) => {
    try {
      setLocalLoading(true);
      await sendMessage(message, file);
      setTimeout(() => setLocalLoading(false), 200);
    } catch (error) {
      console.error("Error sending message:", error);
      setLocalLoading(false);
    }
  };

  return (
    <Box
      height="100vh"
      width="100%"
      paddingLeft={isMobile ? "5%" : isSidebarOpen ? "30%" : "20%"}
      paddingRight={isMobile ? "5%" : "20%"}
      display="flex"
      flexDirection="column"
    >
      <MessageList
        messages={currentMessages}
        isLoading={showLoading}
        isSidebarOpen={isSidebarOpen}
        onSubmit={handleSubmit}
        disabled={showLoading}
      />
      <Box position="sticky" bottom={0} bg="black" pt={2} pb={2}>
        <ChatInput
          onSubmit={handleSubmit}
          hasMessages={currentMessages.length > 1}
          disabled={showLoading}
        />
      </Box>
    </Box>
  );
};
