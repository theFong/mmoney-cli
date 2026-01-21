"""Pytest fixtures for mmoney-cli tests."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_mm():
    """Create a mock MonarchMoney client."""
    mm = MagicMock()
    mm.token = "test_token"
    mm._headers = {}
    return mm


@pytest.fixture
def mock_accounts_response():
    """Sample accounts response."""
    return {
        "accounts": [
            {
                "id": "123456",
                "displayName": "Checking (...1234)",
                "currentBalance": 1000.00,
                "type": {"name": "depository", "display": "Cash"},
                "subtype": {"name": "checking", "display": "Checking"},
                "institution": {"name": "Test Bank"},
            },
            {
                "id": "789012",
                "displayName": "Credit Card (...5678)",
                "currentBalance": -500.00,
                "type": {"name": "credit", "display": "Credit Cards"},
                "subtype": {"name": "credit_card", "display": "Credit Card"},
                "institution": {"name": "Test Bank"},
            },
        ]
    }


@pytest.fixture
def mock_transactions_response():
    """Sample transactions response."""
    return {
        "allTransactions": {
            "totalCount": 2,
            "results": [
                {
                    "id": "txn_001",
                    "date": "2024-01-15",
                    "amount": -50.00,
                    "merchant": {"name": "Coffee Shop"},
                    "category": {"name": "Food & Drink"},
                },
                {
                    "id": "txn_002",
                    "date": "2024-01-14",
                    "amount": -100.00,
                    "merchant": {"name": "Gas Station"},
                    "category": {"name": "Auto & Transport"},
                },
            ],
        }
    }


@pytest.fixture
def mock_categories_response():
    """Sample categories response."""
    return {
        "categories": [
            {"id": "cat_001", "name": "Food & Drink", "icon": "🍔"},
            {"id": "cat_002", "name": "Auto & Transport", "icon": "🚗"},
            {"id": "cat_003", "name": "Shopping", "icon": "🛒"},
        ]
    }


@pytest.fixture
def mock_tags_response():
    """Sample tags response."""
    return {
        "householdTransactionTags": [
            {"id": "tag_001", "name": "Business", "color": "blue"},
            {"id": "tag_002", "name": "Personal", "color": "green"},
        ]
    }


@pytest.fixture
def mock_budgets_response():
    """Sample budgets response."""
    return {
        "budgetData": {
            "totalBudget": 5000.00,
            "totalSpent": 3500.00,
            "budgetItems": [
                {"categoryId": "cat_001", "budgeted": 500.00, "spent": 400.00},
                {"categoryId": "cat_002", "budgeted": 300.00, "spent": 250.00},
            ],
        }
    }


@pytest.fixture
def mock_cashflow_response():
    """Sample cashflow response."""
    return {
        "summary": [
            {"month": "2024-01", "income": 5000.00, "expenses": 3500.00, "savings": 1500.00},
            {"month": "2023-12", "income": 5000.00, "expenses": 4000.00, "savings": 1000.00},
        ]
    }


@pytest.fixture
def mock_holdings_response():
    """Sample holdings response."""
    return {
        "portfolio": {
            "holdings": [
                {"id": "hold_001", "name": "AAPL", "quantity": 10, "value": 1500.00},
                {"id": "hold_002", "name": "GOOGL", "quantity": 5, "value": 7000.00},
            ]
        }
    }


@pytest.fixture
def mock_institutions_response():
    """Sample institutions response."""
    return {
        "credentials": [
            {
                "id": "cred_001",
                "institution": {"id": "inst_001", "name": "Test Bank", "status": "HEALTHY"},
            }
        ]
    }


@pytest.fixture
def mock_subscription_response():
    """Sample subscription response."""
    return {
        "subscription": {
            "plan": "premium",
            "status": "active",
            "expiresAt": "2025-01-01",
        }
    }


@pytest.fixture
def mock_recurring_response():
    """Sample recurring transactions response."""
    return {
        "recurringTransactions": [
            {"id": "rec_001", "name": "Netflix", "amount": -15.99, "frequency": "monthly"},
            {"id": "rec_002", "name": "Gym", "amount": -50.00, "frequency": "monthly"},
        ]
    }
