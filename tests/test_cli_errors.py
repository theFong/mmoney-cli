"""Tests for CLI error handling and edge cases."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from click.testing import CliRunner

from mmoney_cli.cli import cli, output_json, output_error, get_client, run_async, ExitCode, ErrorCode


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestAuthErrors:
    """Tests for authentication error handling."""

    def test_login_invalid_credentials(self, runner):
        """Test login with invalid credentials."""
        with patch("mmoney_cli.cli.MonarchMoney") as MockMM:
            mm_instance = MagicMock()
            mm_instance.login = AsyncMock(
                side_effect=Exception("Invalid email or password")
            )
            MockMM.return_value = mm_instance

            result = runner.invoke(
                cli,
                ["auth", "login", "--no-interactive", "-e", "bad@email.com", "-p", "wrongpass"],
            )

            assert result.exit_code == 2  # AUTH_ERROR
            error = json.loads(result.output)
            assert error["error"]["code"] == "AUTH_FAILED"
            assert "Login failed" in error["error"]["message"]
            assert "Invalid email or password" in error["error"]["details"]

    def test_login_mfa_wrong_code(self, runner):
        """Test login with wrong MFA code."""
        with patch("mmoney_cli.cli.MonarchMoney") as MockMM:
            mm_instance = MagicMock()
            mm_instance.multi_factor_authenticate = AsyncMock(
                side_effect=Exception("Invalid MFA code")
            )
            MockMM.return_value = mm_instance

            result = runner.invoke(
                cli,
                ["auth", "login", "--mfa-code", "000000", "-e", "test@example.com", "-p", "pass"],
            )

            assert result.exit_code == 2  # AUTH_ERROR
            error = json.loads(result.output)
            assert error["error"]["code"] == "AUTH_MFA_FAILED"
            assert "MFA login failed" in error["error"]["message"]

    def test_login_with_mfa_secret(self, runner):
        """Test login with MFA secret (TOTP)."""
        with patch("mmoney_cli.cli.MonarchMoney") as MockMM:
            mm_instance = MagicMock()
            mm_instance.login = AsyncMock()
            MockMM.return_value = mm_instance

            result = runner.invoke(
                cli,
                [
                    "auth", "login",
                    "--no-interactive",
                    "--mfa-secret", "JBSWY3DPEHPK3PXP",
                    "-e", "test@example.com",
                    "-p", "password123",
                ],
            )

            assert result.exit_code == 0
            mm_instance.login.assert_called_once_with(
                email="test@example.com",
                password="password123",
                mfa_secret_key="JBSWY3DPEHPK3PXP",
            )

    def test_login_network_error(self, runner):
        """Test login with network error."""
        with patch("mmoney_cli.cli.MonarchMoney") as MockMM:
            mm_instance = MagicMock()
            mm_instance.login = AsyncMock(
                side_effect=Exception("Connection refused")
            )
            MockMM.return_value = mm_instance

            result = runner.invoke(
                cli,
                ["auth", "login", "--no-interactive", "-e", "test@example.com", "-p", "pass"],
            )

            assert result.exit_code == 2  # AUTH_ERROR
            error = json.loads(result.output)
            assert error["error"]["code"] == "AUTH_FAILED"
            assert "Login failed" in error["error"]["message"]

    def test_auth_status_no_token(self, runner):
        """Test auth status when session exists but no token."""
        with patch("mmoney_cli.cli.MonarchMoney") as MockMM:
            mm_instance = MagicMock()
            mm_instance.token = None
            MockMM.return_value = mm_instance

            result = runner.invoke(cli, ["auth", "status"])

            assert result.exit_code == 0
            assert "Not authenticated" in result.output


class TestAPIErrors:
    """Tests for API error handling."""

    def test_accounts_list_api_error(self, runner):
        """Test accounts list when API returns error."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_accounts = AsyncMock(
                side_effect=Exception("API Error: Unauthorized")
            )
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["accounts", "list"])

            assert result.exit_code != 0

    def test_transactions_list_timeout(self, runner):
        """Test transactions list with timeout."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_transactions = AsyncMock(
                side_effect=TimeoutError("Request timed out")
            )
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["transactions", "list"])

            assert result.exit_code != 0

    def test_accounts_refresh_timeout(self, runner):
        """Test accounts refresh timeout."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.request_accounts_refresh_and_wait = AsyncMock(
                side_effect=TimeoutError("Refresh timed out")
            )
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["accounts", "refresh", "--timeout", "1"])

            assert result.exit_code != 0


