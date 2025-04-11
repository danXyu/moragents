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
  FormHelperText,
  Text,
  useToast,
  HStack,
  Box,
  Tooltip,
  Switch,
  FormErrorMessage,
} from "@chakra-ui/react";
import { ChevronLeftIcon, InfoIcon } from "@chakra-ui/icons";
import styles from "./CreateAgentModal.module.css";

interface CreateAgentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAgentCreated: () => void;
  apiBaseUrl: string;
}

interface FormErrors {
  human_readable_name?: string;
  description?: string;
  mcp_server_url?: string;
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

  const [errors, setErrors] = useState<FormErrors>({});

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    // Clear error for this field when user types
    if (errors[name as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const handleSwitchChange = () => {
    setFormData((prev) => ({
      ...prev,
      is_enabled: !prev.is_enabled,
    }));
  };

  const validateForm = () => {
    const newErrors: FormErrors = {};
    let isValid = true;

    // Validate agent name
    if (!formData.human_readable_name.trim()) {
      newErrors.human_readable_name = "Agent name is required";
      isValid = false;
    }

    // Validate description
    if (!formData.description.trim()) {
      newErrors.description = "Description is required";
      isValid = false;
    }

    // Validate MCP server URL
    if (!formData.mcp_server_url.trim()) {
      newErrors.mcp_server_url = "MCP Server URL is required";
      isValid = false;
    } else if (!formData.mcp_server_url.startsWith("http")) {
      newErrors.mcp_server_url = "URL must start with http:// or https://";
      isValid = false;
    }

    setErrors(newErrors);
    return isValid;
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
        title: "Agent created successfully",
        description: `"${formData.human_readable_name}" has been added to your agents.`,
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
    <Modal isOpen={isOpen} onClose={onClose} size="xl" isCentered>
      <ModalOverlay className={styles.overlay} />
      <ModalContent className={styles.modalContent}>
        <ModalHeader className={styles.modalHeader}>
          <Text>Create New Agent</Text>
          <Button
            leftIcon={<ChevronLeftIcon boxSize={5} />}
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
            tools will be verified and imported automatically.
          </Text>

          <VStack spacing={2} align="stretch">
            <FormControl isRequired isInvalid={!!errors.human_readable_name}>
              <FormLabel className={styles.formLabel}>Agent Name</FormLabel>
              <Input
                name="human_readable_name"
                value={formData.human_readable_name}
                onChange={handleChange}
                placeholder="e.g., WebSearch Agent"
                className={styles.input}
                size="md"
              />
              {errors.human_readable_name && (
                <FormErrorMessage>
                  {errors.human_readable_name}
                </FormErrorMessage>
              )}
            </FormControl>

            <FormControl isRequired isInvalid={!!errors.description}>
              <FormLabel className={styles.formLabel}>Description</FormLabel>
              <Textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                placeholder="Describe what this agent does..."
                className={styles.textarea}
                rows={3}
                size="md"
              />
              {errors.description && (
                <FormErrorMessage>{errors.description}</FormErrorMessage>
              )}
            </FormControl>

            <FormControl isRequired isInvalid={!!errors.mcp_server_url}>
              <FormLabel className={styles.formLabel}>MCP Server URL</FormLabel>
              <Input
                name="mcp_server_url"
                value={formData.mcp_server_url}
                onChange={handleChange}
                placeholder="e.g., https://example.com/sse"
                className={styles.input}
                size="md"
              />
              {errors.mcp_server_url ? (
                <FormErrorMessage>{errors.mcp_server_url}</FormErrorMessage>
              ) : (
                <FormHelperText className={styles.helperText}>
                  Remote URL to connect to (must be a Server-Sent Events
                  endpoint)
                </FormHelperText>
              )}
            </FormControl>
          </VStack>
        </ModalBody>

        <ModalFooter className={styles.modalFooter}>
          <HStack spacing={3}>
            <Button
              variant="outline"
              onClick={onClose}
              className={styles.cancelButton}
              size="md"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              isLoading={isSubmitting}
              loadingText="Creating..."
              className={styles.createButton}
              size="md"
            >
              Create Agent
            </Button>
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
