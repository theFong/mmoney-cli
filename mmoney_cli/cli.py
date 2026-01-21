#!/usr/bin/env python3
"""Monarch Money CLI - Command line interface for the Monarch Money API."""

import asyncio
import csv
import functools
import io
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any, Optional

import click
import keyring
from monarchmoney import MonarchMoney

# Context keys
_ALLOW_MUTATIONS = "allow_mutations"
_OUTPUT_FORMAT = "output_format"

# Config directory in user's home
_CONFIG_DIR = Path.home() / ".mmoney"
_SESSION_FILE = _CONFIG_DIR / "session.pickle"


def _ensure_config_dir():
    """Create config directory if it doesn't exist."""
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)


__version__ = "0.1.0"


# ============================================================================
# Exit Codes
# ============================================================================


class ExitCode:
    """Standard exit codes for agent-friendly error handling."""

    SUCCESS = 0
    GENERAL_ERROR = 1
    AUTH_ERROR = 2
    NOT_FOUND = 3
    VALIDATION_ERROR = 4
    API_ERROR = 5
    MUTATION_BLOCKED = 6


# ============================================================================
# Error Codes
# ============================================================================


class ErrorCode:
    """Error codes for structured error responses."""

    # Authentication errors
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTH_FAILED = "AUTH_FAILED"
    AUTH_MFA_REQUIRED = "AUTH_MFA_REQUIRED"
    AUTH_MFA_FAILED = "AUTH_MFA_FAILED"
    AUTH_INVALID_TOKEN = "AUTH_INVALID_TOKEN"

    # Validation errors
    VALIDATION_MISSING_FIELD = "VALIDATION_MISSING_FIELD"
    VALIDATION_INVALID_VALUE = "VALIDATION_INVALID_VALUE"
    VALIDATION_INVALID_DATE = "VALIDATION_INVALID_DATE"

    # API errors
    API_ERROR = "API_ERROR"
    API_TIMEOUT = "API_TIMEOUT"
    API_RATE_LIMIT = "API_RATE_LIMIT"

    # Resource errors
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"

    # Permission errors
    MUTATION_BLOCKED = "MUTATION_BLOCKED"

    # General errors
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


def output_error(
    code: str, message: str, details: str = None, exit_code: int = ExitCode.GENERAL_ERROR
):
    """Output a structured error and exit.

    Args:
        code: Machine-readable error code (e.g., "AUTH_REQUIRED")
        message: Human-readable error message
        details: Optional additional details or suggestions
        exit_code: Process exit code (default: 1)

    Output format:
        {
            "error": {
                "code": "AUTH_REQUIRED",
                "message": "Authentication required",
                "details": "Run 'mmoney auth login' first."
            }
        }
    """
    error_data = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    if details:
        error_data["error"]["details"] = details

    click.echo(json.dumps(error_data, indent=2), err=True)
    sys.exit(exit_code)


# ============================================================================
# Output Formats
# ============================================================================


class OutputFormat:
    """Available output formats."""

    JSON = "json"
    JSONL = "jsonl"
    CSV = "csv"
    TEXT = "text"