# ============================================================================
# Input Validation Tests
# ============================================================================


class TestInputValidation:
    """Tests for input validation."""

    def test_transactions_create_missing_required(self, runner):
        """Test transactions create with missing required options."""
        result = runner.invoke(cli, ["transactions", "create"])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_accounts_create_missing_required(self, runner):
        """Test accounts create with missing required options."""
        result = runner.invoke(cli, ["accounts", "create", "--name", "Test"])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_categories_create_missing_required(self, runner):
        """Test categories create with missing required options."""
        result = runner.invoke(cli, ["categories", "create"])

        assert result.exit_code != 0

    def test_tags_create_missing_name(self, runner):
        """Test tags create without name."""
        result = runner.invoke(cli, ["tags", "create"])

        assert result.exit_code != 0

    def test_budgets_set_missing_amount(self, runner):
        """Test budgets set without amount."""
        result = runner.invoke(cli, ["budgets", "set"])

        assert result.exit_code != 0

    def test_holdings_list_missing_account_id(self, runner):
        """Test holdings list without account ID."""
        result = runner.invoke(cli, ["holdings", "list"])

        assert result.exit_code != 0

    def test_transactions_get_missing_id(self, runner):
        """Test transactions get without ID."""
        result = runner.invoke(cli, ["transactions", "get"])

        assert result.exit_code != 0

    def test_accounts_update_missing_id(self, runner):
        """Test accounts update without ID."""
        result = runner.invoke(cli, ["accounts", "update"])

        assert result.exit_code != 0

    def test_accounts_delete_missing_id(self, runner):
        """Test accounts delete without ID."""
        result = runner.invoke(cli, ["accounts", "delete"])

        assert result.exit_code != 0


