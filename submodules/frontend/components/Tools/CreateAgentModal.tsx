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
  Divider,
  Text,
  useToast,
  InputGroup,
  InputLeftAddon,
  HStack,
} from "@chakra-ui/react";
import { ChevronLeftIcon } from "@chakra-ui/icons";
import styles from "./ToolsConfiguration.module.css";

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
    command: "",
    description: "",
    delegator_description: "",
    mcp_server_url: "",
    upload_required: false,
    is_enabled: true,
  });

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSwitchChange = (name: string) => {
    setFormData((prev) => ({
      ...prev,
      [name]: !prev[name as keyof typeof prev],
    }));
  };

  const validateForm = () => {
    const requiredFields = [
      "human_readable_name",
      "command",
      "description",
      "delegator_description",
      "mcp_server_url",
    ];

    const missingFields = requiredFields.filter(
      (field) => !formData[field as keyof typeof formData]
    );

    if (missingFields.length > 0) {
      toast({
        title: "Missing required fields",
        description: `Please fill in all required fields: ${missingFields.join(
          ", "
        )}`,
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
      // Mock API call for now
      console.log("Creating new agent with data:", formData);

      // Simulate API delay
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // For demo purposes, we'll just show success
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
        command: "",
        description: "",
        delegator_description: "",
        mcp_server_url: "",
        upload_required: false,
        is_enabled: true,
      });
    } catch (error) {
      console.error("Error creating agent:", error);
      toast({
        title: "Error creating agent",
        description: "There was an error creating the agent. Please try again.",
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
    <Modal isOpen={isOpen} onClose={onClose} size="lg">
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
        {/* No ModalCloseButton here as it's been replaced by the Back button */}

        <ModalBody className={styles.modalBody}>
          <Text className={styles.createAgentDescription}>
            Create a new agent by connecting to an MCP server. The agent&apos;s
            tools will be imported automatically.
          </Text>

          <VStack spacing={3} align="stretch">
            <FormControl isRequired className={styles.formGroup}>
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

            <FormControl isRequired className={styles.formGroup}>
              <FormLabel className={styles.formLabel}>Command</FormLabel>
              <InputGroup size="sm">
                <InputLeftAddon className={styles.inputLeftAddon}>
                  /
                </InputLeftAddon>
                <Input
                  name="command"
                  value={formData.command}
                  onChange={handleChange}
                  placeholder="e.g., search"
                  className={styles.input}
                  size="sm"
                />
              </InputGroup>
              <FormHelperText className={styles.helperText}>
                Command used to invoke this agent (no spaces)
              </FormHelperText>
            </FormControl>

            <FormControl isRequired className={styles.formGroup}>
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

            <FormControl isRequired className={styles.formGroup}>
              <FormLabel className={styles.formLabel}>
                Delegator Description
              </FormLabel>
              <Textarea
                name="delegator_description"
                value={formData.delegator_description}
                onChange={handleChange}
                placeholder="Description for the delegator..."
                className={styles.textarea}
                rows={2}
                size="sm"
              />
              <FormHelperText className={styles.helperText}>
                Description used by the delegator to determine when to use this
                agent
              </FormHelperText>
            </FormControl>

            <FormControl isRequired className={styles.formGroup}>
              <FormLabel className={styles.formLabel}>MCP Server URL</FormLabel>
              <Input
                name="mcp_server_url"
                value={formData.mcp_server_url}
                onChange={handleChange}
                placeholder="e.g., https://my-mcp-server.com/api"
                className={styles.input}
                size="sm"
              />
              <FormHelperText className={styles.helperText}>
                The URL of the MCP server to connect to
              </FormHelperText>
            </FormControl>

            <Divider className={styles.formDivider} />

            <FormControl
              display="flex"
              alignItems="center"
              className={styles.formGroup}
            >
              <Switch
                id="upload-required"
                isChecked={formData.upload_required}
                onChange={() => handleSwitchChange("upload_required")}
                className={styles.switch}
                size="sm"
              />
              <FormLabel
                htmlFor="upload-required"
                mb="0"
                ml={2}
                className={styles.switchLabel}
              >
                Requires File Upload
              </FormLabel>
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
