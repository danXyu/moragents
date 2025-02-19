import { ChatMessage, UserMessage } from "@/services/types";
import { DEFAULT_CONVERSATION_ID } from "@/services/LocalStorage/config";
import { getMessagesHistory } from "@/services/ChatManagement/storage";
import { addMessageToHistory } from "@/services/ChatManagement/messages";
import { getOrCreateConversation } from "@/services/ChatManagement/storage";
import { getStorageData } from "../LocalStorage/core";
import { saveStorageData } from "../LocalStorage/core";

/**
 * Send a message to the backend API and handle the response
 */
export const writeMessage = async (
  message: string,
  backendClient: any,
  chainId: number,
  address: string,
  conversationId: string = DEFAULT_CONVERSATION_ID
): Promise<ChatMessage[]> => {
  const convId = getOrCreateConversation(conversationId);
  const currentHistory = getMessagesHistory(convId);

  const newMessage: UserMessage = {
    role: "user",
    content: message,
    timestamp: Date.now(),
  };

  // Add user message to local storage
  addMessageToHistory(newMessage, convId);

  try {
    // Send message along with conversation history to backend
    const response = await backendClient.post("/api/v1/chat", {
      prompt: {
        role: "user",
        content: message,
      },
      chat_history: currentHistory,
      chain_id: String(chainId),
      wallet_address: address,
    });

    // Process response
    if (response.data) {
      // Add assistant's response to local storage
      addMessageToHistory(response.data, convId);
    }

    // Return the updated messages after API response is processed
    return getMessagesHistory(convId);
  } catch (error) {
    console.error("Failed to send message:", error);
    throw error;
  }
};

/**
 * Upload a file to the chat API
 * Note: This is a placeholder function - implement according to your API
 */
export const uploadFile = async (
  file: File,
  backendClient: any,
  chainId: number,
  address: string,
  conversationId: string = DEFAULT_CONVERSATION_ID
): Promise<ChatMessage[]> => {
  const convId = getOrCreateConversation(conversationId);

  try {
    // Create form data
    const formData = new FormData();
    formData.append("file", file);
    formData.append("chain_id", String(chainId));
    formData.append("wallet_address", address);

    // Upload file to backend
    const response = await backendClient.post("/api/v1/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    // Process response
    if (response.data) {
      // Add system message about file upload
      addMessageToHistory(
        {
          role: "user",
          content: `Uploaded file: ${file.name}`,
          timestamp: Date.now(),
        },
        convId
      );

      // Add assistant's response if any
      if (response.data.message) {
        addMessageToHistory(response.data.message, convId);
      }
    }

    return getMessagesHistory(convId);
  } catch (error) {
    console.error("Failed to upload file:", error);
    throw error;
  }
};

/**
 * Generate a title for a conversation based on chat history
 * @param messages Array of chat messages to generate title from
 * @param backendClient Axios client instance
 * @param conversationId Optional conversation ID
 * @returns Generated title string
 */
export const generateConversationTitle = async (
  messages: ChatMessage[],
  backendClient: any,
  conversationId: string = DEFAULT_CONVERSATION_ID
): Promise<string> => {
  try {
    const response = await backendClient.post("/api/v1/generate-title", {
      chat_history: messages,
      conversation_id: conversationId,
    });

    if (response.data && response.data.title) {
      const data = getStorageData();
      data.conversations[conversationId].name = response.data.title;
      saveStorageData(data);

      return response.data.title;
    }

    throw new Error("No title returned from API");
  } catch (error) {
    console.error("Failed to generate conversation title:", error);
    throw error;
  }
};
