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
    .map((env) => `${env.key}="${env.value}"`)
    .join("\n");

  // Format arguments
  const args = config.args
    .filter((arg) => arg.trim())
    .map((arg) => `"${arg}"`)
    .join(" ");

  // Replace placeholders in the template
  return SCRIPT_TEMPLATE.replace("{{DATE}}", new Date().toLocaleString())
    .replace("{{COMMAND}}", config.command)
    .replace("{{ARGS}}", args)
    .replace(
      "{{ENV_VARS}}",
      envVars ? envVars : "# No environment variables specified"
    );
};
