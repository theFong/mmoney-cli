# mmoney - Monarch Money CLI

Access your Monarch Money financial data through natural language.

## Prerequisites
- `mmoney` CLI installed (`pip install mmoney-cli`)
- Authenticated (`mmoney auth login` or `mmoney auth use-token`)

## Available Commands

### Accounts
```bash
mmoney accounts list --format json          # List all accounts
mmoney accounts list --format csv           # CSV format for tables
```

### Transactions
```bash
mmoney transactions list --format json      # Recent transactions
mmoney transactions list --search "grocery" # Search by merchant/description
mmoney transactions list --start-date 2024-01-01 --end-date 2024-01-31
mmoney transactions list --category-id 123  # Filter by category
mmoney transactions summary                 # Spending summary
```

### Holdings (Investments)
```bash
mmoney holdings list --format json          # All investment holdings
mmoney holdings history --account-id 123    # Balance history
```

### Cashflow
```bash
mmoney cashflow summary                              # This month
mmoney cashflow summary --timeframe last_month
mmoney cashflow summary --timeframe last_3_months
mmoney cashflow summary --timeframe this_year
```

### Budgets
```bash
mmoney budgets list --format json           # All budgets with status
```

### Categories & Tags
```bash
mmoney categories list --format json        # All categories
mmoney tags list --format json              # All tags
```

### Other
```bash
mmoney recurring list                       # Recurring transactions
mmoney institutions list                    # Connected institutions
mmoney subscription details                 # Subscription status
```

## Output Formats
- `--format json` (default) - Structured JSON, best for parsing
- `--format csv` - Tabular data, good for spreadsheets
- `--format jsonl` - One JSON object per line, good for streaming
- `--format text` - Simple key-value pairs

## Usage Tips

1. **Always use `--format json`** for structured data parsing
2. **Use `--format csv`** when presenting tabular data to users
3. **Filter transactions** with `--search`, `--start-date`, `--end-date`
4. **Check authentication** with `mmoney auth status` if commands fail

## Example Queries

**"Show my account balances"**
```bash
mmoney accounts list --format csv
```

**"What did I spend on groceries last month?"**
```bash
mmoney transactions list --search "grocery" --start-date 2024-12-01 --end-date 2024-12-31 --format json
```

**"How much did I save this month?"**
```bash
mmoney cashflow summary --timeframe this_month
```

**"Show my investment portfolio"**
```bash
mmoney holdings list --format csv
```

## Error Handling

If a command fails, check:
1. Authentication: `mmoney auth status`
2. Re-login if needed: `mmoney auth login`

Exit codes:
- `0` - Success
- `1` - General error
- `2` - Authentication error
- `3` - Not found
- `4` - Validation error