def _flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """Flatten nested dictionary for CSV/text output."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep).items())
        elif isinstance(v, list):
            # Convert list to string representation
            items.append((new_key, json.dumps(v, default=str) if v else ""))
        else:
            items.append((new_key, v))
    return dict(items)


def _extract_records(data: Any) -> list[dict]:
    """Extract a list of records from API response for tabular output.

    Handles common API response patterns:
    - {"accounts": [...]} -> [...]
    - {"allTransactions": {"results": [...]}} -> [...]
    - {...} -> [{...}]
    """
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        # Try common keys that contain record lists
        list_keys = [
            "accounts",
            "results",
            "transactions",
            "categories",
            "householdTransactionTags",
            "credentials",
            "budgetData",
            "recurringTransactions",
            "splits",
            "snapshots",
            "history",
        ]

        # Check for nested results (e.g., allTransactions.results)
        for key, value in data.items():
            if isinstance(value, dict) and "results" in value:
                return value["results"]
            if key in list_keys and isinstance(value, list):
                return value

        # Single record - wrap in list
        return [data]

    return []


def output_json(data, pretty=True):
    """Output data as JSON."""
    if pretty:
        click.echo(json.dumps(data, indent=2, default=str))
    else:
        click.echo(json.dumps(data, default=str))


def output_jsonl(data: Any):
    """Output data as JSON Lines (one JSON object per line).

    Good for streaming and line-by-line processing.
    """
    records = _extract_records(data)
    for record in records:
        click.echo(json.dumps(record, default=str))


def output_csv(data: Any):
    """Output data as CSV.

    Good for tabular data like transactions and accounts.
    """
    records = _extract_records(data)
    if not records:
        return

    # Flatten all records to get all possible keys
    flattened = [_flatten_dict(r) if isinstance(r, dict) else {"value": r} for r in records]

    # Collect all keys from all records
    all_keys = set()
    for record in flattened:
        all_keys.update(record.keys())
    fieldnames = sorted(all_keys)

    # Write CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for record in flattened:
        writer.writerow({k: str(v) if v is not None else "" for k, v in record.items()})

    click.echo(output.getvalue().rstrip())


def output_text(data: Any):
    """Output data as simple key=value text.

    Good for grep/awk and simple extraction.
    """
    records = _extract_records(data)
    for i, record in enumerate(records):
        if i > 0:
            click.echo("---")  # Record separator
        if isinstance(record, dict):
            flat = _flatten_dict(record)
            for key, value in sorted(flat.items()):
                click.echo(f"{key}={value if value is not None else ''}")
        else:
            click.echo(str(record))


def output_data(data: Any, format: str = OutputFormat.JSON):
    """Output data in the specified format.

    Args:
        data: Data to output (usually API response dict)
        format: Output format (json, jsonl, csv, text)
    """
    if format == OutputFormat.JSONL:
        output_jsonl(data)
    elif format == OutputFormat.CSV:
        output_csv(data)
    elif format == OutputFormat.TEXT:
        output_text(data)
    else:
        output_json(data)


def run_async(coro):
    """Run an async coroutine."""
    return asyncio.run(coro)


# ============================================================================
# Keychain Storage
# ============================================================================

_KEYRING_SERVICE = "mmoney-cli"
_KEYRING_USERNAME = "monarch-token"


def save_token_to_keychain(token: str) -> bool:
    """Save auth token to system keychain.

    Returns True if successful, False if keyring is not available.
    """
    try:
        keyring.set_password(_KEYRING_SERVICE, _KEYRING_USERNAME, token)
        return True
    except Exception:
        return False


def load_token_from_keychain() -> Optional[str]:
    """Load auth token from system keychain.

    Returns the token if found, None otherwise.
    """
    try:
        return keyring.get_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
    except Exception:
        return None


def delete_token_from_keychain() -> bool:
    """Delete auth token from system keychain.

    Returns True if successful, False otherwise.
    """
    try:
        keyring.delete_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
        return True
    except Exception:
        return False


def get_client():
    """Get a MonarchMoney client with loaded session.

    Tries keychain first, then falls back to pickle file in ~/.mmoney/.
    """
    mm = MonarchMoney(session_file=str(_SESSION_FILE))

    # Try keychain first
    token = load_token_from_keychain()
    if token:
        mm.set_token(token)
        mm._headers["Authorization"] = f"Token {token}"
        return mm

    # Fall back to pickle file
    try:
        if _SESSION_FILE.exists():
            mm.load_session(str(_SESSION_FILE))
    except Exception:
        pass
    return mm


def get_output_format() -> str:
    """Get the output format from the current Click context."""
    ctx = click.get_current_context()
    # Walk up to root context to get format
    root = ctx
    while root.parent:
        root = root.parent
    return (root.obj or {}).get(_OUTPUT_FORMAT, OutputFormat.TEXT)


def output_result(data: Any):
    """Output result in the format specified by --format option."""
    output_data(data, get_output_format())


def require_mutations(f):
    """Decorator that blocks mutation commands in read-only mode.

    Apply this to any command that creates, updates, or deletes data.
    Users must pass --allow-mutations to use these commands.
    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        ctx = click.get_current_context()
        # Walk up to root context to get allow_mutations flag
        root = ctx
        while root.parent:
            root = root.parent
        if not (root.obj or {}).get(_ALLOW_MUTATIONS, False):
            output_error(
                code=ErrorCode.MUTATION_BLOCKED,
                message="This command modifies data. Use --allow-mutations to enable.",
                details="Example: mmoney --allow-mutations accounts create ...",
                exit_code=ExitCode.MUTATION_BLOCKED,
            )
        return f(*args, **kwargs)

    return wrapper


