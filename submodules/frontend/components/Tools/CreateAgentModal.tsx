import React, { useState } from "react";
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  Button,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  VStack,
  Switch,
  FormHelperText,
  Text,
  useToast,
  HStack,
} from "@chakra-ui/react";
import { ChevronLeftIcon } from "@chakra-ui/icons";
import styles from "./CreateAgentModal.module.css";

interface CreateAgentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAgentCreated: () => void;
  apiBaseUrl: string;
}

export const CreateAgentModal: React.FC<CreateAgentModalProps> = ({
  isOpen,
  onClose,
  onAgentCreated,
  apiBaseUrl,
}) => {
  const toast = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    human_readable_name: "",
    description: "",
    mcp_server_url: "",
    is_enabled: true,
  });

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSwitchChange = () => {
    setFormData((prev) => ({
      ...prev,
      is_enabled: !prev.is_enabled,
    }));
  };

  const validateForm = () => {
    const requiredFields = [
      "human_readable_name",
      "description",
      "mcp_server_url",
    ];

    const missingFields = requiredFields.filter(
      (field) => !formData[field as keyof typeof formData]
    );

    if (missingFields.length > 0) {
      toast({
        title: "Missing required fields",
        description: `Please fill in all required fields.`,
        status: "error",
        duration: 5000,
        isClosable: true,
        position: "top-right",
      });
      return false;
    }

    return true;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setIsSubmitting(true);

    try {
      // Call the backend API to create the agent
      const response = await fetch(`${apiBaseUrl}/agents/create`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to create agent");
      }

      toast({
        title: "Agent created",
        description: `Agent "${formData.human_readable_name}" has been created successfully.`,
        status: "success",
        duration: 5000,
        isClosable: true,
        position: "top-right",
      });

      onAgentCreated();

      // Reset form
      setFormData({
        human_readable_name: "",
        description: "",
        mcp_server_url: "",
        is_enabled: true,
      });

      // Close the modal
      onClose();
    } catch (error) {
      console.error("Error creating agent:", error);
      toast({
        title: "Error creating agent",
        description:
          error instanceof Error
            ? error.message
            : "There was an error creating the agent. Please try again.",
        status: "error",
        duration: 5000,
        isClosable: true,
        position: "top-right",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl">
      <ModalOverlay className={styles.overlay} />
      <ModalContent className={styles.modalContent}>
        <ModalHeader className={styles.modalHeader}>
          <Text>Create New Agent</Text>
          <Button
            leftIcon={<ChevronLeftIcon />}
            onClick={onClose}
            className={styles.backButton}
            variant="ghost"
            size="sm"
          >
            Back
          </Button>
        </ModalHeader>

        <ModalBody className={styles.modalBody}>
          <Text className={styles.createAgentDescription}>
            Create a new agent by connecting to an MCP server. The agent&apos;s
            tools will be imported automatically.
          </Text>

          <VStack spacing={4} align="stretch">
            <FormControl isRequired>
              <FormLabel className={styles.formLabel}>Agent Name</FormLabel>
              <Input
                name="human_readable_name"
                value={formData.human_readable_name}
                onChange={handleChange}
                placeholder="e.g., WebSearch Agent"
                className={styles.input}
                size="sm"
              />
            </FormControl>

            <FormControl isRequired>
              <FormLabel className={styles.formLabel}>Description</FormLabel>
              <Textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                placeholder="Describe what this agent does..."
                className={styles.textarea}
                rows={2}
                size="sm"
              />
            </FormControl>

            <FormControl isRequired>
              <FormLabel className={styles.formLabel}>MCP Server URL</FormLabel>
              <Input
                name="mcp_server_url"
                value={formData.mcp_server_url}
                onChange={handleChange}
                placeholder="e.g., https://example.com/sse"
                className={styles.input}
                size="sm"
              />
              <FormHelperText className={styles.helperText}>
                Remote URL to connect to (must be a Server-Sent Events endpoint)
              </FormHelperText>
            </FormControl>
          </VStack>
        </ModalBody>

        <ModalFooter className={styles.modalFooter}>
          <HStack spacing={3}>
            <Button
              variant="outline"
              onClick={onClose}
              className={styles.cancelButton}
              size="sm"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              isLoading={isSubmitting}
              loadingText="Creating..."
              className={styles.createButton}
              size="sm"
            >
              Create Agent
            </Button>
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
