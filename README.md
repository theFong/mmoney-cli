# mmoney-cli

CLI for [Monarch Money](https://www.monarchmoney.com) - access your financial data from the command line.

Built on top of [monarchmoneycommunity](https://github.com/bradleyseanf/monarchmoneycommunity).

## Installation

```bash
pip install mmoney-cli
```

## Quick Start

```bash
# Login (interactive)
mmoney auth login

# Or login with credentials
mmoney auth login --no-interactive -e your@email.com -p yourpassword

# If blocked by MFA (even without MFA enabled), use device UUID from browser:
# 1. Open app.monarchmoney.com in browser
# 2. Open DevTools > Console
# 3. Run: localStorage.getItem('monarchDeviceUUID')
mmoney auth login --device-uuid YOUR_UUID -e your@email.com -p yourpassword

# Or use token directly from browser:
# 1. Open app.monarchmoney.com
# 2. DevTools > Application > Local Storage > accessToken
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

## Authentication Troubleshooting

If you see "Multi-Factor Auth Required" even without MFA enabled, Monarch is using device fingerprinting. Solutions:

1. **Device UUID** (recommended): Get from browser and use `--device-uuid`
2. **Token**: Get auth token from browser Local Storage
3. **MFA Secret**: If you have MFA enabled, use `--mfa-secret` with your TOTP secret

## License

MIT