# ============================================================================
# Edge Cases Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_accounts_list_empty(self, runner):
        """Test accounts list with no accounts."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_accounts = AsyncMock(return_value={"accounts": []})
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["accounts", "list"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert output["accounts"] == []

    def test_transactions_list_empty(self, runner):
        """Test transactions list with no transactions."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_transactions = AsyncMock(
                return_value={"allTransactions": {"totalCount": 0, "results": []}}
            )
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["transactions", "list"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert output["allTransactions"]["results"] == []

    def test_categories_list_empty(self, runner):
        """Test categories list with no categories."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_transaction_categories = AsyncMock(return_value={"categories": []})
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["categories", "list"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert output["categories"] == []

    def test_tags_list_empty(self, runner):
        """Test tags list with no tags."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_transaction_tags = AsyncMock(
                return_value={"householdTransactionTags": []}
            )
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["tags", "list"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert output["householdTransactionTags"] == []

    def test_transactions_list_with_pagination(self, runner):
        """Test transactions list with offset for pagination."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_transactions = AsyncMock(
                return_value={"allTransactions": {"totalCount": 100, "results": []}}
            )
            mock_get_client.return_value = mm_instance

            result = runner.invoke(
                cli,
                ["transactions", "list", "--limit", "10", "--offset", "50"],
            )

            assert result.exit_code == 0
            mm_instance.get_transactions.assert_called_once()
            call_kwargs = mm_instance.get_transactions.call_args[1]
            assert call_kwargs["limit"] == 10
            assert call_kwargs["offset"] == 50

    def test_accounts_refresh_with_specific_ids(self, runner):
        """Test accounts refresh with specific account IDs."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.request_accounts_refresh_and_wait = AsyncMock(return_value=True)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(
                cli,
                ["accounts", "refresh", "-a", "123", "-a", "456"],
            )

            assert result.exit_code == 0
            mm_instance.request_accounts_refresh_and_wait.assert_called_once()
            call_kwargs = mm_instance.request_accounts_refresh_and_wait.call_args[1]
            assert call_kwargs["account_ids"] == ["123", "456"]

    def test_accounts_refresh_no_wait(self, runner):
        """Test accounts refresh without waiting."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.request_accounts_refresh = AsyncMock(return_value=True)
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["accounts", "refresh", "--no-wait"])

            assert result.exit_code == 0
            mm_instance.request_accounts_refresh.assert_called_once()

    def test_accounts_create_all_options(self, runner):
        """Test accounts create with all options."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.create_manual_account = AsyncMock(
                return_value={"createManualAccount": {"id": "new_123"}}
            )
            mock_get_client.return_value = mm_instance

            result = runner.invoke(
                cli,
                [
                    "--allow-mutations",
                    "accounts", "create",
                    "--name", "Test Account",
                    "--type", "depository",
                    "--subtype", "savings",
                    "--balance", "5000.50",
                    "--not-in-net-worth",
                ],
            )

            assert result.exit_code == 0
            mm_instance.create_manual_account.assert_called_once()
            call_kwargs = mm_instance.create_manual_account.call_args[1]
            assert call_kwargs["account_name"] == "Test Account"
            assert call_kwargs["account_balance"] == 5000.50
            assert call_kwargs["is_in_net_worth"] is False

    def test_transactions_update_all_options(self, runner):
        """Test transactions update with all options."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.update_transaction = AsyncMock(
                return_value={"updateTransaction": {"id": "txn_001"}}
            )
            mock_get_client.return_value = mm_instance

            result = runner.invoke(
                cli,
                [
                    "--allow-mutations",
                    "transactions", "update", "txn_001",
                    "--category-id", "cat_001",
                    "--merchant", "New Merchant",
                    "--amount", "-75.50",
                    "--date", "2024-02-01",
                    "--notes", "Updated note",
                    "--hide-from-reports", "true",
                    "--needs-review", "false",
                ],
            )

            assert result.exit_code == 0
            mm_instance.update_transaction.assert_called_once()
            call_kwargs = mm_instance.update_transaction.call_args[1]
            assert call_kwargs["transaction_id"] == "txn_001"
            assert call_kwargs["merchant_name"] == "New Merchant"
            assert call_kwargs["amount"] == -75.50

    def test_transactions_list_all_filters(self, runner):
        """Test transactions list with all filter options."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_transactions = AsyncMock(
                return_value={"allTransactions": {"totalCount": 0, "results": []}}
            )
            mock_get_client.return_value = mm_instance

            result = runner.invoke(
                cli,
                [
                    "transactions", "list",
                    "--limit", "50",
                    "--offset", "10",
                    "--start-date", "2024-01-01",
                    "--end-date", "2024-12-31",
                    "--search", "coffee",
                    "--category-id", "cat_001",
                    "--category-id", "cat_002",
                    "--account-id", "acc_001",
                    "--tag-id", "tag_001",
                    "--has-attachments", "true",
                    "--has-notes", "true",
                    "--is-split", "false",
                    "--is-recurring", "false",
                ],
            )

            assert result.exit_code == 0
            mm_instance.get_transactions.assert_called_once()
            call_kwargs = mm_instance.get_transactions.call_args[1]
            assert call_kwargs["limit"] == 50
            assert call_kwargs["offset"] == 10
            assert call_kwargs["search"] == "coffee"
            assert call_kwargs["category_ids"] == ["cat_001", "cat_002"]
            assert call_kwargs["has_attachments"] is True
            assert call_kwargs["is_split"] is False

    def test_budgets_set_with_all_options(self, runner):
        """Test budgets set with all options."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.set_budget_amount = AsyncMock(return_value={"setBudget": True})
            mock_get_client.return_value = mm_instance

            result = runner.invoke(
                cli,
                [
                    "--allow-mutations",
                    "budgets", "set",
                    "--amount", "1000",
                    "--category-id", "cat_001",
                    "--timeframe", "month",
                    "--start-date", "2024-01-01",
                    "--apply-to-future",
                ],
            )

            assert result.exit_code == 0
            call_kwargs = mm_instance.set_budget_amount.call_args[1]
            assert call_kwargs["amount"] == 1000
            assert call_kwargs["apply_to_future"] is True

    def test_categories_create_with_all_options(self, runner):
        """Test categories create with all options."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.create_transaction_category = AsyncMock(
                return_value={"createCategory": {"id": "cat_new"}}
            )
            mock_get_client.return_value = mm_instance

            result = runner.invoke(
                cli,
                [
                    "--allow-mutations",
                    "categories", "create",
                    "--group-id", "grp_001",
                    "--name", "New Category",
                    "--icon", "🎉",
                    "--rollover",
                ],
            )

            assert result.exit_code == 0
            call_kwargs = mm_instance.create_transaction_category.call_args[1]
            assert call_kwargs["icon"] == "🎉"
            assert call_kwargs["rollover_enabled"] is True

    def test_accounts_delete_without_confirmation(self, runner):
        """Test accounts delete aborts without confirmation."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["--allow-mutations", "accounts", "delete", "123"], input="n\n")

            assert result.exit_code == 1
            mm_instance.delete_account.assert_not_called()

    def test_transactions_delete_without_confirmation(self, runner):
        """Test transactions delete aborts without confirmation."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["--allow-mutations", "transactions", "delete", "txn_001"], input="n\n")

            assert result.exit_code == 1
            mm_instance.delete_transaction.assert_not_called()

    def test_categories_delete_without_confirmation(self, runner):
        """Test categories delete aborts without confirmation."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["--allow-mutations", "categories", "delete", "cat_001"], input="n\n")

            assert result.exit_code == 1
            mm_instance.delete_transaction_category.assert_not_called()


# ============================================================================
# Utility Function Tests
# ============================================================================


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_output_json_pretty(self, runner, capsys):
        """Test output_json with pretty formatting."""
        data = {"key": "value", "number": 123}
        output_json(data, pretty=True)
        captured = capsys.readouterr()
        assert '"key": "value"' in captured.out
        assert "  " in captured.out  # indentation

    def test_output_json_compact(self, runner, capsys):
        """Test output_json without pretty formatting."""
        data = {"key": "value", "number": 123}
        output_json(data, pretty=False)
        captured = capsys.readouterr()
        assert captured.out.strip() == '{"key": "value", "number": 123}'

    def test_output_json_with_date(self, runner, capsys):
        """Test output_json handles date objects."""
        from datetime import date, datetime
        data = {"date": date(2024, 1, 15), "datetime": datetime(2024, 1, 15, 10, 30)}
        output_json(data, pretty=False)
        captured = capsys.readouterr()
        assert "2024-01-15" in captured.out

    def test_get_client_loads_session(self):
        """Test get_client loads session."""
        with patch("mmoney_cli.cli.MonarchMoney") as MockMM:
            mm_instance = MagicMock()
            MockMM.return_value = mm_instance

            client = get_client()

            mm_instance.load_session.assert_called_once()
            assert client == mm_instance

    def test_get_client_handles_missing_session(self):
        """Test get_client handles missing session gracefully."""
        with patch("mmoney_cli.cli.MonarchMoney") as MockMM:
            mm_instance = MagicMock()
            mm_instance.load_session.side_effect = Exception("No session file")
            MockMM.return_value = mm_instance

            client = get_client()

            # Should not raise, just return client without session
            assert client == mm_instance

    def test_run_async(self):
        """Test run_async executes coroutine."""
        async def sample_coro():
            return "result"

        result = run_async(sample_coro())
        assert result == "result"


# ============================================================================
# Special Response Handling Tests
# ============================================================================


class TestSpecialResponses:
    """Tests for handling special API responses."""

    def test_accounts_list_null_fields(self, runner):
        """Test accounts list handles null fields."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_accounts = AsyncMock(
                return_value={
                    "accounts": [
                        {
                            "id": "123",
                            "displayName": "Test",
                            "currentBalance": None,
                            "institution": None,
                        }
                    ]
                }
            )
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["accounts", "list"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert output["accounts"][0]["currentBalance"] is None

    def test_transactions_list_large_response(self, runner):
        """Test transactions list handles large response."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            large_results = [
                {"id": f"txn_{i}", "amount": -10.00} for i in range(1000)
            ]
            mm_instance.get_transactions = AsyncMock(
                return_value={"allTransactions": {"totalCount": 1000, "results": large_results}}
            )
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["transactions", "list", "--limit", "1000"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert len(output["allTransactions"]["results"]) == 1000

    def test_holdings_snapshots_date_parsing(self, runner):
        """Test holdings snapshots with date parsing."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_aggregate_snapshots = AsyncMock(
                return_value={"snapshots": []}
            )
            mock_get_client.return_value = mm_instance

            result = runner.invoke(
                cli,
                ["holdings", "snapshots", "-s", "2024-01-01", "-e", "2024-12-31"],
            )

            assert result.exit_code == 0
            call_kwargs = mm_instance.get_aggregate_snapshots.call_args[1]
            from datetime import date
            assert call_kwargs["start_date"] == date(2024, 1, 1)
            assert call_kwargs["end_date"] == date(2024, 12, 31)

    def test_holdings_snapshots_with_account_type(self, runner):
        """Test holdings snapshots with account type filter."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_aggregate_snapshots = AsyncMock(
                return_value={"snapshots": []}
            )
            mock_get_client.return_value = mm_instance

            result = runner.invoke(
                cli,
                ["holdings", "snapshots", "--account-type", "investment"],
            )

            assert result.exit_code == 0
            call_kwargs = mm_instance.get_aggregate_snapshots.call_args[1]
            assert call_kwargs["account_type"] == "investment"


# ============================================================================
# Read-Only Mode Tests
# ============================================================================


class TestReadOnlyMode:
    """Tests for read-only safe mode."""

    def test_accounts_create_blocked_without_flag(self, runner):
        """Test accounts create is blocked without --allow-mutations."""
        result = runner.invoke(
            cli,
            [
                "accounts", "create",
                "--name", "Test Account",
                "--type", "depository",
                "--subtype", "checking",
                "--balance", "1000",
            ],
        )

        assert result.exit_code == 6  # MUTATION_BLOCKED
        error = json.loads(result.output)
        assert error["error"]["code"] == "MUTATION_BLOCKED"
        assert "This command modifies data" in error["error"]["message"]
        assert "--allow-mutations" in error["error"]["details"]

    def test_accounts_update_blocked_without_flag(self, runner):
        """Test accounts update is blocked without --allow-mutations."""
        result = runner.invoke(cli, ["accounts", "update", "123", "--name", "New Name"])

        assert result.exit_code == 6  # MUTATION_BLOCKED
        error = json.loads(result.output)
        assert error["error"]["code"] == "MUTATION_BLOCKED"

    def test_accounts_delete_blocked_without_flag(self, runner):
        """Test accounts delete is blocked without --allow-mutations."""
        result = runner.invoke(cli, ["accounts", "delete", "123", "--yes"])

        assert result.exit_code == 6  # MUTATION_BLOCKED
        error = json.loads(result.output)
        assert error["error"]["code"] == "MUTATION_BLOCKED"

    def test_transactions_create_blocked_without_flag(self, runner):
        """Test transactions create is blocked without --allow-mutations."""
        result = runner.invoke(
            cli,
            [
                "transactions", "create",
                "--date", "2024-01-15",
                "--account-id", "123",
                "--amount", "-50.00",
                "--merchant", "Test",
                "--category-id", "cat_001",
            ],
        )

        assert result.exit_code == 6  # MUTATION_BLOCKED
        error = json.loads(result.output)
        assert error["error"]["code"] == "MUTATION_BLOCKED"

    def test_transactions_update_blocked_without_flag(self, runner):
        """Test transactions update is blocked without --allow-mutations."""
        result = runner.invoke(
            cli,
            ["transactions", "update", "txn_001", "--merchant", "New Merchant"],
        )

        assert result.exit_code == 6  # MUTATION_BLOCKED
        error = json.loads(result.output)
        assert error["error"]["code"] == "MUTATION_BLOCKED"

    def test_transactions_delete_blocked_without_flag(self, runner):
        """Test transactions delete is blocked without --allow-mutations."""
        result = runner.invoke(cli, ["transactions", "delete", "txn_001", "--yes"])

        assert result.exit_code == 6  # MUTATION_BLOCKED
        error = json.loads(result.output)
        assert error["error"]["code"] == "MUTATION_BLOCKED"

    def test_categories_create_blocked_without_flag(self, runner):
        """Test categories create is blocked without --allow-mutations."""
        result = runner.invoke(
            cli,
            ["categories", "create", "--group-id", "grp_001", "--name", "New Category"],
        )

        assert result.exit_code == 6  # MUTATION_BLOCKED
        error = json.loads(result.output)
        assert error["error"]["code"] == "MUTATION_BLOCKED"

    def test_categories_delete_blocked_without_flag(self, runner):
        """Test categories delete is blocked without --allow-mutations."""
        result = runner.invoke(cli, ["categories", "delete", "cat_001", "--yes"])

        assert result.exit_code == 6  # MUTATION_BLOCKED
        error = json.loads(result.output)
        assert error["error"]["code"] == "MUTATION_BLOCKED"

    def test_tags_create_blocked_without_flag(self, runner):
        """Test tags create is blocked without --allow-mutations."""
        result = runner.invoke(cli, ["tags", "create", "--name", "New Tag"])

        assert result.exit_code == 6  # MUTATION_BLOCKED
        error = json.loads(result.output)
        assert error["error"]["code"] == "MUTATION_BLOCKED"

    def test_tags_set_blocked_without_flag(self, runner):
        """Test tags set is blocked without --allow-mutations."""
        result = runner.invoke(
            cli,
            ["tags", "set", "txn_001", "--tag-id", "tag_001"],
        )

        assert result.exit_code == 6  # MUTATION_BLOCKED
        error = json.loads(result.output)
        assert error["error"]["code"] == "MUTATION_BLOCKED"

    def test_budgets_set_blocked_without_flag(self, runner):
        """Test budgets set is blocked without --allow-mutations."""
        result = runner.invoke(
            cli,
            ["budgets", "set", "--amount", "500", "--category-id", "cat_001"],
        )

        assert result.exit_code == 6  # MUTATION_BLOCKED
        error = json.loads(result.output)
        assert error["error"]["code"] == "MUTATION_BLOCKED"

    def test_read_commands_work_without_flag(self, runner):
        """Test that read-only commands work without --allow-mutations."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_accounts = AsyncMock(return_value={"accounts": []})
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["accounts", "list"])

            assert result.exit_code == 0


