import React, { FC, useEffect, useRef } from "react";
import { Box } from "@chakra-ui/react";
import { ChatMessage } from "@/services/types";
import { MessageItem } from "@/components/MessageItem";

import styles from "./index.module.css";

type MessageListProps = {
  messages: ChatMessage[];
  paddingBottom?: number;
};

export const MessageList: FC<MessageListProps> = ({
  messages,
  paddingBottom = 0,
}) => {
  const lastMessageRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const prevPaddingRef = useRef<number>(paddingBottom);

  // Handle immediate scrolling when messages change
  useEffect(() => {
    if (messages.length > 0 && lastMessageRef.current && containerRef.current) {
      const lastMessage = lastMessageRef.current;
      const container = containerRef.current;

      // Calculate the scroll position to show the start of the last message
      const scrollPosition = lastMessage.offsetTop - container.offsetTop;

      // Use instant scrolling (no animation)
      container.scrollTop = scrollPosition;
    }
  }, [messages]);

  // Handle padding changes separately
  useEffect(() => {
    // Only update if padding has changed
    if (paddingBottom !== prevPaddingRef.current) {
      prevPaddingRef.current = paddingBottom;
    }
  }, [paddingBottom]);

  return (
    <Box
      ref={containerRef}
      className={styles.messageList}
      style={{
        marginBottom: `${paddingBottom}px`,
        position: "relative", // Ensure stable positioning
      }}
    >
      {messages.map((message, index) => (
        <div
          ref={index === messages.length - 1 ? lastMessageRef : undefined}
          key={index}
        >
          <MessageItem message={message} />
        </div>
      ))}
    </Box>
  );
};
