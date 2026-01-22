# Command Reference

Complete reference for all mmoney CLI commands.

> **Note:** By default, the CLI runs in **read-only mode**. Use `--allow-mutations` to enable commands that modify data.

## Global Options

| Option | Short | Description |
|--------|-------|-------------|
| `--format` | `-f` | Output format: `text` (default), `json`, `jsonl`, `csv` |
| `--allow-mutations` | | Enable create/update/delete commands |
| `--version` | | Show version |
| `--help` | | Show help |

## Output Formats

| Format | Best For |
|--------|----------|
| `text` | Human reading, grep/awk processing |
| `json` | Structured data, API integration |
| `jsonl` | Streaming, line-by-line processing |
| `csv` | Spreadsheets, tabular analysis |

---

## auth

Authentication and session management.

### auth login

Login to Monarch Money.

```bash
# With MFA secret (best - fully automated)
mmoney auth login -e EMAIL -p PASSWORD --mfa-secret SECRET --no-interactive

# With MFA code (one-time)
mmoney auth login -e EMAIL -p PASSWORD --mfa-code 123456

# With device UUID (from browser)
mmoney auth login -e EMAIL -p PASSWORD --device-uuid UUID --no-interactive

# With token (from browser network tab)
mmoney auth login --token TOKEN
```

| Option | Short | Description |
|--------|-------|-------------|
| `--email` | `-e` | Email address |
| `--password` | `-p` | Password |
| `--mfa-secret` | | MFA secret key for automatic TOTP |
| `--mfa-code` | | One-time MFA code (6 digits) |
| `--token` | `-t` | Auth token from browser |
| `--device-uuid` | `-d` | Device UUID from browser |
| `--interactive/--no-interactive` | `-i` | Use interactive login (default: true) |

### auth logout

Delete saved session from keychain and file.

```bash
mmoney auth logout
```

### auth status

Check authentication status.

```bash
mmoney auth status
# Output: "Authenticated (keychain)" or "Not authenticated"
```

---

## accounts

Account management. Equivalent to the Accounts page in Monarch Money.

### accounts list

List all accounts linked to your profile.

```bash
mmoney accounts list
mmoney -f json accounts list
```

**Output fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique account identifier |
| `displayName` | string | User-facing account name |
| `type.name` | string | Account type (checking, savings, credit, etc.) |
| `subtype.name` | string | Account subtype |
| `currentBalance` | number | Current balance |
| `availableBalance` | number | Available balance (if applicable) |
| `isAsset` | boolean | True if asset, false if liability |
| `includeInNetWorth` | boolean | Include in net worth calculation |
| `institution.name` | string | Financial institution name |
| `syncDisabled` | boolean | Whether sync is disabled |
| `updatedAt` | string | Last update timestamp (ISO 8601) |

### accounts types

List available account types for creating manual accounts.

```bash
mmoney accounts types
```

### accounts refresh

Refresh account data from linked institutions.

```bash
# Refresh all accounts and wait for completion
mmoney accounts refresh

# Refresh specific accounts
mmoney accounts refresh --account-ids ACC_ID_1 --account-ids ACC_ID_2

# Start refresh without waiting
mmoney accounts refresh --no-wait

# Custom timeout (default: 300 seconds)
mmoney accounts refresh --timeout 600
```

| Option | Short | Description |
|--------|-------|-------------|
| `--account-ids` | `-a` | Account IDs to refresh (default: all) |
| `--wait/--no-wait` | | Wait for refresh to complete (default: true) |
| `--timeout` | | Timeout in seconds for --wait (default: 300) |

### accounts refresh-status

Check if account refresh is complete.

```bash
mmoney accounts refresh-status
mmoney accounts refresh-status --account-ids ACC_ID
```

### accounts create ⚠️

Create a manual account. Requires `--allow-mutations`.

```bash
mmoney --allow-mutations accounts create \
  --name "My Account" \
  --type checking \
  --subtype personal \
  --balance 1000.00
```

| Option | Short | Required | Description |
|--------|-------|----------|-------------|
| `--name` | `-n` | Yes | Account name |
| `--type` | | Yes | Account type |
| `--subtype` | | Yes | Account subtype |
| `--balance` | `-b` | No | Initial balance (default: 0) |
| `--in-net-worth/--not-in-net-worth` | | No | Include in net worth (default: true) |

### accounts update ⚠️

Update an account. Requires `--allow-mutations`.

```bash
mmoney --allow-mutations accounts update ACC_ID --name "New Name" --balance 500
```

| Option | Short | Description |
|--------|-------|-------------|
| `--name` | `-n` | Account name |
| `--balance` | `-b` | Account balance |
| `--type` | | Account type |
| `--subtype` | | Account subtype |
| `--in-net-worth` | | Include in net worth |
| `--hide-from-summary` | | Hide from summary list |
| `--hide-transactions` | | Hide transactions from reports |

### accounts delete ⚠️

Delete an account. Requires `--allow-mutations` and confirmation.