# ============================================================================
# Exit Codes and Error Codes Tests
# ============================================================================


class TestExitCodes:
    """Tests for exit code constants."""

    def test_exit_codes_defined(self):
        """Test that all exit codes are defined."""
        assert ExitCode.SUCCESS == 0
        assert ExitCode.GENERAL_ERROR == 1
        assert ExitCode.AUTH_ERROR == 2
        assert ExitCode.NOT_FOUND == 3
        assert ExitCode.VALIDATION_ERROR == 4
        assert ExitCode.API_ERROR == 5
        assert ExitCode.MUTATION_BLOCKED == 6

    def test_exit_codes_unique(self):
        """Test that exit codes are unique."""
        codes = [
            ExitCode.SUCCESS,
            ExitCode.GENERAL_ERROR,
            ExitCode.AUTH_ERROR,
            ExitCode.NOT_FOUND,
            ExitCode.VALIDATION_ERROR,
            ExitCode.API_ERROR,
            ExitCode.MUTATION_BLOCKED,
        ]
        assert len(codes) == len(set(codes))


class TestErrorCodes:
    """Tests for error code constants."""

    def test_auth_error_codes_defined(self):
        """Test that auth error codes are defined."""
        assert ErrorCode.AUTH_REQUIRED == "AUTH_REQUIRED"
        assert ErrorCode.AUTH_FAILED == "AUTH_FAILED"
        assert ErrorCode.AUTH_MFA_REQUIRED == "AUTH_MFA_REQUIRED"
        assert ErrorCode.AUTH_MFA_FAILED == "AUTH_MFA_FAILED"
        assert ErrorCode.AUTH_INVALID_TOKEN == "AUTH_INVALID_TOKEN"

    def test_validation_error_codes_defined(self):
        """Test that validation error codes are defined."""
        assert ErrorCode.VALIDATION_MISSING_FIELD == "VALIDATION_MISSING_FIELD"
        assert ErrorCode.VALIDATION_INVALID_VALUE == "VALIDATION_INVALID_VALUE"
        assert ErrorCode.VALIDATION_INVALID_DATE == "VALIDATION_INVALID_DATE"

    def test_api_error_codes_defined(self):
        """Test that API error codes are defined."""
        assert ErrorCode.API_ERROR == "API_ERROR"
        assert ErrorCode.API_TIMEOUT == "API_TIMEOUT"
        assert ErrorCode.API_RATE_LIMIT == "API_RATE_LIMIT"

    def test_resource_error_codes_defined(self):
        """Test that resource error codes are defined."""
        assert ErrorCode.NOT_FOUND == "NOT_FOUND"
        assert ErrorCode.ALREADY_EXISTS == "ALREADY_EXISTS"

    def test_permission_error_codes_defined(self):
        """Test that permission error codes are defined."""
        assert ErrorCode.MUTATION_BLOCKED == "MUTATION_BLOCKED"


class TestOutputError:
    """Tests for the output_error function."""

    def test_output_error_format(self, capsys):
        """Test that output_error produces correct JSON format."""
        with pytest.raises(SystemExit) as excinfo:
            output_error(
                code="TEST_ERROR",
                message="Test message",
                details="Test details",
                exit_code=42,
            )

        assert excinfo.value.code == 42
        captured = capsys.readouterr()
        error = json.loads(captured.err)
        assert error["error"]["code"] == "TEST_ERROR"
        assert error["error"]["message"] == "Test message"
        assert error["error"]["details"] == "Test details"

    def test_output_error_without_details(self, capsys):
        """Test output_error without details."""
        with pytest.raises(SystemExit):
            output_error(
                code="TEST_ERROR",
                message="Test message",
                exit_code=1,
            )

        captured = capsys.readouterr()
        error = json.loads(captured.err)
        assert "details" not in error["error"]
        assert error["error"]["code"] == "TEST_ERROR"
        assert error["error"]["message"] == "Test message"