# ============================================================================
# Main CLI Group
# ============================================================================


@click.group()
@click.version_option(version=__version__, prog_name="mmoney")
@click.option(
    "--allow-mutations",
    is_flag=True,
    default=False,
    help="Enable commands that modify data (create, update, delete). Default: read-only.",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "jsonl", "csv", "text"]),
    default="text",
    help="Output format: text (default, key=value), json, jsonl (streaming), csv (tabular).",
)
@click.pass_context
def cli(ctx, allow_mutations, format):
    """Monarch Money CLI - Access your financial data from the command line.

    Built on top of the monarchmoneycommunity library.

    By default, runs in READ-ONLY mode for safety (ideal for AI agents).
    Use --allow-mutations to enable commands that modify data.

    \b
    OUTPUT FORMATS:
    - text: Key=value pairs (default, simple extraction, grep/awk)
    - json: Pretty-printed JSON (nested data, backward compatible)
    - jsonl: One JSON object per line (streaming, line processing)
    - csv: Comma-separated values (tabular data, spreadsheets)
    """
    ctx.ensure_object(dict)
    ctx.obj[_ALLOW_MUTATIONS] = allow_mutations
    ctx.obj[_OUTPUT_FORMAT] = format


# ============================================================================
# Auth Commands
# ============================================================================


@cli.group()
def auth():
    """Authentication and session management."""
    pass


