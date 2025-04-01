#!/bin/bash
# Format the specific project files that need reformatting

set -e  # Exit immediately if a command exits with a non-zero status

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Formatting Project Files ===${NC}"

# Check if black is installed
if ! command -v black &> /dev/null; then
    echo -e "${RED}Error: black is not installed. Installing now...${NC}"
    pip install black==23.12.1
fi

# Path to your submodules/agents directory - adjust if needed
AGENTS_DIR="$(pwd)/submodules/agents"

if [ ! -d "$AGENTS_DIR" ]; then
    echo -e "${RED}Error: Could not find agents directory at $AGENTS_DIR${NC}"
    echo -e "${YELLOW}Please run this script from your project root directory${NC}"
    exit 1
fi

echo -e "${BLUE}Formatting Python files in $AGENTS_DIR${NC}"

# Run black on all Python files in the agents directory
black "$AGENTS_DIR"

# Verify the formatting
if black --check "$AGENTS_DIR"; then
    echo -e "${GREEN}All files are now properly formatted.${NC}"
else
    echo -e "${RED}Some files still need formatting. This shouldn't happen - please check for errors.${NC}"
    exit 1
fi

echo -e "${GREEN}Formatting complete!${NC}"