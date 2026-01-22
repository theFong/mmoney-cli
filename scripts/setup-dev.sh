#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Check if running in CI or non-interactive mode
INTERACTIVE=${INTERACTIVE:-true}
if [[ ! -t 0 ]]; then
    INTERACTIVE=false
fi

# ============================================================================
# Install uv (fast Python package manager)
# ============================================================================
install_uv() {
    if command -v uv &> /dev/null; then
        info "uv is already installed: $(uv --version)"
        return 0
    fi

    info "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Add to PATH for current session
    export PATH="$HOME/.local/bin:$PATH"

    if command -v uv &> /dev/null; then
        info "uv installed successfully: $(uv --version)"
    else
        error "Failed to install uv"
    fi
}

# ============================================================================
# Install Python dependencies
# ============================================================================
install_deps() {
    info "Installing Python dependencies..."
    uv sync --extra dev
    info "Dependencies installed"
}

# ============================================================================
# Setup pre-commit hooks
# ============================================================================
setup_hooks() {
    info "Installing pre-commit hooks..."
    uv run pre-commit install
    uv run pre-commit install --hook-type pre-push
    info "Git hooks installed"
}

# ============================================================================
# Generate secrets baseline if missing
# ============================================================================
setup_secrets_baseline() {
    if [[ ! -f ".secrets.baseline" ]]; then
        info "Generating secrets baseline..."
        uv run detect-secrets scan > .secrets.baseline
        info "Secrets baseline created"
    else
        info "Secrets baseline already exists"
    fi
}

# ============================================================================
# Verify installation
# ============================================================================
verify_install() {
    info "Verifying installation..."

    local checks_passed=true

    # Check uv
    if command -v uv &> /dev/null; then
        echo "  ✓ uv: $(uv --version)"
    else
        echo "  ✗ uv not found"
        checks_passed=false
    fi

    # Check Python
    if uv run python --version &> /dev/null; then
        echo "  ✓ Python: $(uv run python --version)"
    else
        echo "  ✗ Python not working"
        checks_passed=false
    fi

    # Check mmoney CLI
    if uv run mmoney --version &> /dev/null; then
        echo "  ✓ mmoney CLI: $(uv run mmoney --version)"
    else
        echo "  ✗ mmoney CLI not working"
        checks_passed=false
    fi

    # Check pre-commit
    if [[ -f ".git/hooks/pre-commit" ]]; then
        echo "  ✓ pre-commit hooks installed"
    else
        echo "  ✗ pre-commit hooks not installed"
        checks_passed=false
    fi

    if [[ "$checks_passed" == "true" ]]; then
        info "All checks passed!"
    else
        warn "Some checks failed"
        return 1
    fi
}

# ============================================================================
# Run linters
# ============================================================================
run_lint() {
    info "Running linters..."
    uv run ruff check .
    uv run ruff format --check .
    uv run vulture mmoney_cli --min-confidence 80
    uv run pyright mmoney_cli/
    info "All linters passed!"
}

# ============================================================================
# Run tests
# ============================================================================
run_tests() {
    info "Running tests..."
    uv run pytest tests/ -q
    info "All tests passed!"
}

# ============================================================================
# Main
# ============================================================================
main() {
    local cmd="${1:-setup}"

    case "$cmd" in
        setup)
            info "Setting up development environment..."
            install_uv
            install_deps
            setup_hooks
            setup_secrets_baseline
            verify_install
            echo ""
            info "Development environment ready!"
            echo ""
            echo "Quick commands:"
            echo "  uv run mmoney --help    # Run the CLI"
            echo "  uv run pytest tests/    # Run tests"
            echo "  uv run ruff check .     # Run linter"
            echo "  uv run pyright .        # Type check"
            ;;
        deps)
            install_deps
            ;;
        hooks)
            setup_hooks
            ;;
        verify)
            verify_install
            ;;
        lint)
            run_lint
            ;;
        test)
            run_tests
            ;;
        all)
            install_uv
            install_deps
            setup_hooks
            setup_secrets_baseline
            verify_install
            run_lint
            run_tests
            ;;
        *)
            echo "Usage: $0 {setup|deps|hooks|verify|lint|test|all}"
            echo ""
            echo "Commands:"
            echo "  setup   - Full dev environment setup (default)"
            echo "  deps    - Install dependencies only"
            echo "  hooks   - Install git hooks only"
            echo "  verify  - Verify installation"
            echo "  lint    - Run all linters"
            echo "  test    - Run tests"
            echo "  all     - Setup + lint + test"
            exit 1
            ;;
    esac
}

main "$@"