@auth.command("login")
@click.option("--email", "-e", help="Email address")
@click.option("--password", "-p", help="Password")
@click.option("--mfa-secret", help="MFA secret key for automatic TOTP")
@click.option("--mfa-code", help="One-time MFA code (6 digits)")
@click.option("--token", "-t", help="Auth token from browser (bypasses captcha)")
@click.option("--device-uuid", "-d", help="Device UUID from browser (bypasses MFA)")
@click.option("--interactive/--no-interactive", "-i", default=True, help="Use interactive login")
def auth_login(email, password, mfa_secret, mfa_code, token, device_uuid, interactive):
    """Login to Monarch Money.

    AUTHENTICATION METHODS (in order of preference):

    1. EMAIL + PASSWORD + MFA SECRET (Best - longest lasting, fully automated):

    \b
       Enable MFA in Monarch settings. When setting up your authenticator app,
       copy the secret key (shown alongside the QR code). This lets the CLI
       generate TOTP codes automatically.
       mmoney auth login -e EMAIL -p PASSWORD --mfa-secret YOUR_SECRET --no-interactive

    2. EMAIL + PASSWORD + MFA CODE (Requires manual code entry):

    \b
       Use the 6-digit code from your authenticator app.
       mmoney auth login -e EMAIL -p PASSWORD --mfa-code 123456

    3. EMAIL + PASSWORD + DEVICE UUID (Requires browser):

    \b
       Get device UUID from browser to bypass MFA requirement:
       a. Open https://app.monarch.com and log in
       b. Open DevTools Console (F12 > Console tab)
       c. Run: copy(localStorage.getItem('monarchDeviceUUID'))
       d. Run: mmoney auth login -e EMAIL -p PASSWORD --device-uuid YOUR_UUID --no-interactive

    4. TOKEN FROM BROWSER (Shortest lived):

    \b
       Get token from browser Network tab:
       a. Open https://app.monarch.com and log in
       b. Open DevTools Network tab, refresh page
       c. Click any 'graphql' request
       d. In Headers, find 'Authorization: Token YOUR_TOKEN'
       e. Copy the token value (after 'Token ')
       f. Run: mmoney auth login --token YOUR_TOKEN
    """
    mm = MonarchMoney(session_file=str(_SESSION_FILE))

    if token:
        mm.set_token(token)
        if save_token_to_keychain(token):
            click.echo("Token saved to system keychain.")
        else:
            _ensure_config_dir()
            mm.save_session(str(_SESSION_FILE))
            click.echo(f"Token saved to file ({_SESSION_FILE}).")
        return

    if device_uuid:
        mm._headers["Device-UUID"] = device_uuid

    if mfa_code:
        # One-time MFA code login
        if not email or not password:
            output_error(
                code=ErrorCode.VALIDATION_MISSING_FIELD,
                message="--email and --password required with --mfa-code",
                details="Provide both email and password when using MFA code authentication.",
                exit_code=ExitCode.VALIDATION_ERROR,
            )
        try:
            run_async(mm.multi_factor_authenticate(email=email, password=password, code=mfa_code))
            if mm.token and save_token_to_keychain(mm.token):
                click.echo("Session saved to system keychain.")
            else:
                _ensure_config_dir()
                mm.save_session(str(_SESSION_FILE))
                click.echo(f"Session saved to file ({_SESSION_FILE}).")
        except Exception as e:
            output_error(
                code=ErrorCode.AUTH_MFA_FAILED,
                message="MFA login failed",
                details=str(e),
                exit_code=ExitCode.AUTH_ERROR,
            )
    elif interactive:
        run_async(mm.interactive_login(save_session=False))
        # Save to keychain after interactive login
        if mm.token and save_token_to_keychain(mm.token):
            click.echo("Session saved to system keychain.")
        else:
            _ensure_config_dir()
            mm.save_session(str(_SESSION_FILE))
            click.echo(f"Session saved to file ({_SESSION_FILE}).")
    else:
        if not email or not password:
            output_error(
                code=ErrorCode.VALIDATION_MISSING_FIELD,
                message="--email and --password required for non-interactive login",
                details="Provide both email and password for non-interactive authentication.",
                exit_code=ExitCode.VALIDATION_ERROR,
            )
        try:
            run_async(
                mm.login(
                    email=email, password=password, mfa_secret_key=mfa_secret, save_session=False
                )
            )
            # Save to keychain after successful login
            if mm.token and save_token_to_keychain(mm.token):
                click.echo("Session saved to system keychain.")
            else:
                _ensure_config_dir()
                mm.save_session(str(_SESSION_FILE))
                click.echo(f"Session saved to file ({_SESSION_FILE}).")
        except Exception as e:
            output_error(
                code=ErrorCode.AUTH_FAILED,
                message="Login failed",
                details=str(e),
                exit_code=ExitCode.AUTH_ERROR,
            )

    click.echo("Login successful!")


@auth.command("logout")
def auth_logout():
    """Delete saved session from keychain and file."""
    # Delete from keychain
    keychain_deleted = delete_token_from_keychain()

    # Also delete pickle file if it exists
    file_deleted = False
    if _SESSION_FILE.exists():
        try:
            _SESSION_FILE.unlink()
            file_deleted = True
        except Exception:
            pass

    if keychain_deleted or file_deleted:
        click.echo("Session deleted.")
    else:
        click.echo("No session found.")


@auth.command("status")
def auth_status():
    """Check authentication status."""
    # Check keychain first
    token = load_token_from_keychain()
    if token:
        click.echo("Authenticated (keychain)")
        return

    # Fall back to pickle file in ~/.mmoney/
    if _SESSION_FILE.exists():
        mm = MonarchMoney(session_file=str(_SESSION_FILE))
        try:
            mm.load_session(str(_SESSION_FILE))
            if mm.token:
                click.echo(f"Authenticated (file: {_SESSION_FILE})")
                return
        except Exception:
            pass

    click.echo("Not authenticated")


