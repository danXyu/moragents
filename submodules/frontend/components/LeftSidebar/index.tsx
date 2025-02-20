import React, { FC, useEffect, useState, useRef } from "react";
import {
  Box,
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  Text,
  VStack,
  Popover,
  PopoverContent,
  PopoverBody,
  PopoverArrow,
  PopoverTrigger,
} from "@chakra-ui/react";
import {
  IconChevronLeft,
  IconChevronRight,
  IconPlus,
  IconSearch,
  IconRefresh,
  IconTrash,
} from "@tabler/icons-react";
import { useRouter } from "next/router";
import { ProfileMenu } from "./ProfileMenu";
import styles from "./index.module.css";

// Import from our new modular services
import { useChatContext } from "@/contexts/chat/useChatContext";
import {
  getAllConversations,
  createNewConversation,
  clearMessagesHistory,
} from "@/contexts/chat";
import { Conversation } from "@/services/types";

// Add keyframes for blink animation
const blinkKeyframes = `
  @keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
  }
`;

export type LeftSidebarProps = {
  isSidebarOpen: boolean;
  onToggleSidebar: (open: boolean) => void;
};

export const LeftSidebar: FC<LeftSidebarProps> = ({
  isSidebarOpen,
  onToggleSidebar,
}) => {
  // Add keyframes to document head once
  useEffect(() => {
    const styleElement = document.createElement("style");
    styleElement.innerHTML = blinkKeyframes;
    document.head.appendChild(styleElement);

    return () => {
      document.head.removeChild(styleElement);
    };
  }, []);

  // Use our centralized chat context
  const { state, setCurrentConversation, deleteChat, refreshMessages } =
    useChatContext();
  const { currentConversationId, conversationTitles } = state;

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState("llama3.2:3b");
  const router = useRouter();
  const ToggleIcon = isSidebarOpen ? IconChevronLeft : IconChevronRight;

  // Animation state (moved outside of component to prevent nesting issues)
  const [animatingConversations, setAnimatingConversations] = useState<{
    [id: string]: { text: string; typing: boolean };
  }>({});

  const modelOptions = [{ value: "llama3.3:70b", label: "Llama 3.3 (70B)" }];

  const fetchConversations = () => {
    try {
      const conversationsData = getAllConversations();

      // Merge conversation data with titles from context
      const updatedConversations = conversationsData.map((conv) => {
        const newName = conversationTitles[conv.id] || conv.name;

        // Set up animation if the name has changed
        if (newName !== conv.name && conv.name !== "New Conversation") {
          setAnimatingConversations((prev) => ({
            ...prev,
            [conv.id]: { text: newName, typing: true },
          }));

          // Auto-clear typing after animation completes
          setTimeout(() => {
            setAnimatingConversations((prev) => ({
              ...prev,
              [conv.id]: { text: newName, typing: false },
            }));
          }, newName.length * 30 + 100);
        }

        return {
          ...conv,
          name: newName,
        };
      });

      setConversations(updatedConversations);
    } catch (error) {
      console.error("Failed to fetch conversations:", error);
    }
  };

  const handleCreateNewConversation = async () => {
    setIsLoading(true);
    try {
      const newConversationId = createNewConversation();
      fetchConversations();
      setCurrentConversation(newConversationId);
    } catch (error) {
      console.error("Failed to create new conversation:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteConversation = async (conversationId: string) => {
    try {
      await deleteChat(conversationId);
      fetchConversations();
      if (conversationId === currentConversationId) {
        setCurrentConversation("default");
      }
    } catch (error) {
      console.error("Failed to delete conversation:", error);
    }
  };

  const handleClearChatHistory = async () => {
    try {
      clearMessagesHistory(currentConversationId);
      router.reload();
    } catch (error) {
      console.error("Failed to clear chat history:", error);
    }
  };

  // Watch for changes in conversation titles and current conversation
  useEffect(() => {
    fetchConversations();
  }, [conversationTitles, currentConversationId]);

  // Poll for updates to ensure we catch title changes
  useEffect(() => {
    const intervalId = setInterval(() => {
      refreshMessages();
    }, 2000);

    return () => clearInterval(intervalId);
  }, [refreshMessages]);

  const filteredConversations = conversations.filter(
    (conv) =>
      conv?.name
        ?.toLowerCase?.()
        ?.includes(searchQuery?.toLowerCase?.() ?? "") ?? false
  );

  return (
    <div
      className={`${styles.sidebarContainer} ${
        !isSidebarOpen ? styles.collapsed : ""
      }`}
    >
      <div className={styles.sidebar}>
        <div className={styles.container}>
          <div className={styles.searchContainer}>
            <InputGroup>
              <InputLeftElement>
                <IconSearch className={styles.searchIcon} size={16} />
              </InputLeftElement>
              <Input
                placeholder="Search chats..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={styles.searchInput}
              />
            </InputGroup>
            <button
              className={styles.newChatIcon}
              onClick={handleCreateNewConversation}
              disabled={isLoading}
            >
              <IconPlus size={16} />
            </button>
          </div>

          <div className={styles.mainContent}>
            {filteredConversations.map((conversation) => {
              // Get animation state for this conversation
              const isTyping =
                animatingConversations[conversation.id]?.typing || false;

              return (
                <div
                  key={conversation.id}
                  className={`${styles.conversationItem} ${
                    currentConversationId === conversation.id
                      ? styles.conversationActive
                      : ""
                  }`}
                  onClick={() => setCurrentConversation(conversation.id)}
                >
                  {/* No component wrapper, just direct styling on the span */}
                  <span
                    className={styles.conversationName}
                    style={{
                      color: isTyping ? "#1ed760" : undefined,
                    }}
                  >
                    {conversation.name}
                    {isTyping && (
                      <span
                        style={{
                          display: "inline-block",
                          marginLeft: "1px",
                          animation: "blink 0.7s infinite",
                          fontWeight: "bold",
                        }}
                      >
                        |
                      </span>
                    )}
                  </span>
                  <div className={styles.buttonGroup}>
                    {conversation.id === "default" ? (
                      <button
                        className={styles.resetButton}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleClearChatHistory();
                        }}
                      >
                        <IconRefresh size={16} />
                      </button>
                    ) : (
                      <button
                        className={styles.deleteButton}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteConversation(conversation.id);
                        }}
                      >
                        <IconTrash size={16} />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          <Box width="100%" mb={1}>
            <Popover
              placement="top"
              trigger="hover"
              openDelay={0}
              closeDelay={0}
            >
              <PopoverTrigger>
                <Box
                  as="button"
                  width="100%"
                  bg="rgba(255, 255, 255, 0.05)"
                  color="white"
                  borderColor="rgba(255, 255, 255, 0.1)"
                  borderWidth="1px"
                  borderRadius="8px"
                  fontSize="15px"
                  fontWeight="500"
                  height="40px"
                  opacity="0.8"
                  cursor="pointer"
                  _hover={{ bg: "rgba(255, 255, 255, 0.08)" }}
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                >
                  Create or Trade Tokenized Agents
                </Box>
              </PopoverTrigger>
              <PopoverContent
                bg="#080808"
                borderColor="rgba(255, 255, 255, 0.1)"
                boxShadow="0 4px 12px rgba(0, 0, 0, 0.2)"
                color="white"
                fontSize="14px"
                maxWidth="380px"
                _focus={{
                  boxShadow: "none",
                  outline: "none",
                }}
              >
                <PopoverArrow bg="#080808" />
                <PopoverBody p={4}>
                  All of the functionality in moragents can be leveraged in your
                  own custom agents that can trade for you, post on X, and more.
                  Agent tokenization is coming soon.
                </PopoverBody>
              </PopoverContent>
            </Popover>
          </Box>

          <div className={styles.footer}>
            <VStack spacing={4} align="stretch" width="100%">
              <Box width="100%">
                <Box className={styles.modelSelection}>
                  <Text className={styles.modelLabel}>Model:</Text>
                  <Select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className={styles.modelSelect}
                  >
                    {modelOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </Select>
                </Box>
                <div className={styles.comingSoonContainer}>
                  <Text className={styles.costInfo}>Coming soon</Text>
                  <Text className={styles.modelNote}>
                    Stake your Morpheus tokens to access more powerful models
                    and leverage builder keys to automatically enable advanced
                    agents.
                  </Text>
                </div>
              </Box>
            </VStack>

            <ProfileMenu />
          </div>
        </div>
      </div>

      <button
        className={styles.toggleButton}
        onClick={() => onToggleSidebar(!isSidebarOpen)}
        aria-label="Toggle sidebar"
      >
        <ToggleIcon size={20} />
      </button>
    </div>
  );
};
