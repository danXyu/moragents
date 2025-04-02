#!/bin/bash
# Run all linters on Python files in the project including submodules

set -e  # Exit immediately if a command exits with a non-zero status

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get the root directory (parent of build/)
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Get the project root directory
PROJECT_ROOT="$ROOT_DIR/.."

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print section headers
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Python and pip
if command_exists python3; then
    PYTHON_CMD="python3"
elif command_exists python; then
    PYTHON_CMD="python"
else
    echo -e "${RED}Error: Python is not installed.${NC}"
    exit 1
fi

# Check for pip
if command_exists pip3; then
    PIP_CMD="pip3"
elif command_exists pip; then
    PIP_CMD="pip"
else
    echo -e "${RED}Error: pip is not installed. Please install pip.${NC}"
    exit 1
fi

print_header "Checking/Installing Linting Tools"
echo "Using Python: $($PYTHON_CMD --version)"
echo "Using pip: $($PIP_CMD --version)"

# Install linting tools if needed
echo "Installing linting tools..."
$PIP_CMD install flake8==7.0.0 black==23.12.1 isort==5.13.2

# Create a temporary file for capturing linting issues
LINT_ISSUES=$(mktemp)

# Define exclusion patterns - align these with the GitHub Actions workflow
EXCLUDE_DIRS="--exclude=.git,__pycache__,build,dist,*.egg,*.egg-info,.eggs,.venv,venv,env,.env,ENV,node_modules,*/node_modules/*,*/.venv/*,*/site-packages/*"

# Find Python files to check (excluding node_modules, venv, etc.)
print_header "Finding Python Files to Check"
PYTHON_FILES=$(find "$PROJECT_ROOT" -name "*.py" -type f | grep -v "node_modules\|\.venv\|site-packages\|__pycache__\|\.git")
FILE_COUNT=$(echo "$PYTHON_FILES" | wc -l)
echo "Found $FILE_COUNT Python files to check."

if [ "$FILE_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}Warning: No Python files found to check in $PROJECT_ROOT${NC}"
    exit 0
fi

# Black formatting check with correct line length (with diff)
print_header "Checking Python Formatting with Black"
if black --line-length=120 --diff $PYTHON_FILES 2>&1 | tee -a "$LINT_ISSUES" | grep -q "would reformat"; then
    echo -e "\n${YELLOW}Some files need formatting with Black.${NC}"
    echo -e "Run: ${GREEN}black --line-length=120 \"$PROJECT_ROOT\"${NC} to fix formatting issues."
    FORMAT_NEEDED=1
else
    echo -e "${GREEN}All Python files are properly formatted according to Black.${NC}"
fi

# Use isort with the settings from pyproject.toml
print_header "Checking Python Import Sorting with isort"
if isort --profile black --line-length 120 --diff $PYTHON_FILES 2>&1 | tee -a "$LINT_ISSUES" | grep -q "ERROR"; then
    echo -e "\n${YELLOW}Some imports need sorting with isort.${NC}"
    echo -e "Run: ${GREEN}isort --profile black --line-length 120 \"$PROJECT_ROOT\"${NC} to fix import sorting issues."
    FORMAT_NEEDED=1
else
    echo -e "${GREEN}All Python imports are properly sorted according to isort.${NC}"
fi

# flake8 linting check
print_header "Checking Python Code with flake8"
if ! flake8 $EXCLUDE_DIRS --max-line-length=120 "$PROJECT_ROOT" 2>&1 | tee -a "$LINT_ISSUES"; then
    echo -e "\n${YELLOW}flake8 found issues that need to be fixed.${NC}"
    LINT_ISSUES_FOUND=1
else
    echo -e "${GREEN}No flake8 issues found.${NC}"
fi

# Check if formatting or linting issues were found
print_header "Summary"
if [ -n "$FORMAT_NEEDED" ] || [ -n "$LINT_ISSUES_FOUND" ]; then
    echo -e "${YELLOW}Linting issues were found. See above for details.${NC}"
    
    # Ask if user wants to automatically fix formatting issues
    if [ -n "$FORMAT_NEEDED" ]; then
        echo -ne "\n${BLUE}Would you like to automatically fix formatting issues? [y/N] ${NC}"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            echo "Formatting Python files with Black..."
            black --line-length=120 $PYTHON_FILES
            
            echo "Sorting imports with isort..."
            isort --profile black --line-length 120 $PYTHON_FILES
            
            echo -e "${GREEN}Formatting complete!${NC}"
        else
            echo "Skipping automatic formatting."
        fi
    fi
    
    # Remind about flake8 issues
    if [ -n "$LINT_ISSUES_FOUND" ]; then
        echo -e "\n${YELLOW}Note: flake8 issues must be fixed manually. They cannot be auto-fixed.${NC}"
    fi
    
    exit 1
else
    echo -e "${GREEN}All linting checks passed successfully!${NC}"
    exit 0
fi