# ============================================================================
# Accounts Commands
# ============================================================================


@cli.group()
def accounts():
    """Account management."""
    pass


@accounts.command("list")
def accounts_list():
    """List all accounts."""
    mm = get_client()
    result = run_async(mm.get_accounts())
    output_result(result)


@accounts.command("types")
def accounts_types():
    """List available account types."""
    mm = get_client()
    result = run_async(mm.get_account_type_options())
    output_result(result)


@accounts.command("create")
@click.option("--name", "-n", required=True, help="Account name")
@click.option("--type", "account_type", required=True, help="Account type")
@click.option("--subtype", required=True, help="Account subtype")
@click.option("--balance", "-b", default=0.0, type=float, help="Initial balance")
@click.option("--in-net-worth/--not-in-net-worth", default=True, help="Include in net worth")
@require_mutations
def accounts_create(name, account_type, subtype, balance, in_net_worth):
    """Create a manual account."""
    mm = get_client()
    result = run_async(
        mm.create_manual_account(
            account_type=account_type,
            account_sub_type=subtype,
            is_in_net_worth=in_net_worth,
            account_name=name,
            account_balance=balance,
        )
    )
    output_result(result)


@accounts.command("update")
@click.argument("account_id")
@click.option("--name", "-n", help="Account name")
@click.option("--balance", "-b", type=float, help="Account balance")
@click.option("--type", "account_type", help="Account type")
@click.option("--subtype", help="Account subtype")
@click.option("--in-net-worth", type=bool, help="Include in net worth")
@click.option("--hide-from-summary", type=bool, help="Hide from summary list")
@click.option("--hide-transactions", type=bool, help="Hide transactions from reports")
@require_mutations
def accounts_update(
    account_id,
    name,
    balance,
    account_type,
    subtype,
    in_net_worth,
    hide_from_summary,
    hide_transactions,
):
    """Update an account."""
    mm = get_client()
    result = run_async(
        mm.update_account(
            account_id=account_id,
            account_name=name,
            account_balance=balance,
            account_type=account_type,
            account_sub_type=subtype,
            include_in_net_worth=in_net_worth,
            hide_from_summary_list=hide_from_summary,
            hide_transactions_from_reports=hide_transactions,
        )
    )
    output_result(result)


@accounts.command("delete")
@click.argument("account_id")
@click.confirmation_option(prompt="Are you sure you want to delete this account?")
@require_mutations
def accounts_delete(account_id):
    """Delete an account."""
    mm = get_client()
    result = run_async(mm.delete_account(account_id))
    output_result(result)


@accounts.command("refresh")
@click.option("--account-ids", "-a", multiple=True, help="Account IDs to refresh (default: all)")
@click.option("--wait/--no-wait", default=True, help="Wait for refresh to complete")
@click.option("--timeout", default=300, type=int, help="Timeout in seconds (for --wait)")
def accounts_refresh(account_ids, wait, timeout):
    """Refresh account data from institutions."""
    mm = get_client()
    account_list = list(account_ids) if account_ids else None

    if wait:
        result = run_async(
            mm.request_accounts_refresh_and_wait(account_ids=account_list, timeout=timeout)
        )
        click.echo(f"Refresh complete: {result}")
    else:
        result = run_async(mm.request_accounts_refresh(account_list or []))
        click.echo(f"Refresh started: {result}")


@accounts.command("refresh-status")
@click.option("--account-ids", "-a", multiple=True, help="Account IDs to check")
def accounts_refresh_status(account_ids):
    """Check if account refresh is complete."""
    mm = get_client()
    account_list = list(account_ids) if account_ids else None
    result = run_async(mm.is_accounts_refresh_complete(account_list))
    click.echo(f"Refresh complete: {result}")


# ============================================================================
# Holdings Commands
# ============================================================================


@cli.group()
def holdings():
    """Account holdings and history."""
    pass


