import React, { FC, useState, useEffect, useRef } from "react";
import {
  Textarea,
  InputGroup,
  InputLeftAddon,
  InputRightAddon,
  IconButton,
  Box,
  VStack,
  Text,
  useMediaQuery,
} from "@chakra-ui/react";
import { AttachmentIcon } from "@chakra-ui/icons";
import { SendIcon } from "../CustomIcon/SendIcon";
import PrefilledOptions from "./PrefilledOptions";
import styles from "./index.module.css";
import API_BASE_URL from "../../config";

type Command = {
  command: string;
  description: string;
  name: string;
};

type ChatInputProps = {
  onSubmit: (message: string, file: File | null) => Promise<void>;
  disabled: boolean;
  hasMessages?: boolean;
  isSidebarOpen?: boolean;
  onPrefillOptionsHeightChange?: (height: number) => void;
};

export const ChatInput: FC<ChatInputProps> = ({
  onSubmit,
  disabled,
  hasMessages = false,
  isSidebarOpen = false,
  onPrefillOptionsHeightChange,
}) => {
  const [message, setMessage] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [commands, setCommands] = useState<Command[]>([]);
  const [showCommands, setShowCommands] = useState(false);
  const [selectedCommandIndex, setSelectedCommandIndex] = useState(0);
  const [dropdownPosition, setDropdownPosition] = useState({
    top: 0,
    left: 0,
    width: 0,
  });
  const [isMobile] = useMediaQuery("(max-width: 768px)");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const inputGroupRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const commandsRef = useRef<HTMLDivElement>(null);
  const prefillOptionsRef = useRef<HTMLDivElement>(null);
  const updateTimeoutRef = useRef<number | null>(null);

  // Function to directly update height - no state management
  const updatePrefillHeight = (height: number) => {
    if (onPrefillOptionsHeightChange) {
      // Clear any pending updates
      if (updateTimeoutRef.current) {
        window.clearTimeout(updateTimeoutRef.current);
        updateTimeoutRef.current = null;
      }

      // Immediate update with no delay
      onPrefillOptionsHeightChange(height);
    }
  };

  // Immediate update whenever prefill options expand/collapse
  const handlePrefillExpandChange = (
    isExpanded: boolean,
    selectedGroup: string | null
  ) => {
    if (!isExpanded) {
      // Immediate collapse to 0 height
      updatePrefillHeight(0);
      return;
    }

    // For expansion, force immediate update via direct DOM measurement
    if (prefillOptionsRef.current) {
      const directMeasurement = () => {
        if (!prefillOptionsRef.current) return;
        const prefilledEl = prefillOptionsRef.current.firstChild as HTMLElement;
        if (!prefilledEl) return;

        const height = prefilledEl.getBoundingClientRect().height;
        if (height > 0) {
          updatePrefillHeight(height);
        } else {
          // If height is 0, try again in 5ms (aggressive retry for immediate update)
          updateTimeoutRef.current = window.setTimeout(directMeasurement, 5);
        }
      };

      // Execute measurement immediately
      directMeasurement();
    }
  };

  // Fetch commands
  useEffect(() => {
    fetch(`${API_BASE_URL}/agents/commands`)
      .then((res) => res.json())
      .then((data) => setCommands(data.commands))
      .catch((error) => console.error("Error fetching commands:", error));

    // Clean up any pending updates on unmount
    return () => {
      if (updateTimeoutRef.current) {
        window.clearTimeout(updateTimeoutRef.current);
      }
    };
  }, []);

  // Set up AGGRESSIVE DOM monitor to catch any height changes
  useEffect(() => {
    if (!prefillOptionsRef.current || !onPrefillOptionsHeightChange) return;

    let rafId: number;
    let lastHeight = 0;

    // Check for height changes on every animation frame
    const checkHeight = () => {
      if (prefillOptionsRef.current) {
        const prefilledEl = prefillOptionsRef.current.firstChild as HTMLElement;
        if (prefilledEl) {
          const currentHeight = prefilledEl.getBoundingClientRect().height;
          if (currentHeight > 0 && currentHeight !== lastHeight) {
            lastHeight = currentHeight;
            updatePrefillHeight(currentHeight);
          }
        }
      }
      rafId = requestAnimationFrame(checkHeight);
    };

    // Start monitoring
    rafId = requestAnimationFrame(checkHeight);

    return () => {
      cancelAnimationFrame(rafId);
    };
  }, [onPrefillOptionsHeightChange]);

  // Update dropdown position when message changes
  useEffect(() => {
    if (inputGroupRef.current && message.startsWith("/")) {
      const rect = inputGroupRef.current.getBoundingClientRect();
      const mobileOffset = isMobile ? 20 : 400;
      setDropdownPosition({
        top: rect.top,
        left: rect.left - mobileOffset,
        width: rect.width,
      });
    }
  }, [message, isMobile]);

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

  // Scroll to selected command
  useEffect(() => {
    if (commandsRef.current && showCommands) {
      const selectedElement = commandsRef.current.querySelector(
        `[data-index="${selectedCommandIndex}"]`
      );
      if (selectedElement) {
        selectedElement.scrollIntoView({
          block: "center",
          behavior: "smooth",
        });
      }
    }
  }, [selectedCommandIndex, showCommands]);

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
    <>
      {showCommands && (
        <Box
          ref={commandsRef}
          position="fixed"
          top={`${dropdownPosition.top - (isMobile ? 160 : 210)}px`}
          left={`${dropdownPosition.left}px`}
          right={0}
          mx="auto"
          width={`${dropdownPosition.width}px`}
          bg="#353936"
          borderRadius="8px"
          boxShadow="0 4px 12px rgba(0, 0, 0, 0.3)"
          maxH={isMobile ? "160px" : "200px"}
          overflowY="auto"
          border="1px solid #454945"
          zIndex={1000}
          sx={{
            "&::-webkit-scrollbar": {
              width: "8px",
            },
            "&::-webkit-scrollbar-track": {
              background: "#2A2E2A",
            },
            "&::-webkit-scrollbar-thumb": {
              background: "#454945",
              borderRadius: "4px",
            },
          }}
        >
          <VStack spacing={0} align="stretch">
            {filteredCommands.map((cmd, index) => (
              <Box
                key={cmd.command}
                data-index={index}
                px={3}
                py={2}
                bg={index === selectedCommandIndex ? "#454945" : "transparent"}
                _hover={{ bg: "#404540" }}
                cursor="pointer"
                onClick={() => handleCommandSelect(cmd)}
                transition="background-color 0.2s"
                borderBottom="1px solid #454945"
                _last={{ borderBottom: "none" }}
              >
                <Text
                  fontWeight="bold"
                  fontSize={isMobile ? "xs" : "sm"}
                  color="#59f886"
                >
                  /{cmd.command}
                </Text>
                <Text fontSize={isMobile ? "2xs" : "xs"} color="#A0A0A0">
                  {cmd.name} - {cmd.description}
                </Text>
              </Box>
            ))}
          </VStack>
        </Box>
      )}

      <div className={styles.container}>
        <div ref={prefillOptionsRef}>
          <PrefilledOptions
            onSelect={handlePrefilledSelect}
            isSidebarOpen={isSidebarOpen}
            onExpandChange={handlePrefillExpandChange}
          />
        </div>
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
                  className={
                    isSubmitting || disabled ? styles.disabledIcon : ""
                  }
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
              placeholder="Start typing or press / for commands"
              rows={1}
              resize="none"
              fontSize="14px"
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
      </div>
    </>
  );
};
