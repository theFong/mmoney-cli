# mmoney - Monarch Money CLI

Use the `mmoney` CLI to access Monarch Money financial data. This is an unofficial community tool.

## Data Model

```
Institution ──▶ Credential ──▶ Account ──┬──▶ Transaction ──┬──▶ Category ──▶ Category Group
(Bank)          (Connection)   (Checking) │                  ├──▶ Merchant
                                          │                  └──▶ Tags
                                          ├──▶ Holding (Investment)
                                          └──▶ Balance History
```

**Key Relationships:**
- One institution can have multiple credentials (connections)
- One credential links multiple accounts from the same bank login
- Transactions belong to one account, have one category, one merchant, and multiple tags
- Categories belong to one group (e.g., "Groceries" → "Food & Drink")

## Authentication

Check status:
```bash
mmoney auth status
```

> **Security:** Use interactive mode (default) so passwords aren't logged to shell history. Only use `--no-interactive` with environment variables or secure credential injection.

### Method 1: Email + Password + MFA (Recommended)

The most secure and longest-lasting method. Enable MFA on your Monarch account if not already enabled.

**Interactive login (prompts for password securely):**
```bash
mmoney auth login -e EMAIL --mfa-secret YOUR_MFA_SECRET
# or with one-time code:
mmoney auth login -e EMAIL --mfa-code 123456
```

**Non-interactive (for automation with secure credential injection):**
```bash
mmoney auth login -e "$EMAIL" -p "$PASSWORD" --mfa-secret "$MFA_SECRET" --no-interactive
```

### Method 2: Device ID (No MFA Required)

If MFA is not enabled on your account, use a device ID from your browser to establish a trusted device.

**Step 1: Get the device ID from browser**

Use Claude Code with `--chrome` to navigate to app.monarchmoney.com, login, then run in the browser console:
```javascript
localStorage.getItem('monarchDeviceUUID')
```

**Step 2: Save the device ID**
```bash
mmoney config set device-id YOUR_DEVICE_UUID
```

**Step 3: Login interactively (prompts for password)**
```bash
mmoney auth login -e EMAIL
```

The device ID persists in `~/.mmoney/config.json`, so future logins only need email + password.

### Config Commands

```bash
mmoney config list              # Show all config values
mmoney config get device-id     # Get device ID
mmoney config set device-id ID  # Set device ID
mmoney config unset device-id   # Remove device ID
```

## Output Format

Always use `-f json` for structured output:
```bash
mmoney -f json accounts list
```

## Commands

### Accounts
Bank accounts, credit cards, investments, loans.

```bash
mmoney accounts list              # List all accounts
mmoney accounts types             # List valid account types
mmoney accounts refresh           # Refresh from institutions
mmoney accounts refresh-status    # Check refresh status
```

**Key fields:** `id`, `displayName`, `currentBalance`, `type.name` (depository/credit/investment/loan), `subtype.name` (checking/savings/credit_card/brokerage), `isAsset` (true=asset, false=liability), `institution.name`

### Transactions
Every purchase, payment, transfer, and deposit.

```bash
mmoney transactions list                              # Recent transactions
mmoney transactions list --limit 50                   # Limit results
mmoney transactions list --search "coffee"            # Search by text
mmoney transactions list --start-date 2024-01-01 --end-date 2024-12-31
mmoney transactions list --category-id CAT_ID         # Filter by category
mmoney transactions list --account-id ACC_ID          # Filter by account
mmoney transactions get TXN_ID                        # Single transaction
mmoney transactions summary                           # Spending summary
```

**Key fields:** `id`, `amount` (negative=expense, positive=income), `date`, `merchant.name`, `category.name`, `account.displayName`, `pending`, `isRecurring`, `tags[]`

### Categories
~50 system categories across groups like "Food & Drink", "Transportation", "Housing".

```bash
mmoney categories list    # All categories
mmoney categories groups  # Category groups
```

**Key fields:** `id`, `name`, `group.name`, `group.type` (expense/income), `isSystemCategory`

### Tags
Flexible labels: "Tax Deductible", "Business", "Reimbursable". Transactions can have multiple tags.

```bash
mmoney tags list
```

**Key fields:** `id`, `name`, `color`, `transactionCount`

### Holdings (Investments)
Investment positions in brokerage, 401k, IRA accounts.

```bash
mmoney holdings list ACCOUNT_ID      # Holdings in account
mmoney holdings history ACCOUNT_ID   # Balance history
mmoney holdings snapshots            # Aggregate snapshots
mmoney holdings balances             # Recent balances
```

### Budgets
```bash
mmoney budgets list
mmoney budgets list --start-date 2024-01-01
```

### Cashflow
Income vs expenses, savings rate.

```bash
mmoney cashflow summary   # sumIncome, sumExpense, savings, savingsRate
mmoney cashflow details   # Breakdown by category/merchant
```

### Recurring
Auto-detected subscriptions and bills.

```bash
mmoney recurring list
```

**Key fields:** `stream.frequency` (weekly/monthly/yearly), `stream.amount`, `stream.merchant.name`, `date`, `isPast`

### Institutions
Linked banks and brokers.

```bash
mmoney institutions list
```

**Key fields:** `id`, `institution.name`, `institution.status` (HEALTHY/DEGRADED/DOWN), `updateRequired`, `dataProvider` (PLAID/MX)

## Common Patterns

### Get all account balances
```bash
mmoney -f json accounts list | jq '.accounts[] | {name: .displayName, balance: .currentBalance, type: .type.name}'
```

### Find transactions by merchant
```bash
mmoney -f json transactions list --search "amazon" --limit 20
```

### Monthly spending by category
```bash
mmoney -f json cashflow details --start-date 2024-01-01 --end-date 2024-01-31
```

### Net worth (assets - liabilities)
```bash
mmoney -f json accounts list | jq '[.accounts[] | select(.includeInNetWorth) | if .isAsset then .currentBalance else -.currentBalance end] | add'
```

### Find recurring subscriptions
```bash
mmoney -f json recurring list | jq '.recurringTransactionItems[] | {merchant: .stream.merchant.name, amount: .stream.amount, frequency: .stream.frequency}'
```

## Mutations (Write Operations)

CLI runs in **read-only mode** by default. To modify data:

```bash
mmoney --allow-mutations transactions create --date 2024-01-15 --account-id ACC_ID --amount -25.00 --merchant "Coffee Shop" --category-id CAT_ID
mmoney --allow-mutations transactions update TXN_ID --category-id NEW_CAT_ID
mmoney --allow-mutations accounts update ACC_ID --name "New Name"
```

**Always confirm with the user before running mutation commands.**

## Error Handling

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": "Additional context"
  }
}
```

| Code | Meaning |
|------|---------|
| `AUTH_REQUIRED` | User needs to login |
| `AUTH_FAILED` | Invalid credentials |
| `MUTATION_BLOCKED` | Need `--allow-mutations` flag |
| `VALIDATION_MISSING_FIELD` | Required parameter missing |
| `NOT_FOUND` | Resource not found |
| `API_ERROR` | Monarch Money API error |

> **Note:** Repeated 403 errors may indicate rate limiting. Wait a few minutes before retrying.
