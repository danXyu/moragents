import React, { FC, useState, useEffect, useRef } from "react";
import {
  Textarea,
  InputGroup,
  InputLeftAddon,
  InputRightAddon,
  IconButton,
  useMediaQuery,
} from "@chakra-ui/react";
import { AttachmentIcon } from "@chakra-ui/icons";
import { SendIcon } from "../CustomIcon/SendIcon";
import { Command } from "./Commands";
import { CommandsPortal } from "./CommandsPortal";
import styles from "./index.module.css";
import API_BASE_URL from "../../config";

type ChatInputProps = {
  onSubmit: (message: string, file: File | null) => Promise<void>;
  disabled: boolean;
  isSidebarOpen: boolean;
};

export const ChatInput: FC<ChatInputProps> = ({
  onSubmit,
  disabled,
  isSidebarOpen,
}) => {
  const [message, setMessage] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [commands, setCommands] = useState<Command[]>([]);
  const [showCommands, setShowCommands] = useState(false);
  const [selectedCommandIndex, setSelectedCommandIndex] = useState(0);
  const [isMobile] = useMediaQuery("(max-width: 768px)");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const inputGroupRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Add this useEffect to prevent focus zoom on mobile
  useEffect(() => {
    // Add meta viewport tag to prevent zoom
    const viewportMeta = document.createElement("meta");
    viewportMeta.name = "viewport";
    viewportMeta.content =
      "width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no";

    // Check if there's already a viewport meta tag
    const existingMeta = document.querySelector('meta[name="viewport"]');

    if (existingMeta) {
      // Update existing meta tag
      existingMeta.setAttribute(
        "content",
        "width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no"
      );
    } else {
      // Add new meta tag
      document.head.appendChild(viewportMeta);
    }

    // Optional cleanup
    return () => {
      if (!existingMeta && viewportMeta.parentNode) {
        document.head.removeChild(viewportMeta);
      }
    };
  }, []);

  // Fetch commands
  useEffect(() => {
    fetch(`${API_BASE_URL}/agents/commands`)
      .then((res) => res.json())
      .then((data) => setCommands(data.commands))
      .catch((error) => console.error("Error fetching commands:", error));
  }, []);

  // Filter commands based on input
  const filteredCommands = message.startsWith("/")
    ? commands.filter((cmd) =>
        cmd.command.toLowerCase().includes(message.slice(1).toLowerCase())
      )
    : [];

  // Show/hide commands dropdown based on input
  useEffect(() => {
    setShowCommands(message.startsWith("/") && filteredCommands.length > 0);
    setSelectedCommandIndex(0);
  }, [message, filteredCommands.length]);

  const handleCommandSelect = (command: Command) => {
    setMessage(`/${command.command} `);
    setShowCommands(false);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (showCommands) {
      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setSelectedCommandIndex((prev) =>
            Math.min(prev + 1, filteredCommands.length - 1)
          );
          break;
        case "ArrowUp":
          e.preventDefault();
          setSelectedCommandIndex((prev) => Math.max(prev - 1, 0));
          break;
        case "Tab":
        case "Enter":
          e.preventDefault();
          handleCommandSelect(filteredCommands[selectedCommandIndex]);
          break;
        case "Escape":
          setShowCommands(false);
          break;
      }
    } else if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const agentSupportsFileUploads = !isMobile;

  const handleSubmit = async () => {
    if ((!message && !file) || isSubmitting || disabled) return;

    try {
      setIsSubmitting(true);
      const messageToSend = message;
      const fileToSend = file;

      // Clear input immediately to improve UX
      setMessage("");
      setFile(null);

      // Then submit the message
      await onSubmit(messageToSend, fileToSend);
    } catch (error) {
      console.error("Error submitting message:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      {showCommands && (
        <CommandsPortal
          commands={filteredCommands}
          selectedIndex={selectedCommandIndex}
          onSelect={handleCommandSelect}
          isSidebarOpen={isSidebarOpen}
        />
      )}

      <div className={styles.flexContainer}>
        <InputGroup ref={inputGroupRef} className={styles.inputGroup}>
          {agentSupportsFileUploads && (
            <InputLeftAddon className={styles.fileAddon}>
              <input
                type="file"
                className={styles.hiddenInput}
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                disabled={isSubmitting || disabled}
              />
              <IconButton
                aria-label="Attach file"
                icon={
                  <AttachmentIcon
                    width={isMobile ? "16px" : "20px"}
                    height={isMobile ? "16px" : "20px"}
                  />
                }
                className={isSubmitting || disabled ? styles.disabledIcon : ""}
                disabled={isSubmitting || disabled}
                onClick={() =>
                  document
                    .querySelector('input[type="file"]')
                    ?.dispatchEvent(new MouseEvent("click"))
                }
              />
            </InputLeftAddon>
          )}
          <Textarea
            ref={inputRef}
            className={styles.messageInput}
            onKeyDown={handleKeyDown}
            disabled={isSubmitting || disabled || file !== null}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder={
              file
                ? "Click the arrow to process your file"
                : "Start typing or press / for commands"
            }
            rows={1}
            resize="none"
            overflow="hidden"
          />
          <InputRightAddon className={styles.rightAddon}>
            <IconButton
              className={styles.sendButton}
              disabled={isSubmitting || disabled || (!message && !file)}
              aria-label="Send"
              onClick={handleSubmit}
              icon={
                <SendIcon
                  width={isMobile ? "20px" : "24px"}
                  height={isMobile ? "20px" : "24px"}
                />
              }
            />
          </InputRightAddon>
        </InputGroup>
      </div>
    </>
  );
};
