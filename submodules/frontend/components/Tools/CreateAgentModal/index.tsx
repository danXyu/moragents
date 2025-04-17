import React, { useState } from "react";
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  Button,
  FormControl,
  Input,
  Textarea,
  FormHelperText,
  Text,
  useToast,
  Switch,
  FormErrorMessage,
} from "@chakra-ui/react";
import { ChevronLeftIcon } from "@chakra-ui/icons";
import styles from "./index.module.css";
import { MCPConfigForm } from "./MCPConfigForm";
import { FormErrors } from "./types";

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

  const [errors, setErrors] = useState<FormErrors>({});
  const [showUrlInput, setShowUrlInput] = useState(false);

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

  const handleConfigToggle = () => {
    setShowUrlInput(!showUrlInput);
    if (showUrlInput) {
      // Reset the URL field when switching to config mode
      setFormData((prev) => ({ ...prev, mcp_server_url: "" }));
    }
  };

  const handleUrlUpdate = (url: string) => {
    setFormData((prev) => ({ ...prev, mcp_server_url: url }));
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

  const isFormValid =
    formData.human_readable_name.trim() &&
    formData.description.trim() &&
    formData.mcp_server_url.trim();

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl" scrollBehavior="inside">
      <ModalOverlay className={styles.overlay} />
      <ModalContent className={styles.modalContent}>
        <ModalHeader className={styles.modalHeader}>
          <Button
            leftIcon={<ChevronLeftIcon boxSize={5} />}
            onClick={onClose}
            className={styles.backButton}
            variant="ghost"
            size="sm"
          >
            Back
          </Button>
          <Text className={styles.headerTitle}>Create New Agent</Text>
          <Button
            onClick={handleSubmit}
            isLoading={isSubmitting}
            loadingText="Creating..."
            className={styles.createButton}
            size="md"
            isDisabled={!isFormValid}
          >
            Create
          </Button>
        </ModalHeader>

        <ModalBody className={styles.modalBody}>
          <Text className={styles.createAgentDescription}>
            Create a new agent by connecting to an MCP server. The agent&apos;s
            tools will be verified and imported automatically.
          </Text>

          <div className={styles.formContainer}>
            <div className={styles.formRow}>
              <div className={styles.labelColumn}>
                <label className={styles.formLabel}>Agent Name</label>
              </div>
              <div className={styles.inputColumn}>
                <FormControl
                  isRequired
                  isInvalid={!!errors.human_readable_name}
                >
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
              </div>
            </div>

            <div className={styles.formRow}>
              <div className={styles.labelColumn}>
                <label className={styles.formLabel}>Description</label>
              </div>
              <div className={styles.inputColumn}>
                <FormControl isRequired isInvalid={!!errors.description}>
                  <Textarea
                    name="description"
                    value={formData.description}
                    onChange={handleChange}
                    placeholder="Describe what this agent does..."
                    className={styles.textarea}
                    rows={2}
                    size="md"
                  />
                  {errors.description && (
                    <FormErrorMessage>{errors.description}</FormErrorMessage>
                  )}
                </FormControl>
              </div>
            </div>

            <div className={styles.toggleRow}>
              <Switch
                id="connection-mode"
                colorScheme="green"
                isChecked={showUrlInput}
                onChange={handleConfigToggle}
              />
              <Text className={styles.formLabel}>
                I already have a remote MCP URL
              </Text>
            </div>

            {showUrlInput ? (
              <div className={styles.formRow}>
                <div className={styles.labelColumn}>
                  <label className={styles.formLabel}>MCP Server URL</label>
                </div>
                <div className={styles.inputColumn}>
                  <FormControl isRequired isInvalid={!!errors.mcp_server_url}>
                    <Input
                      name="mcp_server_url"
                      value={formData.mcp_server_url}
                      onChange={handleChange}
                      placeholder="e.g., https://ngrok.com/sse"
                      className={styles.input}
                      size="md"
                    />
                    {errors.mcp_server_url ? (
                      <FormErrorMessage>
                        {errors.mcp_server_url}
                      </FormErrorMessage>
                    ) : (
                      <FormHelperText className={styles.helperText}>
                        Remote URL to connect to (Server-Sent Events endpoint)
                      </FormHelperText>
                    )}
                  </FormControl>
                </div>
              </div>
            ) : (
              <MCPConfigForm onUrlUpdate={handleUrlUpdate} />
            )}
          </div>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};