@holdings.command("list")
@click.argument("account_id")
def holdings_list(account_id):
    """List holdings for an account."""
    mm = get_client()
    result = run_async(mm.get_account_holdings(int(account_id)))
    output_result(result)


@holdings.command("history")
@click.argument("account_id")
def holdings_history(account_id):
    """Get account balance history."""
    mm = get_client()
    result = run_async(mm.get_account_history(int(account_id)))
    output_result(result)


@holdings.command("snapshots")
@click.option("--start-date", "-s", help="Start date (YYYY-MM-DD)")
@click.option("--end-date", "-e", help="End date (YYYY-MM-DD)")
@click.option("--account-type", "-t", help="Filter by account type")
def holdings_snapshots(start_date, end_date, account_type):
    """Get aggregate balance snapshots."""
    mm = get_client()

    start = date.fromisoformat(start_date) if start_date else None
    end = date.fromisoformat(end_date) if end_date else None

    result = run_async(
        mm.get_aggregate_snapshots(start_date=start, end_date=end, account_type=account_type)
    )
    output_result(result)


@holdings.command("balances")
@click.option("--start-date", "-s", help="Start date (YYYY-MM-DD)")
def holdings_balances(start_date):
    """Get recent account balances."""
    mm = get_client()
    result = run_async(mm.get_recent_account_balances(start_date=start_date))
    output_result(result)


# ============================================================================
# Transactions Commands
# ============================================================================


@cli.group()
def transactions():
    """Transaction management."""
    pass


@transactions.command("list")
@click.option("--limit", "-l", default=100, type=int, help="Number of transactions")
@click.option("--offset", default=0, type=int, help="Offset for pagination")
@click.option("--start-date", "-s", help="Start date (YYYY-MM-DD)")
@click.option("--end-date", "-e", help="End date (YYYY-MM-DD)")
@click.option("--search", "-q", default="", help="Search query")
@click.option("--category-id", "-c", multiple=True, help="Filter by category ID")
@click.option("--account-id", "-a", multiple=True, help="Filter by account ID")
@click.option("--tag-id", "-t", multiple=True, help="Filter by tag ID")
@click.option("--has-attachments", type=bool, help="Filter by attachment presence")
@click.option("--has-notes", type=bool, help="Filter by notes presence")
@click.option("--is-split", type=bool, help="Filter split transactions")
@click.option("--is-recurring", type=bool, help="Filter recurring transactions")
def transactions_list(
    limit,
    offset,
    start_date,
    end_date,
    search,
    category_id,
    account_id,
    tag_id,
    has_attachments,
    has_notes,
    is_split,
    is_recurring,
):
    """List transactions."""
    mm = get_client()
    result = run_async(
        mm.get_transactions(
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
            search=search,
            category_ids=list(category_id),
            account_ids=list(account_id),
            tag_ids=list(tag_id),
            has_attachments=has_attachments,
            has_notes=has_notes,
            is_split=is_split,
            is_recurring=is_recurring,
        )
    )
    output_result(result)


@transactions.command("get")
@click.argument("transaction_id")
def transactions_get(transaction_id):
    """Get transaction details."""
    mm = get_client()
    result = run_async(mm.get_transaction_details(transaction_id))
    output_result(result)


@transactions.command("summary")
def transactions_summary():
    """Get transactions summary."""
    mm = get_client()
    result = run_async(mm.get_transactions_summary())
    output_result(result)


@transactions.command("splits")
@click.argument("transaction_id")
def transactions_splits(transaction_id):
    """Get transaction splits."""
    mm = get_client()
    result = run_async(mm.get_transaction_splits(transaction_id))
    output_result(result)


