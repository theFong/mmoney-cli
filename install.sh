#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PACKAGE="mmoney"

echo -e "${BLUE}"
echo "  __  __ __  __  ___  _  _ _____   __"
echo " |  \/  |  \/  |/ _ \| \| | __\ \ / /"
echo " | |\/| | |\/| | (_) | .\` | _| \ V / "
echo " |_|  |_|_|  |_|\___/|_|\_|___| |_|  "
echo -e "${NC}"
echo "Monarch Money CLI Installer"
echo ""

# Detect OS
OS="$(uname -s)"
case "$OS" in
    Linux*)     OS_TYPE="linux";;
    Darwin*)    OS_TYPE="macos";;
    MINGW*|MSYS*|CYGWIN*) OS_TYPE="windows";;
    *)          OS_TYPE="unknown";;
esac

# Check for existing tools
HAS_UV=false
HAS_PIPX=false
HAS_PIP=false

if command -v uv &> /dev/null; then
    HAS_UV=true
fi

if command -v pipx &> /dev/null; then
    HAS_PIPX=true
fi

if command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
    HAS_PIP=true
fi

# Function to install uv
install_uv() {
    echo -e "${YELLOW}Installing uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source the env to get uv in path
    if [ -f "$HOME/.local/bin/env" ]; then
        source "$HOME/.local/bin/env"
    elif [ -f "$HOME/.cargo/env" ]; then
        source "$HOME/.cargo/env"
    fi
    export PATH="$HOME/.local/bin:$PATH"
}

# Function to install pipx
install_pipx() {
    echo -e "${YELLOW}Installing pipx...${NC}"
    if [ "$OS_TYPE" = "macos" ]; then
        if command -v brew &> /dev/null; then
            brew install pipx
            pipx ensurepath
        else
            pip3 install --user pipx
            python3 -m pipx ensurepath
        fi
    elif [ "$OS_TYPE" = "linux" ]; then
        if command -v apt &> /dev/null; then
            sudo apt update && sudo apt install -y pipx
            pipx ensurepath
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y pipx
            pipx ensurepath
        else
            pip3 install --user pipx
            python3 -m pipx ensurepath
        fi
    else
        pip3 install --user pipx
        python3 -m pipx ensurepath
    fi
}

# Function to prompt user
prompt_choice() {
    echo -e "${YELLOW}No package manager for CLI tools found.${NC}"
    echo ""
    echo "Which would you like to install?"
    echo ""
    echo "  1) uv (recommended - fast, modern Python package manager)"
    echo "  2) pipx (traditional - stable, widely used)"
    echo "  3) Skip - I'll install manually"
    echo ""
    read -p "Enter choice [1/2/3]: " choice

    case "$choice" in
        1) install_uv; HAS_UV=true;;
        2) install_pipx; HAS_PIPX=true;;
        3) echo -e "${YELLOW}Skipping. Install manually with: pipx install $PACKAGE${NC}"; exit 0;;
        *) echo -e "${RED}Invalid choice${NC}"; exit 1;;
    esac
}

# Main logic
echo -e "Detected OS: ${GREEN}$OS_TYPE${NC}"
echo ""

if $HAS_UV; then
    echo -e "${GREEN}✓${NC} uv found"
    echo -e "${BLUE}Installing $PACKAGE with uv...${NC}"
    uv tool install "$PACKAGE"
elif $HAS_PIPX; then
    echo -e "${GREEN}✓${NC} pipx found"
    echo -e "${BLUE}Installing $PACKAGE with pipx...${NC}"
    pipx install "$PACKAGE"
else
    echo -e "${YELLOW}!${NC} Neither uv nor pipx found"

    if ! $HAS_PIP; then
        echo -e "${RED}Error: Python/pip not found. Please install Python 3.9+ first.${NC}"
        echo ""
        echo "Install Python from: https://www.python.org/downloads/"
        exit 1
    fi

    prompt_choice

    # Now install with the chosen tool
    if $HAS_UV; then
        echo ""
        echo -e "${BLUE}Installing $PACKAGE with uv...${NC}"
        uv tool install "$PACKAGE"
    elif $HAS_PIPX; then
        echo ""
        echo -e "${BLUE}Installing $PACKAGE with pipx...${NC}"
        pipx install "$PACKAGE"
    fi
fi

echo ""
echo -e "${GREEN}✓ Installation complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Restart your terminal (or run: source ~/.zshrc)"
echo "  2. Login: mmoney auth login --help"
echo ""
echo -e "Documentation: ${BLUE}https://github.com/theFong/mmoney-cli${NC}"
