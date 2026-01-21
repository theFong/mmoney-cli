"""Tests for mmoney CLI commands."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from click.testing import CliRunner

from mmoney_cli.cli import cli


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


# ============================================================================
# Auth Command Tests
# ============================================================================


class TestAuthCommands:
    """Tests for auth commands."""

    def test_auth_login_with_token(self, runner):
        """Test login with token."""
        with patch("mmoney_cli.cli.MonarchMoney") as MockMM, \
             patch("mmoney_cli.cli.save_token_to_keychain") as mock_keychain:
            mm_instance = MagicMock()
            MockMM.return_value = mm_instance
            mock_keychain.return_value = True  # Keychain save succeeds

            result = runner.invoke(cli, ["auth", "login", "--token", "test_token_123"])

            assert result.exit_code == 0
            assert "Token saved" in result.output
            mm_instance.set_token.assert_called_once_with("test_token_123")
            mock_keychain.assert_called_once_with("test_token_123")

    def test_auth_login_with_mfa_code(self, runner):
        """Test login with one-time MFA code."""
        with patch("mmoney_cli.cli.MonarchMoney") as MockMM:
            mm_instance = MagicMock()
            mm_instance.multi_factor_authenticate = AsyncMock()
            MockMM.return_value = mm_instance

            result = runner.invoke(
                cli,
                [
                    "auth", "login",
                    "--mfa-code", "123456",
                    "-e", "test@example.com",
                    "-p", "password123",
                ],
            )

            assert result.exit_code == 0
            assert "Login successful" in result.output
            mm_instance.multi_factor_authenticate.assert_called_once_with(
                email="test@example.com",
                password="password123",
                code="123456",
            )
            mm_instance.save_session.assert_called_once()

    def test_auth_login_mfa_code_requires_credentials(self, runner):
        """Test that MFA code login requires email and password."""
        with patch("mmoney_cli.cli.MonarchMoney") as MockMM:
            mm_instance = MagicMock()
            MockMM.return_value = mm_instance

            result = runner.invoke(cli, ["auth", "login", "--mfa-code", "123456"])

            assert result.exit_code == 4  # VALIDATION_ERROR
            error = json.loads(result.output)
            assert error["error"]["code"] == "VALIDATION_MISSING_FIELD"
            assert "--email and --password required" in error["error"]["message"]

    def test_auth_login_with_device_uuid(self, runner):
        """Test login with device UUID."""
        with patch("mmoney_cli.cli.MonarchMoney") as MockMM:
            mm_instance = MagicMock()
            mm_instance._headers = {}
            mm_instance.login = AsyncMock()
            MockMM.return_value = mm_instance

            result = runner.invoke(
                cli,
                [
                    "auth", "login",
                    "--device-uuid", "test-uuid-123",
                    "-e", "test@example.com",
                    "-p", "password123",
                    "--no-interactive",
                ],
            )

            assert result.exit_code == 0
            assert mm_instance._headers["Device-UUID"] == "test-uuid-123"

    def test_auth_login_non_interactive_requires_credentials(self, runner):
        """Test that non-interactive login requires email and password."""
        with patch("mmoney_cli.cli.MonarchMoney") as MockMM:
            mm_instance = MagicMock()
            MockMM.return_value = mm_instance

            result = runner.invoke(cli, ["auth", "login", "--no-interactive"])

            assert result.exit_code == 4  # VALIDATION_ERROR
            error = json.loads(result.output)
            assert error["error"]["code"] == "VALIDATION_MISSING_FIELD"
            assert "--email and --password required" in error["error"]["message"]

    def test_auth_logout(self, runner):
        """Test logout command."""
        with patch("mmoney_cli.cli.delete_token_from_keychain") as mock_delete:
            mock_delete.return_value = True

            result = runner.invoke(cli, ["auth", "logout"])

            assert result.exit_code == 0
            assert "Session deleted" in result.output
            mock_delete.assert_called_once()

    def test_auth_status_authenticated(self, runner):
        """Test status command when authenticated via keychain."""
        with patch("mmoney_cli.cli.load_token_from_keychain") as mock_load:
            mock_load.return_value = "valid_token"

            result = runner.invoke(cli, ["auth", "status"])

            assert result.exit_code == 0
            assert "Authenticated" in result.output
            assert "keychain" in result.output

    def test_auth_status_not_authenticated(self, runner):
        """Test status command when not authenticated."""
        with patch("mmoney_cli.cli.MonarchMoney") as MockMM:
            mm_instance = MagicMock()
            mm_instance.load_session.side_effect = Exception("No session")
            MockMM.return_value = mm_instance

            result = runner.invoke(cli, ["auth", "status"])

            assert result.exit_code == 0
            assert "Not authenticated" in result.output


# ============================================================================
# Accounts Command Tests
# ============================================================================


class TestAccountsCommands:
    """Tests for accounts commands."""

    def test_accounts_list(self, runner, mock_accounts_response):
        """Test accounts list command."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_accounts = AsyncMock(return_value=mock_accounts_response)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["-f", "json", "accounts", "list"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert "accounts" in output
            assert len(output["accounts"]) == 2

    def test_accounts_types(self, runner):
        """Test accounts types command."""
        mock_types = {"accountTypes": [{"name": "checking"}, {"name": "savings"}]}
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_account_type_options = AsyncMock(return_value=mock_types)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["-f", "json", "accounts", "types"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert "accountTypes" in output

    def test_accounts_create(self, runner):
        """Test accounts create command."""
        mock_result = {"createManualAccount": {"id": "new_123"}}
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.create_manual_account = AsyncMock(return_value=mock_result)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(
                cli,
                [
                    "--allow-mutations",
                    "accounts", "create",
                    "--name", "Test Account",
                    "--type", "depository",
                    "--subtype", "checking",
                    "--balance", "1000",
                ],
            )

            assert result.exit_code == 0
            mm_instance.create_manual_account.assert_called_once()

    def test_accounts_update(self, runner):
        """Test accounts update command."""
        mock_result = {"updateAccount": {"id": "123"}}
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.update_account = AsyncMock(return_value=mock_result)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(
                cli,
                ["--allow-mutations", "accounts", "update", "123", "--name", "Updated Name"],
            )

            assert result.exit_code == 0
            mm_instance.update_account.assert_called_once()

    def test_accounts_delete(self, runner):
        """Test accounts delete command."""
        mock_result = {"deleteAccount": True}
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.delete_account = AsyncMock(return_value=mock_result)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["--allow-mutations", "accounts", "delete", "123", "--yes"])

            assert result.exit_code == 0
            mm_instance.delete_account.assert_called_once_with("123")

    def test_accounts_refresh(self, runner):
        """Test accounts refresh command."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.request_accounts_refresh_and_wait = AsyncMock(return_value=True)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["accounts", "refresh"])

            assert result.exit_code == 0
            assert "Refresh complete" in result.output

    def test_accounts_refresh_status(self, runner):
        """Test accounts refresh-status command."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.is_accounts_refresh_complete = AsyncMock(return_value=True)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["accounts", "refresh-status"])

            assert result.exit_code == 0
            assert "Refresh complete: True" in result.output