@transactions.command("create")
@click.option("--date", "-d", required=True, help="Transaction date (YYYY-MM-DD)")
@click.option("--account-id", "-a", required=True, help="Account ID")
@click.option("--amount", required=True, type=float, help="Amount (negative for expense)")
@click.option("--merchant", "-m", required=True, help="Merchant name")
@click.option("--category-id", "-c", required=True, help="Category ID")
@click.option("--notes", "-n", default="", help="Notes")
@click.option("--update-balance/--no-update-balance", default=False, help="Update account balance")
@require_mutations
def transactions_create(date, account_id, amount, merchant, category_id, notes, update_balance):
    """Create a transaction."""
    mm = get_client()
    result = run_async(
        mm.create_transaction(
            date=date,
            account_id=account_id,
            amount=amount,
            merchant_name=merchant,
            category_id=category_id,
            notes=notes,
            update_balance=update_balance,
        )
    )
    output_result(result)


@transactions.command("update")
@click.argument("transaction_id")
@click.option("--category-id", "-c", help="Category ID")
@click.option("--merchant", "-m", help="Merchant name")
@click.option("--amount", type=float, help="Amount")
@click.option("--date", "-d", help="Date (YYYY-MM-DD)")
@click.option("--notes", "-n", help="Notes")
@click.option("--hide-from-reports", type=bool, help="Hide from reports")
@click.option("--needs-review", type=bool, help="Needs review flag")
@require_mutations
def transactions_update(
    transaction_id,
    category_id,
    merchant,
    amount,
    date,
    notes,
    hide_from_reports,
    needs_review,
):
    """Update a transaction."""
    mm = get_client()
    result = run_async(
        mm.update_transaction(
            transaction_id=transaction_id,
            category_id=category_id,
            merchant_name=merchant,
            amount=amount,
            date=date,
            notes=notes,
            hide_from_reports=hide_from_reports,
            needs_review=needs_review,
        )
    )
    output_result(result)


@transactions.command("delete")
@click.argument("transaction_id")
@click.confirmation_option(prompt="Are you sure you want to delete this transaction?")
@require_mutations
def transactions_delete(transaction_id):
    """Delete a transaction."""
    mm = get_client()
    result = run_async(mm.delete_transaction(transaction_id))
    click.echo(f"Deleted: {result}")


# ============================================================================
# Categories Commands
# ============================================================================


@cli.group()
def categories():
    """Transaction categories."""
    pass


@categories.command("list")
def categories_list():
    """List all categories."""
    mm = get_client()
    result = run_async(mm.get_transaction_categories())
    output_result(result)


@categories.command("groups")
def categories_groups():
    """List category groups."""
    mm = get_client()
    result = run_async(mm.get_transaction_category_groups())
    output_result(result)


@categories.command("create")
@click.option("--group-id", "-g", required=True, help="Category group ID")
@click.option("--name", "-n", required=True, help="Category name")
@click.option("--icon", default="❓", help="Category icon")
@click.option("--rollover/--no-rollover", default=False, help="Enable rollover")
@require_mutations
def categories_create(group_id, name, icon, rollover):
    """Create a category."""
    mm = get_client()
    result = run_async(
        mm.create_transaction_category(
            group_id=group_id,
            transaction_category_name=name,
            icon=icon,
            rollover_enabled=rollover,
        )
    )
    output_result(result)


@categories.command("delete")
@click.argument("category_id")
@click.confirmation_option(prompt="Are you sure you want to delete this category?")
@require_mutations
def categories_delete(category_id):
    """Delete a category."""
    mm = get_client()
    result = run_async(mm.delete_transaction_category(category_id))
    click.echo(f"Deleted: {result}")


# ============================================================================
# Tags Commands
# ============================================================================


@cli.group()
def tags():
    """Transaction tags."""
    pass


@tags.command("list")
def tags_list():
    """List all tags."""
    mm = get_client()
    result = run_async(mm.get_transaction_tags())
    output_result(result)


@tags.command("create")
@click.option("--name", "-n", required=True, help="Tag name")
@click.option("--color", "-c", default="blue", help="Tag color")
@require_mutations
def tags_create(name, color):
    """Create a tag."""
    mm = get_client()
    result = run_async(mm.create_transaction_tag(name=name, color=color))
    output_result(result)


