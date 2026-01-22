# mmoney-cli

![CI](https://github.com/theFong/mmoney-cli/actions/workflows/ci.yml/badge.svg)

> **Disclaimer:** This is an unofficial, community-built CLI tool. It is not affiliated with, endorsed by, or supported by Monarch Money. Use at your own risk.

CLI for [Monarch Money](https://www.monarchmoney.com) - access your financial data from the command line. Built for humans and AI agents.

Built on top of [monarchmoneycommunity](https://github.com/bradleyseanf/monarchmoneycommunity).

## Quick Start

### 1. Install

```bash
# One-liner (recommended)
curl -sSL https://raw.githubusercontent.com/theFong/mmoney-cli/main/install.sh | bash

# Or with a package manager
uv tool install mmoney      # fast, modern
pipx install mmoney         # stable, widely used
pip install mmoney          # may require PATH setup
```

### 2. Authenticate

```bash
# Interactive login (recommended - keeps password out of shell history)
mmoney auth login

# Or with MFA secret for full automation
mmoney auth login -e your@email.com -p yourpassword --mfa-secret YOUR_SECRET
```

See [Authentication Methods](#authentication-methods) for all options.

### 3. Use

```bash
mmoney accounts list                    # List all accounts
mmoney transactions list --limit 10     # Recent transactions
mmoney cashflow summary                 # Income, expenses, savings
```

## Claude Code Integration

This CLI is designed for use with [Claude Code](https://claude.ai/claude-code) and other AI agents.

### Install the Skill

```bash
mkdir -p .claude/commands && curl -o .claude/commands/mmoney.md https://raw.githubusercontent.com/theFong/mmoney-cli/main/.claude/commands/mmoney.md
```

### Example Prompts

Once installed, ask Claude Code things like:

- "Do I have enough liquid cash to cover 6 months of expenses?"
- "What's my savings rate this month vs last month?"
- "Am I on track with my budget? Where am I overspending?"
- "How much am I losing to subscriptions I might not need?"
- "What's my net worth trend over the past year?"
- "Show me my biggest spending categories - where can I cut back?"
- "If I lost my job today, how long could I sustain my current lifestyle?"
- "What percentage of my income is going to debt payments?"

Claude will combine multiple commands, do the math, and give you actionable insights.

### Security with AI Agents

Your credentials are safe when using Claude Code:
- Tokens stored in OS keychain (not accessible to agents)
- Passwords entered interactively (not in shell history)
- API responses contain only financial data (no credentials)

See [Security](docs/SECURITY.md) for details.

## Usage Examples

### Check account balances
```bash
mmoney accounts list | jq '.accounts[] | {name: .displayName, balance: .currentBalance}'
```

### Find specific transactions
```bash
mmoney transactions list --search "Amazon" --start-date 2024-01-01 --end-date 2024-12-31
```

### Monthly spending summary
```bash
mmoney cashflow summary --timeframe last_month
```

### Export transactions to CSV
```bash
mmoney transactions list --format csv > transactions.csv
```

### Investment portfolio
```bash
mmoney holdings list --format csv
```

## Commands

### Authentication
```bash
mmoney auth login      # Login to Monarch Money
mmoney auth logout     # Delete saved session
mmoney auth status     # Check authentication status
```

### Accounts
```bash
mmoney accounts list              # List all accounts
mmoney accounts types             # List account types
mmoney accounts create            # Create manual account
mmoney accounts update <id>       # Update account
mmoney accounts delete <id>       # Delete account
mmoney accounts refresh           # Refresh from institutions
mmoney accounts refresh-status    # Check refresh status
```

### Holdings
```bash
mmoney holdings list <account_id>     # List holdings
mmoney holdings history <account_id>  # Balance history
mmoney holdings snapshots             # Aggregate snapshots
mmoney holdings balances              # Recent balances
```

### Transactions
```bash
mmoney transactions list              # List transactions
mmoney transactions get <id>          # Get transaction details
mmoney transactions summary           # Transaction summary
mmoney transactions splits <id>       # Get splits
mmoney transactions create            # Create transaction
mmoney transactions update <id>       # Update transaction
mmoney transactions delete <id>       # Delete transaction
```

### Categories
```bash
mmoney categories list      # List categories
mmoney categories groups    # List category groups
mmoney categories create    # Create category
mmoney categories delete    # Delete category
```

### Tags
```bash
mmoney tags list                    # List tags
mmoney tags create                  # Create tag
mmoney tags set <transaction_id>    # Set tags on transaction
```

### Budgets
```bash
mmoney budgets list    # List budgets
mmoney budgets set     # Set budget amount
```

### Cashflow
```bash
mmoney cashflow summary    # Income, expenses, savings
mmoney cashflow details    # By category and merchant
```

### Other
```bash
mmoney recurring list       # Recurring transactions
mmoney institutions list    # Linked institutions
mmoney subscription status  # Subscription details
```

### Common Options

Most list commands support:
- `--limit`, `-l`: Number of records
- `--start-date`, `-s`: Start date (YYYY-MM-DD)
- `--end-date`, `-e`: End date (YYYY-MM-DD)
- `--format`, `-f`: Output format (json, csv, jsonl, text)

## Authentication Methods

Recommended methods in order of preference:

| Method | Flag | Best for |
|--------|------|----------|
| MFA Secret | `--mfa-secret` | Full automation, long-lasting |
| MFA Code | `--mfa-code` | Manual entry, secure |
| Device UUID | `--device-uuid` | Bypasses MFA |
| Token | `--token` | Quick testing, shortest lived |

**Get Device UUID:**
```bash
# In browser console at app.monarchmoney.com:
copy(localStorage.getItem('monarchDeviceUUID'))
```

**Get Token:**
```bash
# In browser Network tab, find 'Authorization: Token YOUR_TOKEN' header
```

Run `mmoney auth login --help` for detailed instructions.

## Session Storage

Sessions are stored securely using your system's keychain:
- **macOS**: Keychain
- **Windows**: Credential Manager
- **Linux**: Secret Service

Falls back to `~/.mmoney/session.pickle` if keychain is unavailable.

## Documentation

- **[Command Reference](docs/commands.md)** - Complete guide to all commands
- **[JSON Schemas](docs/schemas.md)** - Output schemas for agent integration
- **[Security](docs/SECURITY.md)** - Credential storage and AI agent safety

## Development

```bash
# Clone the repo
git clone https://github.com/theFong/mmoney-cli.git
cd mmoney-cli

# Full setup (installs uv, deps, git hooks)
./scripts/setup-dev.sh

# Or use VS Code devcontainer
# Open in VS Code and click "Reopen in Container"
```

**Quick commands:**
```bash
uv run mmoney --help        # Run the CLI
uv run pytest tests/        # Run tests
./scripts/setup-dev.sh lint # Run all linters
./scripts/setup-dev.sh test # Run tests
```

## Releasing

1. Update version in `pyproject.toml`
2. Commit and push to main
3. Either:
   - **Create a GitHub release**: `gh release create vX.Y.Z` (auto-publishes to PyPI)
   - **Manual**: [Run the publish workflow](https://github.com/theFong/mmoney-cli/actions/workflows/publish.yml)

## License

MIT
