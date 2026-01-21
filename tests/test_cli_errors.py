"""Tests for CLI error handling and edge cases."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from mmoney_cli.cli import (
    ErrorCode,
    ExitCode,
    OutputFormat,
    _extract_records,
    _flatten_dict,
    cli,
    get_client,
    output_csv,
    output_data,
    output_error,
    output_json,
    output_jsonl,
    output_text,
    run_async,
)


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
            mm_instance.login = AsyncMock(side_effect=Exception("Invalid email or password"))
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
                    "auth",
                    "login",
                    "--no-interactive",
                    "--mfa-secret",
                    "JBSWY3DPEHPK3PXP",
                    "-e",
                    "test@example.com",
                    "-p",
                    "password123",
                ],
            )

            assert result.exit_code == 0
            mm_instance.login.assert_called_once_with(
                email="test@example.com",
                password="password123",
                mfa_secret_key="JBSWY3DPEHPK3PXP",
                save_session=False,
            )

    def test_login_network_error(self, runner):
        """Test login with network error."""
        with patch("mmoney_cli.cli.MonarchMoney") as MockMM:
            mm_instance = MagicMock()
            mm_instance.login = AsyncMock(side_effect=Exception("Connection refused"))
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
            mm_instance.get_accounts = AsyncMock(side_effect=Exception("API Error: Unauthorized"))
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["accounts", "list"])

            assert result.exit_code != 0

    def test_transactions_list_timeout(self, runner):
        """Test transactions list with timeout."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_transactions = AsyncMock(side_effect=TimeoutError("Request timed out"))
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

            result = runner.invoke(cli, ["-f", "json", "accounts", "list"])

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

            result = runner.invoke(cli, ["-f", "json", "transactions", "list"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert output["allTransactions"]["results"] == []

    def test_categories_list_empty(self, runner):
        """Test categories list with no categories."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_transaction_categories = AsyncMock(return_value={"categories": []})
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["-f", "json", "categories", "list"])

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

            result = runner.invoke(cli, ["-f", "json", "tags", "list"])

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
                    "accounts",
                    "create",
                    "--name",
                    "Test Account",
                    "--type",
                    "depository",
                    "--subtype",
                    "savings",
                    "--balance",
                    "5000.50",
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
                    "transactions",
                    "update",
                    "txn_001",
                    "--category-id",
                    "cat_001",
                    "--merchant",
                    "New Merchant",
                    "--amount",
                    "-75.50",
                    "--date",
                    "2024-02-01",
                    "--notes",
                    "Updated note",
                    "--hide-from-reports",
                    "true",
                    "--needs-review",
                    "false",
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
                    "transactions",
                    "list",
                    "--limit",
                    "50",
                    "--offset",
                    "10",
                    "--start-date",
                    "2024-01-01",
                    "--end-date",
                    "2024-12-31",
                    "--search",
                    "coffee",
                    "--category-id",
                    "cat_001",
                    "--category-id",
                    "cat_002",
                    "--account-id",
                    "acc_001",
                    "--tag-id",
                    "tag_001",
                    "--has-attachments",
                    "true",
                    "--has-notes",
                    "true",
                    "--is-split",
                    "false",
                    "--is-recurring",
                    "false",
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
                    "budgets",
                    "set",
                    "--amount",
                    "1000",
                    "--category-id",
                    "cat_001",
                    "--timeframe",
                    "month",
                    "--start-date",
                    "2024-01-01",
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
                    "categories",
                    "create",
                    "--group-id",
                    "grp_001",
                    "--name",
                    "New Category",
                    "--icon",
                    "🎉",
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

            result = runner.invoke(
                cli, ["--allow-mutations", "accounts", "delete", "123"], input="n\n"
            )

            assert result.exit_code == 1
            mm_instance.delete_account.assert_not_called()

    def test_transactions_delete_without_confirmation(self, runner):
        """Test transactions delete aborts without confirmation."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mock_get_client.return_value = mm_instance

            result = runner.invoke(
                cli, ["--allow-mutations", "transactions", "delete", "txn_001"], input="n\n"
            )

            assert result.exit_code == 1
            mm_instance.delete_transaction.assert_not_called()

    def test_categories_delete_without_confirmation(self, runner):
        """Test categories delete aborts without confirmation."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mock_get_client.return_value = mm_instance

            result = runner.invoke(
                cli, ["--allow-mutations", "categories", "delete", "cat_001"], input="n\n"
            )

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
        """Test get_client loads session from file when keychain is empty."""
        with (
            patch("mmoney_cli.cli.MonarchMoney") as MockMM,
            patch("mmoney_cli.cli.load_token_from_keychain") as mock_keychain,
            patch("mmoney_cli.cli._SESSION_FILE") as mock_session_file,
        ):
            mm_instance = MagicMock()
            MockMM.return_value = mm_instance
            mock_keychain.return_value = None  # No keychain token
            mock_session_file.exists.return_value = True  # File exists

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

            result = runner.invoke(cli, ["-f", "json", "accounts", "list"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert output["accounts"][0]["currentBalance"] is None

    def test_transactions_list_large_response(self, runner):
        """Test transactions list handles large response."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            large_results = [{"id": f"txn_{i}", "amount": -10.00} for i in range(1000)]
            mm_instance.get_transactions = AsyncMock(
                return_value={"allTransactions": {"totalCount": 1000, "results": large_results}}
            )
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["-f", "json", "transactions", "list", "--limit", "1000"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert len(output["allTransactions"]["results"]) == 1000

    def test_holdings_snapshots_date_parsing(self, runner):
        """Test holdings snapshots with date parsing."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_aggregate_snapshots = AsyncMock(return_value={"snapshots": []})
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
            mm_instance.get_aggregate_snapshots = AsyncMock(return_value={"snapshots": []})
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
                "accounts",
                "create",
                "--name",
                "Test Account",
                "--type",
                "depository",
                "--subtype",
                "checking",
                "--balance",
                "1000",
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
                "transactions",
                "create",
                "--date",
                "2024-01-15",
                "--account-id",
                "123",
                "--amount",
                "-50.00",
                "--merchant",
                "Test",
                "--category-id",
                "cat_001",
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


# ============================================================================
# Output Format Tests
# ============================================================================


class TestOutputFormats:
    """Tests for output format functionality."""

    def test_output_format_constants(self):
        """Test that output format constants are defined."""
        assert OutputFormat.JSON == "json"
        assert OutputFormat.JSONL == "jsonl"
        assert OutputFormat.CSV == "csv"
        assert OutputFormat.TEXT == "text"

    def test_flatten_dict_simple(self):
        """Test flattening a simple dict."""
        data = {"a": 1, "b": "hello"}
        result = _flatten_dict(data)
        assert result == {"a": 1, "b": "hello"}

    def test_flatten_dict_nested(self):
        """Test flattening a nested dict."""
        data = {"outer": {"inner": "value", "num": 42}}
        result = _flatten_dict(data)
        assert result == {"outer.inner": "value", "outer.num": 42}

    def test_flatten_dict_with_list(self):
        """Test flattening a dict with list values."""
        data = {"items": [1, 2, 3], "name": "test"}
        result = _flatten_dict(data)
        assert result["name"] == "test"
        assert result["items"] == "[1, 2, 3]"

    def test_extract_records_from_list(self):
        """Test extracting records from a list."""
        data = [{"id": 1}, {"id": 2}]
        result = _extract_records(data)
        assert result == data

    def test_extract_records_from_dict_with_accounts(self):
        """Test extracting records from accounts response."""
        data = {"accounts": [{"id": "acc1"}, {"id": "acc2"}]}
        result = _extract_records(data)
        assert result == [{"id": "acc1"}, {"id": "acc2"}]

    def test_extract_records_from_nested_results(self):
        """Test extracting records from nested allTransactions.results."""
        data = {"allTransactions": {"totalCount": 2, "results": [{"id": "tx1"}, {"id": "tx2"}]}}
        result = _extract_records(data)
        assert result == [{"id": "tx1"}, {"id": "tx2"}]

    def test_extract_records_single_dict(self):
        """Test extracting records from a single dict."""
        data = {"id": "single", "name": "test"}
        result = _extract_records(data)
        assert result == [{"id": "single", "name": "test"}]

    def test_output_jsonl(self, capsys):
        """Test JSONL output format."""
        data = {"accounts": [{"id": "1", "name": "Checking"}, {"id": "2", "name": "Savings"}]}
        output_jsonl(data)
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0]) == {"id": "1", "name": "Checking"}
        assert json.loads(lines[1]) == {"id": "2", "name": "Savings"}

    def test_output_csv(self, capsys):
        """Test CSV output format."""
        data = {"accounts": [{"id": "1", "name": "Checking"}, {"id": "2", "name": "Savings"}]}
        output_csv(data)
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert "id" in lines[0]
        assert "name" in lines[0]
        assert "1" in lines[1] or "2" in lines[1]

    def test_output_csv_empty(self, capsys):
        """Test CSV output with empty data."""
        data = {"accounts": []}
        output_csv(data)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_output_text(self, capsys):
        """Test text output format."""
        data = {"accounts": [{"id": "1", "name": "Checking"}]}
        output_text(data)
        captured = capsys.readouterr()
        assert "id=1" in captured.out
        assert "name=Checking" in captured.out

    def test_output_text_multiple_records(self, capsys):
        """Test text output with multiple records."""
        data = {"accounts": [{"id": "1"}, {"id": "2"}]}
        output_text(data)
        captured = capsys.readouterr()
        assert "---" in captured.out  # Record separator
        assert captured.out.count("id=") == 2

    def test_output_data_json(self, capsys):
        """Test output_data with JSON format."""
        data = {"key": "value"}
        output_data(data, OutputFormat.JSON)
        captured = capsys.readouterr()
        assert json.loads(captured.out) == {"key": "value"}

    def test_output_data_jsonl(self, capsys):
        """Test output_data with JSONL format."""
        data = {"accounts": [{"a": 1}, {"a": 2}]}
        output_data(data, OutputFormat.JSONL)
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert len(lines) == 2

    def test_output_data_csv(self, capsys):
        """Test output_data with CSV format."""
        data = {"accounts": [{"col1": "val1", "col2": "val2"}]}
        output_data(data, OutputFormat.CSV)
        captured = capsys.readouterr()
        assert "col1" in captured.out
        assert "val1" in captured.out

    def test_output_data_text(self, capsys):
        """Test output_data with text format."""
        data = {"accounts": [{"key": "value"}]}
        output_data(data, OutputFormat.TEXT)
        captured = capsys.readouterr()
        assert "key=value" in captured.out


class TestOutputFormatCLIOption:
    """Tests for --format CLI option."""

    def test_format_option_json(self, runner):
        """Test --format json option."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_accounts = AsyncMock(
                return_value={"accounts": [{"id": "1", "name": "Test"}]}
            )
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["--format", "json", "accounts", "list"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert "accounts" in output

    def test_format_option_jsonl(self, runner):
        """Test --format jsonl option."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_accounts = AsyncMock(
                return_value={"accounts": [{"id": "1"}, {"id": "2"}]}
            )
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["--format", "jsonl", "accounts", "list"])

            assert result.exit_code == 0
            lines = result.output.strip().split("\n")
            assert len(lines) == 2
            assert json.loads(lines[0])["id"] == "1"
            assert json.loads(lines[1])["id"] == "2"

    def test_format_option_csv(self, runner):
        """Test --format csv option."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_accounts = AsyncMock(
                return_value={"accounts": [{"id": "1", "name": "Checking"}]}
            )
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["--format", "csv", "accounts", "list"])

            assert result.exit_code == 0
            assert "id" in result.output
            assert "name" in result.output
            assert "Checking" in result.output

    def test_format_option_text(self, runner):
        """Test --format text option."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_accounts = AsyncMock(
                return_value={"accounts": [{"id": "1", "name": "Test"}]}
            )
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["--format", "text", "accounts", "list"])

            assert result.exit_code == 0
            assert "id=1" in result.output
            assert "name=Test" in result.output

    def test_format_option_short_flag(self, runner):
        """Test -f short flag for format."""
        with patch("mmoney_cli.cli.get_client") as mock_get_client:
            mm_instance = MagicMock()
            mm_instance.get_accounts = AsyncMock(return_value={"accounts": [{"id": "1"}]})
            mock_get_client.return_value = mm_instance

            result = runner.invoke(cli, ["-f", "jsonl", "accounts", "list"])

            assert result.exit_code == 0
            assert json.loads(result.output.strip())["id"] == "1"

    def test_format_option_invalid(self, runner):
        """Test invalid format option."""
        result = runner.invoke(cli, ["--format", "invalid", "accounts", "list"])

        assert result.exit_code != 0
        assert "Invalid value" in result.output or "invalid" in result.output.lower()


# ============================================================================
# Keychain Storage Tests
# ============================================================================


class TestKeychainStorage:
    """Tests for keychain storage functionality."""

    def test_save_token_to_keychain_success(self):
        """Test saving token to keychain."""
        from mmoney_cli.cli import save_token_to_keychain

        with patch("mmoney_cli.cli.keyring") as mock_keyring:
            result = save_token_to_keychain("test_token")

            assert result is True
            mock_keyring.set_password.assert_called_once_with(
                "mmoney-cli", "monarch-token", "test_token"
            )

    def test_save_token_to_keychain_failure(self):
        """Test saving token to keychain when keyring fails."""
        from mmoney_cli.cli import save_token_to_keychain

        with patch("mmoney_cli.cli.keyring") as mock_keyring:
            mock_keyring.set_password.side_effect = Exception("Keychain error")
            result = save_token_to_keychain("test_token")

            assert result is False

    def test_load_token_from_keychain_success(self):
        """Test loading token from keychain."""
        from mmoney_cli.cli import load_token_from_keychain

        with patch("mmoney_cli.cli.keyring") as mock_keyring:
            mock_keyring.get_password.return_value = "saved_token"
            result = load_token_from_keychain()

            assert result == "saved_token"
            mock_keyring.get_password.assert_called_once_with("mmoney-cli", "monarch-token")

    def test_load_token_from_keychain_not_found(self):
        """Test loading token when not in keychain."""
        from mmoney_cli.cli import load_token_from_keychain

        with patch("mmoney_cli.cli.keyring") as mock_keyring:
            mock_keyring.get_password.return_value = None
            result = load_token_from_keychain()

            assert result is None

    def test_load_token_from_keychain_failure(self):
        """Test loading token when keyring fails."""
        from mmoney_cli.cli import load_token_from_keychain

        with patch("mmoney_cli.cli.keyring") as mock_keyring:
            mock_keyring.get_password.side_effect = Exception("Keychain error")
            result = load_token_from_keychain()

            assert result is None

    def test_delete_token_from_keychain_success(self):
        """Test deleting token from keychain."""
        from mmoney_cli.cli import delete_token_from_keychain

        with patch("mmoney_cli.cli.keyring") as mock_keyring:
            result = delete_token_from_keychain()

            assert result is True
            mock_keyring.delete_password.assert_called_once_with("mmoney-cli", "monarch-token")

    def test_delete_token_from_keychain_failure(self):
        """Test deleting token when keyring fails."""
        from mmoney_cli.cli import delete_token_from_keychain

        with patch("mmoney_cli.cli.keyring") as mock_keyring:
            mock_keyring.delete_password.side_effect = Exception("Keychain error")
            result = delete_token_from_keychain()

            assert result is False

    def test_get_client_uses_keychain_first(self):
        """Test get_client tries keychain before file and sets Authorization header."""
        with (
            patch("mmoney_cli.cli.load_token_from_keychain") as mock_load,
            patch("mmoney_cli.cli.MonarchMoney") as MockMM,
        ):
            mock_load.return_value = "keychain_token"
            mm_instance = MagicMock()
            mm_instance._headers = {}
            MockMM.return_value = mm_instance

            from mmoney_cli.cli import get_client

            get_client()

            mock_load.assert_called_once()
            mm_instance.set_token.assert_called_once_with("keychain_token")
            mm_instance.load_session.assert_not_called()
            # Verify Authorization header is set (regression test for 401 bug)
            assert mm_instance._headers["Authorization"] == "Token keychain_token"

    def test_get_client_falls_back_to_file(self):
        """Test get_client falls back to file when keychain empty."""
        with (
            patch("mmoney_cli.cli.load_token_from_keychain") as mock_load,
            patch("mmoney_cli.cli.MonarchMoney") as MockMM,
            patch("mmoney_cli.cli._SESSION_FILE") as mock_session_file,
        ):
            mock_load.return_value = None
            mock_session_file.exists.return_value = True  # File exists
            mm_instance = MagicMock()
            MockMM.return_value = mm_instance

            from mmoney_cli.cli import get_client

            get_client()  # Call to trigger mocks

            mock_load.assert_called_once()
            mm_instance.set_token.assert_not_called()
            mm_instance.load_session.assert_called_once()

    def test_auth_login_token_saves_to_keychain(self, runner):
        """Test auth login with token saves to keychain."""
        with (
            patch("mmoney_cli.cli.MonarchMoney") as MockMM,
            patch("mmoney_cli.cli.save_token_to_keychain") as mock_save,
        ):
            mm_instance = MagicMock()
            MockMM.return_value = mm_instance
            mock_save.return_value = True

            result = runner.invoke(cli, ["auth", "login", "--token", "my_token"])

            assert result.exit_code == 0
            mock_save.assert_called_once_with("my_token")
            assert "keychain" in result.output.lower()

    def test_auth_login_token_fallback_to_file(self, runner):
        """Test auth login falls back to file when keychain fails."""
        with (
            patch("mmoney_cli.cli.MonarchMoney") as MockMM,
            patch("mmoney_cli.cli.save_token_to_keychain") as mock_save,
        ):
            mm_instance = MagicMock()
            MockMM.return_value = mm_instance
            mock_save.return_value = False  # Keychain fails

            result = runner.invoke(cli, ["auth", "login", "--token", "my_token"])

            assert result.exit_code == 0
            mm_instance.save_session.assert_called_once()
            assert "file" in result.output.lower()

    def test_auth_logout_clears_keychain(self, runner):
        """Test auth logout clears keychain."""
        with (
            patch("mmoney_cli.cli.delete_token_from_keychain") as mock_delete,
            patch("mmoney_cli.cli._SESSION_FILE") as mock_session_file,
        ):
            mock_delete.return_value = True
            mock_session_file.exists.return_value = False  # No file to delete

            result = runner.invoke(cli, ["auth", "logout"])

            assert result.exit_code == 0
            mock_delete.assert_called_once()
            assert "Session deleted" in result.output