```bash
mmoney --allow-mutations accounts delete ACC_ID
```

---

## transactions

Transaction management. Equivalent to the Transactions page in Monarch Money.

### transactions list

List transactions with optional filters.

```bash
# Basic listing
mmoney transactions list

# With filters
mmoney transactions list \
  --limit 50 \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --search "coffee" \
  --category-id CAT_ID \
  --account-id ACC_ID
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--limit` | `-l` | 100 | Number of transactions |
| `--offset` | | 0 | Offset for pagination |
| `--start-date` | `-s` | | Start date (YYYY-MM-DD) |
| `--end-date` | `-e` | | End date (YYYY-MM-DD) |
| `--search` | `-q` | | Search query |
| `--category-id` | `-c` | | Filter by category ID (repeatable) |
| `--account-id` | `-a` | | Filter by account ID (repeatable) |
| `--tag-id` | `-t` | | Filter by tag ID (repeatable) |
| `--has-attachments` | | | Filter by attachment presence |
| `--has-notes` | | | Filter by notes presence |
| `--is-split` | | | Filter split transactions |
| `--is-recurring` | | | Filter recurring transactions |

**Output fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique transaction identifier |
| `date` | string | Transaction date (YYYY-MM-DD) |
| `amount` | number | Amount (negative for expenses) |
| `merchant.name` | string | Merchant name |
| `category.name` | string | Category name |
| `account.displayName` | string | Account name |
| `notes` | string | User notes |
| `isPending` | boolean | Pending status |
| `isRecurring` | boolean | Recurring transaction |
| `isSplit` | boolean | Has splits |
| `tags` | array | Applied tags |

### transactions get

Get details for a specific transaction.

```bash
mmoney transactions get TXN_ID
```

### transactions summary

Get transactions summary statistics.

```bash
mmoney transactions summary
```

### transactions splits

Get split details for a transaction.

```bash
mmoney transactions splits TXN_ID
```

### transactions create ⚠️

Create a transaction. Requires `--allow-mutations`.

```bash
mmoney --allow-mutations transactions create \
  --date 2024-01-15 \
  --account-id ACC_ID \
  --amount -25.00 \
  --merchant "Coffee Shop" \
  --category-id CAT_ID \
  --notes "Morning coffee"
```

| Option | Short | Required | Description |
|--------|-------|----------|-------------|
| `--date` | `-d` | Yes | Transaction date (YYYY-MM-DD) |
| `--account-id` | `-a` | Yes | Account ID |
| `--amount` | | Yes | Amount (negative for expense) |
| `--merchant` | `-m` | Yes | Merchant name |
| `--category-id` | `-c` | Yes | Category ID |
| `--notes` | `-n` | No | Notes |
| `--update-balance/--no-update-balance` | | No | Update account balance |

### transactions update ⚠️

Update a transaction. Requires `--allow-mutations`.

```bash
mmoney --allow-mutations transactions update TXN_ID \
  --category-id NEW_CAT_ID \
  --notes "Updated notes"
```

| Option | Short | Description |
|--------|-------|-------------|
| `--category-id` | `-c` | Category ID |
| `--merchant` | `-m` | Merchant name |
| `--amount` | | Amount |
| `--date` | `-d` | Date (YYYY-MM-DD) |
| `--notes` | `-n` | Notes |
| `--hide-from-reports` | | Hide from reports |
| `--needs-review` | | Needs review flag |

### transactions delete ⚠️

Delete a transaction. Requires `--allow-mutations` and confirmation.

```bash
mmoney --allow-mutations transactions delete TXN_ID
```

---

## holdings

Investment holdings and history. Equivalent to the Investments section in Monarch Money.

### holdings list

List holdings for a specific investment account.

```bash
mmoney holdings list ACCOUNT_ID
```

**Output fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Holding identifier |
| `name` | string | Security name |
| `ticker` | string | Ticker symbol |
| `quantity` | number | Number of shares |
| `price` | number | Current price per share |
| `value` | number | Total value |
| `costBasis` | number | Cost basis |

### holdings history

Get balance history for an account.

```bash
mmoney holdings history ACCOUNT_ID
```

### holdings snapshots

Get aggregate balance snapshots across accounts.

```bash
mmoney holdings snapshots
mmoney holdings snapshots --start-date 2024-01-01 --end-date 2024-12-31
mmoney holdings snapshots --account-type investment
```

| Option | Short | Description |
|--------|-------|-------------|
| `--start-date` | `-s` | Start date (YYYY-MM-DD) |
| `--end-date` | `-e` | End date (YYYY-MM-DD) |
| `--account-type` | `-t` | Filter by account type |

### holdings balances

Get recent account balances.

```bash
mmoney holdings balances
mmoney holdings balances --start-date 2024-01-01
```

---

## categories

Transaction categories. Equivalent to Categories in Monarch Money settings.

### categories list

List all categories.

```bash
mmoney categories list
```

