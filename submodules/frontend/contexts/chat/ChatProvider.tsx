import React, {
  useReducer,
  useCallback,
  useEffect,
  ReactNode,
  useRef,
} from "react";
import { useChainId, useAccount } from "wagmi";
import { ChatMessage } from "@/services/types";
import { getHttpClient } from "@/services/constants";
import {
  writeMessage,
  uploadFile,
  generateConversationTitle,
} from "@/services/ChatManagement/api";
import { getMessagesHistory } from "@/services/ChatManagement/storage";
import { getStorageData } from "@/services/LocalStorage/core";
import { deleteConversation } from "@/services/ChatManagement/conversations";
import { chatReducer, initialState } from "@/contexts/chat/ChatReducer";
import ChatContext from "@/contexts/chat/ChatContext";

interface ChatProviderProps {
  children: ReactNode;
}

export const ChatProvider = ({ children }: ChatProviderProps) => {
  const [state, dispatch] = useReducer(chatReducer, initialState);
  const chainId = useChainId();
  const { address } = useAccount();

  // Track conversations that have already attempted title generation
  const titleGenerationAttempted = useRef<Set<string>>(new Set());
  // Track active title generation requests to prevent duplicates
  const pendingTitleGeneration = useRef<Set<string>>(new Set());

  // Load initial messages and titles for default conversation
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const messages = getMessagesHistory("default");
        dispatch({
          type: "SET_MESSAGES",
          payload: { conversationId: "default", messages },
        });

        // Load conversation titles from localStorage
        const data = getStorageData();
        const titles: Record<string, string> = {};

        Object.keys(data.conversations).forEach((convId) => {
          if (data.conversations[convId].name) {
            titles[convId] = data.conversations[convId].name;
            // Mark conversations with custom titles as already having attempted title generation
            if (data.conversations[convId].name !== "New Conversation") {
              titleGenerationAttempted.current.add(convId);
            }
          }
        });

        // Set all titles at once
        Object.entries(titles).forEach(([convId, title]) => {
          dispatch({
            type: "SET_CONVERSATION_TITLE",
            payload: { conversationId: convId, title },
          });
        });
      } catch (error) {
        console.error("Failed to load initial data:", error);
      }
    };

    loadInitialData();
  }, []);

  // Set current conversation and load its messages
  const setCurrentConversation = useCallback(
    async (conversationId: string) => {
      dispatch({ type: "SET_CURRENT_CONVERSATION", payload: conversationId });

      // Load messages if not already loaded
      if (!state.messages[conversationId]) {
        dispatch({ type: "SET_LOADING", payload: true });
        try {
          const messages = getMessagesHistory(conversationId);
          dispatch({
            type: "SET_MESSAGES",
            payload: { conversationId, messages },
          });

          // Load conversation title if available
          const data = getStorageData();
          if (data.conversations[conversationId]?.name) {
            dispatch({
              type: "SET_CONVERSATION_TITLE",
              payload: {
                conversationId,
                title: data.conversations[conversationId].name,
              },
            });

            // Mark as having a custom title if it's not the default
            if (
              data.conversations[conversationId].name !== "New Conversation"
            ) {
              titleGenerationAttempted.current.add(conversationId);
            }
          }
        } catch (error) {
          console.error(
            `Failed to load conversation ${conversationId}:`,
            error
          );
          dispatch({
            type: "SET_ERROR",
            payload: "Failed to load conversation",
          });
        } finally {
          dispatch({ type: "SET_LOADING", payload: false });
        }
      }
    },
    [state.messages]
  );

  // Refresh messages and title for current conversation
  const refreshMessages = useCallback(async () => {
    const { currentConversationId } = state;
    dispatch({ type: "SET_LOADING", payload: true });

    try {
      // Get latest messages
      const messages = getMessagesHistory(currentConversationId);
      dispatch({
        type: "SET_MESSAGES",
        payload: { conversationId: currentConversationId, messages },
      });

      // Get latest title
      const data = getStorageData();
      if (data.conversations[currentConversationId]?.name) {
        dispatch({
          type: "SET_CONVERSATION_TITLE",
          payload: {
            conversationId: currentConversationId,
            title: data.conversations[currentConversationId].name,
          },
        });
      }

      // After receiving a response, check if we need to generate a title
      // but ensure we don't trigger this logic repeatedly for the same conversation
      maybeGenerateTitle(currentConversationId, messages);
    } catch (error) {
      console.error("Failed to refresh conversation data:", error);
      dispatch({
        type: "SET_ERROR",
        payload: "Failed to refresh conversation",
      });
    } finally {
      dispatch({ type: "SET_LOADING", payload: false });
    }
  }, [state.currentConversationId]);

  // Refresh all conversation titles from storage
  const refreshAllTitles = useCallback(async () => {
    dispatch({ type: "SET_LOADING", payload: true });

    try {
      // Get storage data which contains all conversations
      const data = getStorageData();

      // For each conversation
      Object.keys(data.conversations).forEach((conversationId) => {
        // Update title if one exists
        if (data.conversations[conversationId]?.name) {
          dispatch({
            type: "SET_CONVERSATION_TITLE",
            payload: {
              conversationId,
              title: data.conversations[conversationId].name,
            },
          });
        }
      });
    } catch (error) {
      console.error("Failed to refresh all conversation titles:", error);
      dispatch({
        type: "SET_ERROR",
        payload: "Failed to refresh conversation titles",
      });
    } finally {
      dispatch({ type: "SET_LOADING", payload: false });
    }
  }, []);

  // Safe title generation that avoids infinite loops
  const maybeGenerateTitle = useCallback(
    (conversationId: string, messages: ChatMessage[]) => {
      // Skip if we've already attempted to generate a title for this conversation
      if (titleGenerationAttempted.current.has(conversationId)) return;

      // Skip if there's a pending title generation request
      if (pendingTitleGeneration.current.has(conversationId)) return;

      // Only generate title if there are enough messages
      // and at least one is from the assistant (indicating a response occurred)
      const hasAgentResponse = messages.some((m) => m.role === "assistant");
      const hasEnoughMessages = messages.length >= 5;
      const currentTitle = state.conversationTitles[conversationId];
      const hasDefaultTitle =
        currentTitle === "New Conversation" || !currentTitle;

      if (hasEnoughMessages && hasAgentResponse && hasDefaultTitle) {
        // Mark as attempted regardless of outcome
        titleGenerationAttempted.current.add(conversationId);
        pendingTitleGeneration.current.add(conversationId);

        // Run title generation outside the current execution context
        setTimeout(() => {
          generateConversationTitle(messages, getHttpClient(), conversationId)
            .then((title) => {
              if (title) {
                dispatch({
                  type: "SET_CONVERSATION_TITLE",
                  payload: { conversationId, title },
                });
              }
            })
            .catch((error) => {
              console.error("Failed to generate conversation title:", error);
            })
            .finally(() => {
              // Clean up pending request tracking
              pendingTitleGeneration.current.delete(conversationId);
            });
        }, 0);
      }
    },
    [state.conversationTitles]
  );

  // Send message or file
  const sendMessage = useCallback(
    async (
      message: string,
      file: File | null,
      useResearch: boolean = false
    ) => {
      if (!message && !file) return;

      const { currentConversationId } = state;
      dispatch({ type: "SET_LOADING", payload: true });

      try {
        if (!file) {
          // Text message flow
          // Add optimistic user message
          const optimisticMessage: ChatMessage = {
            role: "user",
            content: message,
            timestamp: Date.now(),
          };

          // Update UI immediately
          dispatch({
            type: "ADD_OPTIMISTIC_MESSAGE",
            payload: {
              conversationId: currentConversationId,
              message: optimisticMessage,
            },
          });

          // Send to server
          await writeMessage(
            message,
            getHttpClient(),
            chainId,
            address || "",
            currentConversationId,
            useResearch
          );
        } else {
          // File upload flow
          await uploadFile(file, getHttpClient(), currentConversationId);
        }

        // Refresh messages to get server response
        await refreshMessages();
      } catch (error) {
        console.error("Failed to send message:", error);
        dispatch({ type: "SET_ERROR", payload: "Failed to send message" });
      } finally {
        dispatch({ type: "SET_LOADING", payload: false });
      }
    },
    [state.currentConversationId, chainId, address, refreshMessages]
  );

  // Delete conversation
  const deleteChat = useCallback(
    async (conversationId: string) => {
      dispatch({ type: "SET_LOADING", payload: true });

      try {
        deleteConversation(conversationId);

        // Remove from title generation tracking
        titleGenerationAttempted.current.delete(conversationId);
        pendingTitleGeneration.current.delete(conversationId);

        // If current conversation was deleted, switch to default
        if (conversationId === state.currentConversationId) {
          dispatch({ type: "SET_CURRENT_CONVERSATION", payload: "default" });
          const defaultMessages = getMessagesHistory("default");
          dispatch({
            type: "SET_MESSAGES",
            payload: { conversationId: "default", messages: defaultMessages },
          });
        }
      } catch (error) {
        console.error("Failed to delete conversation:", error);
        dispatch({
          type: "SET_ERROR",
          payload: "Failed to delete conversation",
        });
      } finally {
        dispatch({ type: "SET_LOADING", payload: false });
      }
    },
    [state.currentConversationId]
  );

  // Context value
  const value = {
    state,
    setCurrentConversation,
    sendMessage,
    refreshMessages,
    refreshAllTitles,
    deleteChat,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
};
