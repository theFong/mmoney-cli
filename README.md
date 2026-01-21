# mmoney-cli

![CI](https://github.com/theFong/mmoney-cli/actions/workflows/ci.yml/badge.svg)

CLI for [Monarch Money](https://www.monarchmoney.com) - access your financial data from the command line.

Built on top of [monarchmoneycommunity](https://github.com/bradleyseanf/monarchmoneycommunity).

## Installation

```bash
# Using uv (recommended)
uv tool install mmoney-cli

# Or using pip
pip install mmoney-cli
```

## Development

```bash
# Clone and install with uv
git clone https://github.com/theFong/mmoney-cli.git
cd mmoney-cli
uv sync

# Run CLI
uv run mmoney --help
```

## Quick Start

```bash
# Best: Email + Password + MFA Secret (longest lasting, fully automated)
# Enable MFA in Monarch settings, copy the secret key when setting up authenticator
mmoney auth login -e your@email.com -p yourpassword --mfa-secret YOUR_SECRET --no-interactive

# Good: Email + Password + MFA Code (requires manual code entry)
mmoney auth login -e your@email.com -p yourpassword --mfa-code 123456

# Alternative: Email + Password + Device UUID (requires browser)
# 1. Open app.monarch.com, login, open DevTools Console
# 2. Run: copy(localStorage.getItem('monarchDeviceUUID'))
mmoney auth login -e your@email.com -p yourpassword --device-uuid YOUR_UUID --no-interactive

# Fallback: Token from browser (shortest lived)
# 1. Open app.monarch.com, login, open DevTools Network tab
# 2. Click any 'graphql' request, find 'Authorization: Token YOUR_TOKEN' in Headers
mmoney auth login --token YOUR_TOKEN
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

## Common Options

Most list commands support filtering:
- `--limit`, `-l`: Number of records
- `--start-date`, `-s`: Start date (YYYY-MM-DD)
- `--end-date`, `-e`: End date (YYYY-MM-DD)

Example:
```bash
mmoney transactions list --limit 50 --start-date 2024-01-01 --end-date 2024-12-31
```

## Output

All commands output JSON by default, making it easy to pipe to tools like `jq`:

```bash
mmoney accounts list | jq '.accounts[] | {name: .displayName, balance: .currentBalance}'
```

## Session Storage

Sessions are stored in `.mm/mm_session.pickle` in the current directory.

## Authentication Methods

Recommended authentication methods in order of preference:

1. **MFA Secret** (Best): Enable MFA in Monarch, copy the secret key when setting up your authenticator. Use `--mfa-secret` for fully automated, long-lasting auth
2. **MFA Code**: Use `--mfa-code` with the 6-digit code from your authenticator app
3. **Device UUID**: Get from browser console with `localStorage.getItem('monarchDeviceUUID')` and use `--device-uuid`
4. **Token**: Get from browser Network tab (Authorization header) and use `--token` - shortest lived

Run `mmoney auth login --help` for detailed instructions on each method.

## License

MIT