@tags.command("set")
@click.argument("transaction_id")
@click.option("--tag-id", "-t", multiple=True, required=True, help="Tag IDs to set")
@require_mutations
def tags_set(transaction_id, tag_id):
    """Set tags on a transaction."""
    mm = get_client()
    result = run_async(mm.set_transaction_tags(transaction_id=transaction_id, tag_ids=list(tag_id)))
    output_result(result)


# ============================================================================
# Budgets Commands
# ============================================================================


@cli.group()
def budgets():
    """Budget management."""
    pass


@budgets.command("list")
@click.option("--start-date", "-s", help="Start date (YYYY-MM-DD)")
@click.option("--end-date", "-e", help="End date (YYYY-MM-DD)")
def budgets_list(start_date, end_date):
    """List budgets."""
    mm = get_client()
    result = run_async(mm.get_budgets(start_date=start_date, end_date=end_date))
    output_result(result)


@budgets.command("set")
@click.option("--amount", "-a", required=True, type=float, help="Budget amount")
@click.option("--category-id", "-c", help="Category ID")
@click.option("--category-group-id", "-g", help="Category group ID")
@click.option("--timeframe", default="month", help="Timeframe (month, etc.)")
@click.option("--start-date", "-s", help="Start date (YYYY-MM-DD)")
@click.option(
    "--apply-to-future/--no-apply-to-future",
    default=False,
    help="Apply to future months",
)
@require_mutations
def budgets_set(amount, category_id, category_group_id, timeframe, start_date, apply_to_future):
    """Set a budget amount."""
    mm = get_client()
    result = run_async(
        mm.set_budget_amount(
            amount=amount,
            category_id=category_id,
            category_group_id=category_group_id,
            timeframe=timeframe,
            start_date=start_date,
            apply_to_future=apply_to_future,
        )
    )
    output_result(result)


# ============================================================================
# Cashflow Commands
# ============================================================================


@cli.group()
def cashflow():
    """Cashflow reports."""
    pass


@cashflow.command("summary")
@click.option("--start-date", "-s", help="Start date (YYYY-MM-DD)")
@click.option("--end-date", "-e", help="End date (YYYY-MM-DD)")
@click.option("--limit", "-l", default=100, type=int, help="Record limit")
def cashflow_summary(start_date, end_date, limit):
    """Get cashflow summary (income, expenses, savings)."""
    mm = get_client()
    result = run_async(
        mm.get_cashflow_summary(limit=limit, start_date=start_date, end_date=end_date)
    )
    output_result(result)


@cashflow.command("details")
@click.option("--start-date", "-s", help="Start date (YYYY-MM-DD)")
@click.option("--end-date", "-e", help="End date (YYYY-MM-DD)")
@click.option("--limit", "-l", default=100, type=int, help="Record limit")
def cashflow_details(start_date, end_date, limit):
    """Get detailed cashflow (by category, merchant)."""
    mm = get_client()
    result = run_async(mm.get_cashflow(limit=limit, start_date=start_date, end_date=end_date))
    output_result(result)


# ============================================================================
# Recurring Commands
# ============================================================================


@cli.group()
def recurring():
    """Recurring transactions."""
    pass


@recurring.command("list")
@click.option("--start-date", "-s", help="Start date (YYYY-MM-DD)")
@click.option("--end-date", "-e", help="End date (YYYY-MM-DD)")
def recurring_list(start_date, end_date):
    """List recurring transactions."""
    mm = get_client()
    result = run_async(mm.get_recurring_transactions(start_date=start_date, end_date=end_date))
    output_result(result)


# ============================================================================
# Institutions Commands
# ============================================================================


@cli.group()
def institutions():
    """Linked institutions."""
    pass


@institutions.command("list")
def institutions_list():
    """List linked institutions."""
    mm = get_client()
    result = run_async(mm.get_institutions())
    output_result(result)


# ============================================================================
# Subscription Commands
# ============================================================================


@cli.group()
def subscription():
    """Subscription status."""
    pass


@subscription.command("status")
def subscription_status():
    """Get subscription details."""
    mm = get_client()
    result = run_async(mm.get_subscription_details())
    output_result(result)


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    cli()
