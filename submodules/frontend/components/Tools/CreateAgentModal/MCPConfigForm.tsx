import React, { useState, useEffect } from "react";
import {
  VStack,
  FormControl,
  FormLabel,
  Input,
  Box,
  HStack,
  IconButton,
  Button,
  Text,
  Code,
  useToast,
  useClipboard,
  FormHelperText,
  FormErrorMessage,
} from "@chakra-ui/react";
import { AddIcon, DeleteIcon, CopyIcon, CheckIcon } from "@chakra-ui/icons";
import styles from "./MCPConfigForm.module.css";
import { MCPConfig, FormErrors, EnvVar } from "./types";
import { generateShellScript } from "./scriptGenerator";
import { downloadFile } from "@/services/fileUtils";

interface MCPConfigFormProps {
  onUrlUpdate: (url: string) => void;
}

export const MCPConfigForm: React.FC<MCPConfigFormProps> = ({
  onUrlUpdate,
}) => {
  const toast = useToast();
  const [mcpConfig, setMcpConfig] = useState<MCPConfig>({
    command: "npx",
    args: [""],
    env: [{ key: "", value: "" }],
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [generatedScript, setGeneratedScript] = useState("");
  const { hasCopied, onCopy } = useClipboard(generatedScript);
  const [isFormValid, setIsFormValid] = useState(false);

  // Validate the form whenever mcpConfig changes
  useEffect(() => {
    validateForm();
  }, [mcpConfig]);

  const handleConfigChange = (
    field: "command" | "args",
    value: string,
    index: number = 0
  ) => {
    if (field === "command") {
      setMcpConfig((prev) => ({
        ...prev,
        command: value,
      }));

      // Clear error for command field
      if (errors.command) {
        setErrors((prev) => ({ ...prev, command: undefined }));
      }
    } else if (field === "args") {
      const newArgs = [...mcpConfig.args];
      newArgs[index] = value;
      setMcpConfig((prev) => ({
        ...prev,
        args: newArgs,
      }));

      // Clear error for args field
      if (errors.args) {
        setErrors((prev) => ({ ...prev, args: undefined }));
      }
    }
  };

  const handleEnvChange = (
    index: number,
    field: "key" | "value",
    value: string
  ) => {
    const newEnv = [...mcpConfig.env];
    newEnv[index] = {
      ...newEnv[index],
      [field]: value,
    };
    setMcpConfig((prev) => ({
      ...prev,
      env: newEnv,
    }));
  };

  const addArgField = () => {
    setMcpConfig((prev) => ({
      ...prev,
      args: [...prev.args, ""],
    }));
  };

  const removeArgField = (index: number) => {
    if (mcpConfig.args.length > 1) {
      const newArgs = [...mcpConfig.args];
      newArgs.splice(index, 1);
      setMcpConfig((prev) => ({
        ...prev,
        args: newArgs,
      }));
    }
  };

  const addEnvField = () => {
    setMcpConfig((prev) => ({
      ...prev,
      env: [...prev.env, { key: "", value: "" }],
    }));
  };

  const removeEnvField = (index: number) => {
    if (mcpConfig.env.length > 1) {
      const newEnv = [...mcpConfig.env];
      newEnv.splice(index, 1);
      setMcpConfig((prev) => ({
        ...prev,
        env: newEnv,
      }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};
    let isValid = true;

    // Validate MCP config
    if (!mcpConfig.command.trim()) {
      newErrors.command = "Command is required";
      isValid = false;
    }

    // Validate at least one argument is not empty
    const hasValidArg = mcpConfig.args.some((arg) => arg.trim() !== "");
    if (!hasValidArg) {
      newErrors.args = "At least one argument is required";
      isValid = false;
    }

    setErrors(newErrors);
    setIsFormValid(isValid);
    return isValid;
  };

  const handleGenerateScript = () => {
    if (!validateForm()) return;

    const script = generateShellScript(mcpConfig);
    setGeneratedScript(script);

    // Auto-copy to clipboard
    navigator.clipboard.writeText(script).then(() => {
      toast({
        title: "Script copied to clipboard",
        description: "You can now save it and run it to start your MCP server",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    });

    return script;
  };

  const handleDownloadScript = () => {
    const script = generatedScript || handleGenerateScript();
    if (script) {
      downloadFile(script, "start-mcp-server.sh", "text/plain");
    }
  };

  return (
    <VStack spacing={4} className={styles.configContainer}>
      <Text className={styles.configTitle}>MCP Server Walkthrough</Text>

      <FormControl isRequired isInvalid={!!errors.command}>
        <FormLabel className={styles.formLabel}>Command</FormLabel>
        <Input
          value={mcpConfig.command}
          onChange={(e) => handleConfigChange("command", e.target.value)}
          placeholder="e.g., npx"
          className={styles.input}
        />
        {errors.command && (
          <FormErrorMessage>{errors.command}</FormErrorMessage>
        )}
      </FormControl>

      <FormControl isRequired isInvalid={!!errors.args}>
        <FormLabel className={styles.formLabel}>
          Arguments
          <IconButton
            aria-label="Add argument"
            icon={<AddIcon />}
            size="xs"
            ml={2}
            onClick={addArgField}
            colorScheme="green"
            variant="ghost"
          />
        </FormLabel>
        {mcpConfig.args.map((arg, idx) => (
          <HStack key={`arg-${idx}`} spacing={2} mb={2}>
            <Input
              value={arg}
              onChange={(e) => handleConfigChange("args", e.target.value, idx)}
              placeholder="e.g., -y @chaindead/telegram-mcp"
              className={styles.input}
            />
            {mcpConfig.args.length > 1 && (
              <IconButton
                aria-label="Remove argument"
                icon={<DeleteIcon />}
                size="sm"
                onClick={() => removeArgField(idx)}
                colorScheme="red"
                variant="ghost"
              />
            )}
          </HStack>
        ))}
        {errors.args && <FormErrorMessage>{errors.args}</FormErrorMessage>}
      </FormControl>

      <FormControl>
        <FormLabel className={styles.formLabel}>
          Environment Variables
          <IconButton
            aria-label="Add environment variable"
            icon={<AddIcon />}
            size="xs"
            ml={2}
            onClick={addEnvField}
            colorScheme="green"
            variant="ghost"
          />
        </FormLabel>
        {mcpConfig.env.map((env, idx) => (
          <HStack key={`env-${idx}`} spacing={2} mb={2}>
            <Input
              value={env.key}
              onChange={(e) => handleEnvChange(idx, "key", e.target.value)}
              placeholder="Variable name"
              className={styles.input}
            />
            <Input
              value={env.value}
              onChange={(e) => handleEnvChange(idx, "value", e.target.value)}
              placeholder="Value"
              className={styles.input}
            />
            {mcpConfig.env.length > 1 && (
              <IconButton
                aria-label="Remove environment variable"
                icon={<DeleteIcon />}
                size="sm"
                onClick={() => removeEnvField(idx)}
                colorScheme="red"
                variant="ghost"
              />
            )}
          </HStack>
        ))}
      </FormControl>

      <Box className={styles.scriptActions} width="100%">
        <HStack spacing={4} justifyContent="flex-end">
          <Button
            leftIcon={<CopyIcon />}
            onClick={handleGenerateScript}
            colorScheme="green"
            variant="outline"
            className={styles.actionButton}
            isDisabled={!isFormValid}
          >
            Generate & Copy Script
          </Button>
          <Button
            onClick={handleDownloadScript}
            colorScheme="blue"
            className={styles.actionButton}
            isDisabled={!isFormValid || !generatedScript}
          >
            Download Script
          </Button>
        </HStack>
      </Box>

      {generatedScript && (
        <Box className={styles.scriptPreview} width="100%">
          <FormLabel className={styles.formLabel}>
            Generated Script
            <IconButton
              aria-label="Copy script"
              icon={hasCopied ? <CheckIcon /> : <CopyIcon />}
              size="xs"
              ml={2}
              onClick={onCopy}
              colorScheme={hasCopied ? "green" : "blue"}
              variant="ghost"
            />
          </FormLabel>
          <Box className={styles.scriptContainer}>
            <Code className={styles.scriptCode}>
              {generatedScript.split("\n").slice(0, 10).join("\n")}
              {generatedScript.split("\n").length > 10 ? "\n..." : ""}
            </Code>
          </Box>
          <FormHelperText className={styles.helperText}>
            Save this script, make it executable with{" "}
            <Code className={styles.inlineCode}>chmod +x filename.sh</Code>,
            then run it. After running, paste the generated URL into the MCP
            Server URL field.
          </FormHelperText>
        </Box>
      )}
    </VStack>
  );
};
