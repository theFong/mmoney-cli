# JSON Schemas

Output schemas for mmoney CLI commands, verified against actual API responses.

> Use `--format json` or `-f json` to get JSON output.

---

## Data Model Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Institution   │────▶│   Credential    │────▶│    Account      │
│  (Bank/Broker)  │     │  (Connection)   │     │ (Checking, etc) │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                              ┌──────────────────────────┼──────────────────────────┐
                              │                          │                          │
                              ▼                          ▼                          ▼
                    ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐
                    │   Transaction   │        │    Holding      │        │ Balance History │
                    │   (Purchase)    │        │  (Investment)   │        │   (Snapshots)   │
                    └────────┬────────┘        └─────────────────┘        └─────────────────┘
                             │
              ┌──────────────┼──────────────┬──────────────┐
              │              │              │              │
              ▼              ▼              ▼              ▼
    ┌─────────────────┐ ┌─────────┐ ┌─────────────┐ ┌───────────────┐
    │    Category     │ │Merchant │ │    Tags     │ │   Recurring   │
    │ (Groceries,etc) │ │(Amazon) │ │(Tax,Business│ │   Stream      │
    └────────┬────────┘ └─────────┘ └─────────────┘ └───────────────┘
             │
             ▼
    ┌─────────────────┐
    │ Category Group  │
    │ (Food & Drink)  │
    └─────────────────┘
```

### Key Relationships

| Parent | Child | Relationship |
|--------|-------|--------------|
| Institution | Credential | One institution can have multiple credentials (connections) |
| Credential | Account | One credential links multiple accounts from same institution |
| Account | Transaction | Transactions belong to one account |
| Account | Holding | Investment holdings belong to one account |
| Transaction | Category | Each transaction has one category |
| Transaction | Merchant | Each transaction has one merchant |
| Transaction | Tags | Many-to-many: transactions can have multiple tags |
| Category | Category Group | Categories belong to one group (e.g., "Groceries" → "Food & Drink") |

---

## Account Object

**Source:** `mmoney accounts list`

**Business Context:** Accounts represent your financial accounts - bank accounts, credit cards, investment accounts, loans, etc. Monarch connects to 13,000+ financial institutions via Plaid, MX, and other providers.

```json
{
  "id": "221167361477926526",
  "displayName": "Hub (...4887)",
  "syncDisabled": false,
  "deactivatedAt": null,
  "isHidden": false,
  "isAsset": true,
  "mask": "4887",
  "createdAt": "2025-09-07T05:20:32.266280+00:00",
  "updatedAt": "2026-01-21T19:37:39.646324+00:00",
  "displayLastUpdatedAt": "2026-01-21T19:37:39.645057+00:00",
  "currentBalance": 2266.44,
  "displayBalance": 2266.44,
  "includeInNetWorth": true,
  "hideFromList": false,
  "hideTransactionsFromReports": false,
  "includeBalanceInNetWorth": true,
  "includeInGoalBalance": true,
  "dataProvider": "plaid",
  "dataProviderAccountId": "8o97bxYxr7FRLZ6R56ObC8ppqqozAgtmqaxP8",
  "isManual": false,
  "transactionsCount": 215,
  "holdingsCount": 0,
  "order": 2,
  "logoUrl": "https://api.monarch.com/cdn-cgi/image/width=128/images/institution/...",
  "type": {
    "name": "depository",
    "display": "Cash",
    "__typename": "AccountType"
  },
  "subtype": {
    "name": "checking",
    "display": "Checking",
    "__typename": "AccountSubtype"
  },
  "credential": {
    "id": "221167360635919876",
    "updateRequired": false,
    "disconnectedFromDataProviderAt": null,
    "dataProvider": "PLAID",
    "institution": {
      "id": "75130105427928310",
      "plaidInstitutionId": "ins_127989",
      "name": "Bank of America",
      "status": "HEALTHY",
      "__typename": "Institution"
    },
    "__typename": "Credential"
  },
  "institution": {
    "id": "75130105427928310",
    "name": "Bank of America",
    "primaryColor": "#e31837",
    "url": "https://www.bankofamerica.com",
    "__typename": "Institution"
  },
  "__typename": "Account"
}
```

### Account Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier |
| `displayName` | string | User-facing name (often includes last 4 digits) |
| `mask` | string | Last 4 digits of account number |
| `isAsset` | boolean | `true` = asset (adds to net worth), `false` = liability (subtracts) |
| `currentBalance` | number | Current balance from institution |
| `displayBalance` | number | Balance shown to user (always positive for credit cards) |
| `includeInNetWorth` | boolean | Include in net worth calculation |
| `syncDisabled` | boolean | User disabled sync for this account |
| `isManual` | boolean | `true` = manually created, `false` = linked to institution |
| `dataProvider` | string | Data provider: `plaid`, `mx`, `coinbase`, etc. |
| `transactionsCount` | number | Number of transactions in this account |
| `holdingsCount` | number | Number of investment holdings (for investment accounts) |
| `type.name` | string | Account type: `depository`, `credit`, `investment`, `loan`, `other` |
| `subtype.name` | string | Subtype: `checking`, `savings`, `credit_card`, `brokerage`, etc. |
| `credential` | object | Connection to institution (shared across accounts from same login) |
| `institution` | object | Financial institution details |

### Account Types

| Type | Subtypes | isAsset |
|------|----------|---------|
| `depository` | checking, savings, money_market, cd | true |
| `credit` | credit_card | false |
| `investment` | brokerage, 401k, ira, roth, 529 | true |
| `loan` | mortgage, student, auto, personal | false |
| `other` | manual | varies |

---

## Transaction Object

**Source:** `mmoney transactions list`

**Business Context:** Transactions are the core of Monarch - every purchase, payment, transfer, and deposit. Monarch auto-categorizes transactions and lets you create rules for future categorization.

```json
{
  "id": "233547563282554290",
  "amount": -160.0,
  "pending": true,
  "date": "2026-01-21",
  "hideFromReports": false,
  "plaidName": "COMCAST / XFINITY",
  "notes": null,
  "isRecurring": true,
  "reviewStatus": null,
  "needsReview": false,
  "attachments": [],
  "isSplitTransaction": false,
  "createdAt": "2026-01-21T20:58:32.764148+00:00",
  "updatedAt": "2026-01-21T20:59:54.101960+00:00",
  "category": {
    "id": "221167178519240429",
    "name": "Internet & Cable",
    "__typename": "Category"
  },
  "merchant": {
    "name": "Comcast",
    "id": "221167538691465007",
    "transactionsCount": 15,
    "__typename": "Merchant"
  },
  "account": {
    "id": "221167519326363292",
    "displayName": "CREDIT CARD (...6998)",
    "__typename": "Account"
  },
  "tags": [],
  "__typename": "Transaction"
}
```

### Transaction Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier |
| `amount` | number | **Negative = expense, Positive = income** |
| `pending` | boolean | Transaction still pending at institution |
| `date` | string | Transaction date (YYYY-MM-DD) |
| `plaidName` | string | Original description from institution |
| `notes` | string | User-added notes |
| `isRecurring` | boolean | Linked to a recurring transaction stream |
| `needsReview` | boolean | Flagged for user review |
| `isSplitTransaction` | boolean | Has been split into multiple categories |
| `hideFromReports` | boolean | Excluded from reports/budgets |
| `category` | object | Assigned category |
| `merchant` | object | Cleaned merchant name and ID |
| `account` | object | Source account |
| `tags` | array | User-applied tags |
| `attachments` | array | Attached receipts/documents |

### Transaction List Response

The `transactions list` command returns a wrapper:

```json
{
  "allTransactions": {
    "totalCount": 4226,
    "results": [ /* array of transactions */ ],
    "__typename": "TransactionList"
  },
  "transactionRules": [ /* auto-categorization rules */ ]
}
```

---

## Category Object

**Source:** `mmoney categories list`

**Business Context:** Categories organize your spending. Monarch provides ~50 system categories across groups like "Food & Drink", "Transportation", "Housing". You can create custom categories too.

```json
{
  "id": "221167178519240459",
  "order": 0,
  "name": "Advertising & Promotion",
  "systemCategory": "advertising_promotion",
  "isSystemCategory": true,
  "isDisabled": false,
  "updatedAt": "2025-09-07T05:17:37.839046+00:00",
  "createdAt": "2025-09-07T05:17:37.839041+00:00",
  "group": {
    "id": "221167178496171110",
    "name": "Business",
    "type": "expense",
    "__typename": "CategoryGroup"
  },
  "__typename": "Category"
}
```

### Category Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier |
| `name` | string | Display name |
| `systemCategory` | string | System category slug (null for custom) |
| `isSystemCategory` | boolean | `true` = built-in, `false` = user-created |
| `isDisabled` | boolean | Hidden from category picker |
| `order` | number | Display order within group |
| `group` | object | Parent category group |
| `group.type` | string | `expense` or `income` |

### Category Groups

| Group | Type | Example Categories |
|-------|------|-------------------|
| Food & Drink | expense | Groceries, Restaurants, Coffee Shops |
| Transportation | expense | Gas, Parking, Public Transit, Uber/Lyft |
| Housing | expense | Rent, Mortgage, Home Insurance |
| Utilities | expense | Electric, Gas, Water, Internet |
| Income | income | Salary, Interest, Dividends |
| Transfer | transfer | Account Transfer, Credit Card Payment |

---

## Tag Object

**Source:** `mmoney tags list`

**Business Context:** Tags provide flexible labeling beyond categories. Common uses: "Tax Deductible", "Business", "Reimbursable", "Split with Partner". A transaction can have multiple tags.

```json
{
  "id": "221167178477296858",
  "name": "Tax",
  "color": "#1348A5",
  "order": 0,
  "transactionCount": 0,
  "__typename": "TransactionTag"
}
```

### Tag Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier |
| `name` | string | Tag name |
| `color` | string | Hex color code |
| `order` | number | Display order |
| `transactionCount` | number | Number of tagged transactions |

### Default Tags

Monarch creates these tags by default:
- **Tax** - Tax-deductible expenses
- **Reimburse** - Expenses to be reimbursed
- **Split** - Split with someone else
- **Business** - Business expenses
- **Subscription** - Recurring subscriptions

---

## Recurring Transaction Object

**Source:** `mmoney recurring list`

**Business Context:** Monarch automatically detects recurring transactions (subscriptions, bills, loan payments) and projects future cash flow. You can see expected bills and when they're due.

```json
{
  "stream": {
    "id": "223439071093809030",
    "frequency": "monthly",
    "amount": -13.11,
    "isApproximate": false,
    "merchant": {
      "id": "221167416443231669",
      "name": "Google Workspace",
      "logoUrl": "https://...",
      "__typename": "Merchant"
    },
    "__typename": "RecurringTransactionStream"
  },
  "date": "2026-01-01",
  "isPast": true,
  "transactionId": "231911836597706516",
  "amount": -18.0,
  "amountDiff": -4.89,
  "category": {
    "id": "221167178519240458",
    "name": "Miscellaneous",
    "__typename": "Category"
  },
  "account": {
    "id": "221167519326363292",
    "displayName": "CREDIT CARD (...6998)",
    "__typename": "Account"
  },
  "__typename": "RecurringTransactionCalendarItem"
}
```

### Recurring Fields

| Field | Type | Description |
|-------|------|-------------|
| `stream.id` | string | Recurring stream identifier |
| `stream.frequency` | string | `weekly`, `monthly`, `yearly` |
| `stream.amount` | number | Expected amount |
| `stream.isApproximate` | boolean | Amount varies (e.g., utility bills) |
| `stream.merchant` | object | Merchant for this recurring item |
| `date` | string | Expected/actual date for this occurrence |
| `isPast` | boolean | Already occurred |
| `transactionId` | string | Linked transaction ID (if occurred) |
| `amount` | number | Actual amount (if occurred) |
| `amountDiff` | number | Difference from expected amount |

---

## Institution / Credential Object

**Source:** `mmoney institutions list`

**Business Context:** Institutions are your banks, brokers, etc. Credentials represent connections to those institutions. One credential can link multiple accounts (e.g., checking + savings from same bank login).

```json
{
  "id": "221167517439974925",
  "updateRequired": false,
  "disconnectedFromDataProviderAt": null,
  "displayLastUpdatedAt": "2026-01-21T20:58:27.630000+00:00",
  "dataProvider": "PLAID",
  "institution": {
    "id": "75130105427928310",
    "name": "Bank of America",
    "hasIssuesReported": false,
    "status": "HEALTHY",
    "balanceStatus": null,
    "transactionsStatus": null,
    "url": "https://www.bankofamerica.com",
    "__typename": "Institution"
  },
  "__typename": "Credential"
}
```

### Credential Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Credential identifier |
| `updateRequired` | boolean | Needs re-authentication |
| `disconnectedFromDataProviderAt` | string | When disconnected (null if connected) |
| `displayLastUpdatedAt` | string | Last successful sync |
| `dataProvider` | string | `PLAID`, `MX`, `COINBASE`, `FINICITY` |
| `institution` | object | Institution details |
| `institution.status` | string | `HEALTHY`, `DEGRADED`, `DOWN` |

---

## Cashflow Summary Object

**Source:** `mmoney cashflow summary`

**Business Context:** Cashflow shows your income vs expenses over time. Savings rate = (income - expenses) / income. This is the key metric for financial health.

```json
{
  "summary": [
    {
      "summary": {
        "sumIncome": 8576.87,
        "sumExpense": -166586.51,
        "savings": -158009.64,
        "savingsRate": 0.0,
        "__typename": "TransactionsSummary"
      },
      "__typename": "AggregateData"
    }
  ]
}
```

### Cashflow Fields

| Field | Type | Description |
|-------|------|-------------|
| `sumIncome` | number | Total income (positive) |
| `sumExpense` | number | Total expenses (negative) |
| `savings` | number | Net savings (income + expense) |
| `savingsRate` | number | Savings as percentage of income (0-1) |

---

## Error Object

All errors return this structure:

```json
{
  "error": {
    "code": "AUTH_REQUIRED",
    "message": "Authentication required",
    "details": "Run 'mmoney auth login' first."
  }
}
```

### Error Codes

| Code | Exit | Description |
|------|------|-------------|
| `AUTH_REQUIRED` | 2 | Not logged in |
| `AUTH_FAILED` | 2 | Invalid credentials |
| `AUTH_MFA_REQUIRED` | 2 | MFA code needed |
| `MUTATION_BLOCKED` | 6 | Need `--allow-mutations` flag |
| `VALIDATION_MISSING_FIELD` | 4 | Required parameter missing |
| `NOT_FOUND` | 3 | Resource not found |
| `API_ERROR` | 5 | Monarch Money API error |
| `API_TIMEOUT` | 5 | Request timeout |

---

## Sources

- [Monarch Money](https://www.monarchmoney.com) - Official website
- [Monarch Money Help](https://help.monarchmoney.com) - Official documentation
- [NerdWallet Review](https://www.nerdwallet.com/finance/learn/monarch-money-app-review) - Feature overview
- [Experian Review](https://www.experian.com/blogs/ask-experian/monarch-money-review/) - Detailed breakdown