**Output fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Category identifier |
| `name` | string | Category name |
| `icon` | string | Category icon |
| `group.name` | string | Category group name |
| `isSystemCategory` | boolean | System vs custom category |

### categories groups

List category groups.

```bash
mmoney categories groups
```

### categories create ⚠️

Create a category. Requires `--allow-mutations`.

```bash
mmoney --allow-mutations categories create \
  --group-id GROUP_ID \
  --name "My Category" \
  --icon "🏷️"
```

| Option | Short | Required | Description |
|--------|-------|----------|-------------|
| `--group-id` | `-g` | Yes | Category group ID |
| `--name` | `-n` | Yes | Category name |
| `--icon` | | No | Category icon (default: ❓) |
| `--rollover/--no-rollover` | | No | Enable budget rollover |

### categories delete ⚠️

Delete a category. Requires `--allow-mutations` and confirmation.

```bash
mmoney --allow-mutations categories delete CAT_ID
```

---

## tags

Transaction tags. Equivalent to Tags in Monarch Money.

### tags list

List all tags.

```bash
mmoney tags list
```

**Output fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Tag identifier |
| `name` | string | Tag name |
| `color` | string | Tag color |

### tags create ⚠️

Create a tag. Requires `--allow-mutations`.

```bash
mmoney --allow-mutations tags create --name "My Tag" --color blue
```

| Option | Short | Required | Description |
|--------|-------|----------|-------------|
| `--name` | `-n` | Yes | Tag name |
| `--color` | `-c` | No | Tag color (default: blue) |

### tags set ⚠️

Set tags on a transaction. Requires `--allow-mutations`.

```bash
mmoney --allow-mutations tags set TXN_ID --tag-id TAG_ID_1 --tag-id TAG_ID_2
```

---

## budgets

Budget management. Equivalent to the Budgets page in Monarch Money.

### budgets list

List budgets.

```bash
mmoney budgets list
mmoney budgets list --start-date 2024-01-01 --end-date 2024-12-31
```

| Option | Short | Description |
|--------|-------|-------------|
| `--start-date` | `-s` | Start date (YYYY-MM-DD) |
| `--end-date` | `-e` | End date (YYYY-MM-DD) |

### budgets set ⚠️

Set a budget amount. Requires `--allow-mutations`.

```bash
mmoney --allow-mutations budgets set \
  --amount 500.00 \
  --category-id CAT_ID \
  --start-date 2024-01-01
```

| Option | Short | Required | Description |
|--------|-------|----------|-------------|
| `--amount` | `-a` | Yes | Budget amount |
| `--category-id` | `-c` | No | Category ID |
| `--category-group-id` | `-g` | No | Category group ID |
| `--timeframe` | | No | Timeframe (default: month) |
| `--start-date` | `-s` | No | Start date |
| `--apply-to-future/--no-apply-to-future` | | No | Apply to future months |

---

## cashflow

Cashflow reports. Equivalent to the Cashflow page in Monarch Money.

### cashflow summary

Get cashflow summary (income, expenses, savings rate).

```bash
mmoney cashflow summary
mmoney cashflow summary --start-date 2024-01-01 --end-date 2024-12-31
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--start-date` | `-s` | | Start date (YYYY-MM-DD) |
| `--end-date` | `-e` | | End date (YYYY-MM-DD) |
| `--limit` | `-l` | 100 | Record limit |

### cashflow details

Get detailed cashflow by category and merchant.

```bash
mmoney cashflow details
mmoney cashflow details --start-date 2024-01-01 --end-date 2024-12-31
```

---

## recurring

Recurring transactions. Equivalent to the Recurring page in Monarch Money.

### recurring list

List recurring transactions.

```bash
mmoney recurring list
mmoney recurring list --start-date 2024-01-01 --end-date 2024-12-31
```

| Option | Short | Description |
|--------|-------|-------------|
| `--start-date` | `-s` | Start date (YYYY-MM-DD) |
| `--end-date` | `-e` | End date (YYYY-MM-DD) |

---

## institutions

Linked financial institutions.

### institutions list

List all linked institutions.

```bash
mmoney institutions list
```

**Output fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Institution identifier |
| `name` | string | Institution name |
| `logo` | string | Logo URL |
| `status` | string | Connection status |
| `lastUpdate` | string | Last successful update |

---

## subscription

Monarch Money subscription status.

### subscription status

Get subscription details.

```bash
mmoney subscription status
```

---

## Error Handling

All errors return structured JSON:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": "Additional context"
  }
}
```

**Common error codes:**

| Code | Description |
|------|-------------|
| `AUTH_REQUIRED` | Not logged in |
| `AUTH_FAILED` | Invalid credentials |
| `MUTATION_BLOCKED` | Need `--allow-mutations` |
| `VALIDATION_MISSING_FIELD` | Required parameter missing |
| `NOT_FOUND` | Resource not found |
| `API_ERROR` | Monarch Money API error |
| `API_TIMEOUT` | Request timeout |
