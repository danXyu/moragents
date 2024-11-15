// Widgets.tsx
import React, { FC } from "react";
import { Box, IconButton, Text } from "@chakra-ui/react";
import { X } from "lucide-react";
import {
  ChatMessage,
  ImageMessage,
  CryptoDataMessageContent,
} from "../../services/backendClient";
import { ImageDisplay } from "../ImageDisplay";
import TradingViewWidget from "./TradingViewWidget";

export const WIDGET_COMPATIBLE_AGENTS = ["imagen agent", "crypto data agent"];

export const shouldOpenWidget = (message: ChatMessage) => {
  if (message.agentName === "crypto data agent") {
    const content = message.content as unknown as CryptoDataMessageContent;
    return (
      WIDGET_COMPATIBLE_AGENTS.includes(message.agentName) && content.coinId
    );
  }
  return WIDGET_COMPATIBLE_AGENTS.includes(message.agentName);
};

interface WidgetsProps {
  activeWidget: ChatMessage | null;
  onClose: () => void;
}

export const Widgets: FC<WidgetsProps> = ({ activeWidget, onClose }) => {
  const renderWidget = () => {
    if (
      activeWidget?.role === "assistant" &&
      activeWidget.agentName === "imagen agent"
    ) {
      return (
        <Box p={4}>
          <ImageDisplay content={activeWidget.content as ImageMessage} />
        </Box>
      );
    }

    if (
      activeWidget?.role === "assistant" &&
      activeWidget.agentName === "crypto data agent"
    ) {
      const content =
        activeWidget.content as unknown as CryptoDataMessageContent;
      if (!content.coinId) return null;
      return (
        <Box
          h="full"
          w="full"
          display="flex"
          flexDirection="column"
          flexGrow={1}
        >
          <TradingViewWidget symbol={`${content.coinId.toUpperCase()}`} />
        </Box>
      );
    }

    return null;
  };

  return (
    <Box
      w="full"
      h="100%"
      bg="#020804"
      borderRadius="md"
      overflow="auto"
      position="relative"
      mt={16}
      display="flex"
      flexDirection="column"
      alignItems="center"
      flexGrow={1}
    >
      <Text
        fontSize="xl"
        fontWeight="bold"
        color="white"
        mt={4}
        textAlign="center"
        flexShrink={0}
      >
        Agent Widgets
      </Text>
      <IconButton
        aria-label="Close widgets"
        icon={<X />}
        onClick={onClose}
        position="absolute"
        top={2}
        right={4}
        bg="white"
        _hover={{ bg: "gray.300" }}
        zIndex={1}
        flexShrink={0}
      />
      <Box w="full" h="100%" display="flex" flexDirection="column" flexGrow={1}>
        {renderWidget()}
      </Box>
    </Box>
  );
};