# ============================================================================
# Transactions Command Tests
# ============================================================================


class TestTransactionsCommands:
    """Tests for transactions commands."""

    def test_transactions_list(self, runner, mock_transactions_response):
        """Test transactions list command."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_transactions = AsyncMock(return_value=mock_transactions_response)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["-f", "json", "transactions", "list", "--limit", "10"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert "allTransactions" in output

    def test_transactions_list_with_filters(self, runner, mock_transactions_response):
        """Test transactions list with filters."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_transactions = AsyncMock(return_value=mock_transactions_response)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(
                cli,
                [
                    "transactions", "list",
                    "--start-date", "2024-01-01",
                    "--end-date", "2024-01-31",
                    "--account-id", "123",
                    "--category-id", "cat_001",
                ],
            )

            assert result.exit_code == 0
            mm_instance.get_transactions.assert_called_once()

    def test_transactions_get(self, runner):
        """Test transactions get command."""
        mock_detail = {"transaction": {"id": "txn_001", "amount": -50.00}}
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_transaction_details = AsyncMock(return_value=mock_detail)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["-f", "json", "transactions", "get", "txn_001"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert output["transaction"]["id"] == "txn_001"

    def test_transactions_summary(self, runner):
        """Test transactions summary command."""
        mock_summary = {"summary": {"totalIncome": 5000, "totalExpenses": 3000}}
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_transactions_summary = AsyncMock(return_value=mock_summary)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["-f", "json", "transactions", "summary"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert "summary" in output

    def test_transactions_create(self, runner):
        """Test transactions create command."""
        mock_result = {"createTransaction": {"id": "new_txn"}}
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.create_transaction = AsyncMock(return_value=mock_result)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(
                cli,
                [
                    "--allow-mutations",
                    "transactions", "create",
                    "--date", "2024-01-15",
                    "--account-id", "123",
                    "--amount", "-50.00",
                    "--merchant", "Coffee Shop",
                    "--category-id", "cat_001",
                ],
            )

            assert result.exit_code == 0
            mm_instance.create_transaction.assert_called_once()

    def test_transactions_update(self, runner):
        """Test transactions update command."""
        mock_result = {"updateTransaction": {"id": "txn_001"}}
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.update_transaction = AsyncMock(return_value=mock_result)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(
                cli,
                ["--allow-mutations", "transactions", "update", "txn_001", "--merchant", "New Merchant"],
            )

            assert result.exit_code == 0
            mm_instance.update_transaction.assert_called_once()

    def test_transactions_delete(self, runner):
        """Test transactions delete command."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.delete_transaction = AsyncMock(return_value=True)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["--allow-mutations", "transactions", "delete", "txn_001", "--yes"])

            assert result.exit_code == 0
            mm_instance.delete_transaction.assert_called_once_with("txn_001")

    def test_transactions_splits(self, runner):
        """Test transactions splits command."""
        mock_splits = {"splits": [{"id": "split_001", "amount": -25.00}]}
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_transaction_splits = AsyncMock(return_value=mock_splits)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["-f", "json", "transactions", "splits", "txn_001"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert "splits" in output


# ============================================================================
# Holdings Command Tests
# ============================================================================


class TestHoldingsCommands:
    """Tests for holdings commands."""

    def test_holdings_list(self, runner, mock_holdings_response):
        """Test holdings list command."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_account_holdings = AsyncMock(return_value=mock_holdings_response)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["holdings", "list", "123"])

            assert result.exit_code == 0
            mm_instance.get_account_holdings.assert_called_once_with(123)

    def test_holdings_history(self, runner):
        """Test holdings history command."""
        mock_history = {"history": [{"date": "2024-01-01", "balance": 1000}]}
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_account_history = AsyncMock(return_value=mock_history)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["holdings", "history", "123"])

            assert result.exit_code == 0
            mm_instance.get_account_history.assert_called_once_with(123)

    def test_holdings_snapshots(self, runner):
        """Test holdings snapshots command."""
        mock_snapshots = {"snapshots": [{"date": "2024-01-01", "netWorth": 50000}]}
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_aggregate_snapshots = AsyncMock(return_value=mock_snapshots)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(
                cli,
                ["holdings", "snapshots", "--start-date", "2024-01-01", "--end-date", "2024-01-31"],
            )

            assert result.exit_code == 0
            mm_instance.get_aggregate_snapshots.assert_called_once()

    def test_holdings_balances(self, runner):
        """Test holdings balances command."""
        mock_balances = {"balances": [{"accountId": "123", "balance": 1000}]}
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_recent_account_balances = AsyncMock(return_value=mock_balances)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["-f", "json", "holdings", "balances"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert "balances" in output


# ============================================================================
# Categories Command Tests
# ============================================================================


class TestCategoriesCommands:
    """Tests for categories commands."""

    def test_categories_list(self, runner, mock_categories_response):
        """Test categories list command."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_transaction_categories = AsyncMock(return_value=mock_categories_response)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["-f", "json", "categories", "list"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert "categories" in output

    def test_categories_groups(self, runner):
        """Test categories groups command."""
        mock_groups = {"categoryGroups": [{"id": "grp_001", "name": "Expenses"}]}
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_transaction_category_groups = AsyncMock(return_value=mock_groups)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["-f", "json", "categories", "groups"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert "categoryGroups" in output

    def test_categories_create(self, runner):
        """Test categories create command."""
        mock_result = {"createCategory": {"id": "cat_new"}}
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.create_transaction_category = AsyncMock(return_value=mock_result)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(
                cli,
                ["--allow-mutations", "categories", "create", "--group-id", "grp_001", "--name", "New Category"],
            )

            assert result.exit_code == 0
            mm_instance.create_transaction_category.assert_called_once()

    def test_categories_delete(self, runner):
        """Test categories delete command."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.delete_transaction_category = AsyncMock(return_value=True)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["--allow-mutations", "categories", "delete", "cat_001", "--yes"])

            assert result.exit_code == 0
            mm_instance.delete_transaction_category.assert_called_once_with("cat_001")


# ============================================================================
# Tags Command Tests
# ============================================================================


class TestTagsCommands:
    """Tests for tags commands."""

    def test_tags_list(self, runner, mock_tags_response):
        """Test tags list command."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_transaction_tags = AsyncMock(return_value=mock_tags_response)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["-f", "json", "tags", "list"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert "householdTransactionTags" in output

    def test_tags_create(self, runner):
        """Test tags create command."""
        mock_result = {"createTag": {"id": "tag_new", "name": "New Tag"}}
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.create_transaction_tag = AsyncMock(return_value=mock_result)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["--allow-mutations", "tags", "create", "--name", "New Tag"])

            assert result.exit_code == 0
            mm_instance.create_transaction_tag.assert_called_once()

    def test_tags_set(self, runner):
        """Test tags set command."""
        mock_result = {"setTransactionTags": True}
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.set_transaction_tags = AsyncMock(return_value=mock_result)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(
                cli,
                ["--allow-mutations", "tags", "set", "txn_001", "--tag-id", "tag_001", "--tag-id", "tag_002"],
            )

            assert result.exit_code == 0
            mm_instance.set_transaction_tags.assert_called_once()


# ============================================================================
# Budgets Command Tests
# ============================================================================


class TestBudgetsCommands:
    """Tests for budgets commands."""

    def test_budgets_list(self, runner, mock_budgets_response):
        """Test budgets list command."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_budgets = AsyncMock(return_value=mock_budgets_response)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["-f", "json", "budgets", "list"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert "budgetData" in output

    def test_budgets_list_with_dates(self, runner, mock_budgets_response):
        """Test budgets list with date filters."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_budgets = AsyncMock(return_value=mock_budgets_response)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(
                cli,
                ["budgets", "list", "--start-date", "2024-01-01", "--end-date", "2024-01-31"],
            )

            assert result.exit_code == 0
            mm_instance.get_budgets.assert_called_once()

    def test_budgets_set(self, runner):
        """Test budgets set command."""
        mock_result = {"setBudget": True}
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.set_budget_amount = AsyncMock(return_value=mock_result)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(
                cli,
                ["--allow-mutations", "budgets", "set", "--amount", "500", "--category-id", "cat_001"],
            )

            assert result.exit_code == 0
            mm_instance.set_budget_amount.assert_called_once()


# ============================================================================
# Cashflow Command Tests
# ============================================================================


class TestCashflowCommands:
    """Tests for cashflow commands."""

    def test_cashflow_summary(self, runner, mock_cashflow_response):
        """Test cashflow summary command."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_cashflow_summary = AsyncMock(return_value=mock_cashflow_response)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["-f", "json", "cashflow", "summary"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert "summary" in output

    def test_cashflow_summary_with_dates(self, runner, mock_cashflow_response):
        """Test cashflow summary with date filters."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_cashflow_summary = AsyncMock(return_value=mock_cashflow_response)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(
                cli,
                ["cashflow", "summary", "--start-date", "2024-01-01", "--end-date", "2024-01-31"],
            )

            assert result.exit_code == 0
            mm_instance.get_cashflow_summary.assert_called_once()

    def test_cashflow_details(self, runner):
        """Test cashflow details command."""
        mock_details = {"cashflow": {"byCategory": [], "byMerchant": []}}
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_cashflow = AsyncMock(return_value=mock_details)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["-f", "json", "cashflow", "details"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert "cashflow" in output


# ============================================================================
# Recurring Command Tests
# ============================================================================


class TestRecurringCommands:
    """Tests for recurring commands."""

    def test_recurring_list(self, runner, mock_recurring_response):
        """Test recurring list command."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_recurring_transactions = AsyncMock(return_value=mock_recurring_response)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["-f", "json", "recurring", "list"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert "recurringTransactions" in output

    def test_recurring_list_with_dates(self, runner, mock_recurring_response):
        """Test recurring list with date filters."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_recurring_transactions = AsyncMock(return_value=mock_recurring_response)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(
                cli,
                ["recurring", "list", "--start-date", "2024-01-01", "--end-date", "2024-12-31"],
            )

            assert result.exit_code == 0
            mm_instance.get_recurring_transactions.assert_called_once()


# ============================================================================
# Institutions Command Tests
# ============================================================================


class TestInstitutionsCommands:
    """Tests for institutions commands."""

    def test_institutions_list(self, runner, mock_institutions_response):
        """Test institutions list command."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_institutions = AsyncMock(return_value=mock_institutions_response)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["-f", "json", "institutions", "list"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert "credentials" in output


# ============================================================================
# Subscription Command Tests
# ============================================================================


class TestSubscriptionCommands:
    """Tests for subscription commands."""

    def test_subscription_status(self, runner, mock_subscription_response):
        """Test subscription status command."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_subscription_details = AsyncMock(return_value=mock_subscription_response)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["-f", "json", "subscription", "status"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert "subscription" in output


# ============================================================================
# CLI Version and Help Tests
# ============================================================================


class TestCLIBasics:
    """Tests for CLI basics like version and help."""

    def test_version(self, runner):
        """Test version flag."""
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_help(self, runner):
        """Test help flag."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Monarch Money CLI" in result.output
        assert "auth" in result.output
        assert "accounts" in result.output
        assert "transactions" in result.output

    def test_auth_help(self, runner):
        """Test auth subcommand help."""
        result = runner.invoke(cli, ["auth", "--help"])

        assert result.exit_code == 0
        assert "login" in result.output
        assert "logout" in result.output
        assert "status" in result.output

    def test_accounts_help(self, runner):
        """Test accounts subcommand help."""
        result = runner.invoke(cli, ["accounts", "--help"])

        assert result.exit_code == 0
        assert "list" in result.output
        assert "create" in result.output
        assert "update" in result.output
        assert "delete" in result.output
