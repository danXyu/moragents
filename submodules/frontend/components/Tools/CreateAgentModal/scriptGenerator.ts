import { MCPConfig } from "./types";
import { SCRIPT_TEMPLATE } from "./scriptTemplates";

/**
 * Generate a shell script based on the provided MCP configuration
 * @param config - The MCP server configuration
 * @returns A shell script string that will run the MCP server and create a public URL
 */
export const generateShellScript = (config: MCPConfig): string => {
  // Format environment variables
  const envVars = config.env
    .filter((env) => env.key.trim() && env.value.trim())
    .map((env) => `export ${env.key}="${env.value}"`)
    .join("\n");

  // Format arguments
  const args = config.args
    .filter((arg) => arg.trim())
    .map((arg) => `"${arg}"`)
    .join(" ");

  // Properly escape the command and args to prevent shell interpretation issues
  const escapedCommand = config.command.replace(/"/g, '\\"');

  // Replace placeholders in the template
  let script = SCRIPT_TEMPLATE.replace("{{DATE}}", new Date().toLocaleString())
    .replace("{{COMMAND}}", escapedCommand)
    .replace("{{ARGS}}", args)
    .replace(
      "{{ENV_VARS}}",
      envVars ? envVars : "# No environment variables specified"
    );

  // Fix the supergateway command to properly execute the command with arguments
  script = script.replace(
    'npx -y supergateway --stdio "{{COMMAND}} {{ARGS}}"',
    `npx -y supergateway --stdio "${escapedCommand} ${args}"`
  );

  return script;
};
