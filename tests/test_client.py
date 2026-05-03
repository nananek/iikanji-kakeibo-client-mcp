"""KakeiboReadClient のテスト (httpx_mock 使用)"""

from __future__ import annotations

import pytest

from iikanji_mcp.client import KakeiboReadClient


BASE = "https://example.com"
TOKEN = "ikt_test"


def _make_client() -> KakeiboReadClient:
    return KakeiboReadClient(BASE, TOKEN)


class TestAuth:
    def test_includes_bearer_header(self, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/api/v1/journals?page=1&per_page=20",
            json={"ok": True, "journals": [], "total": 0, "page": 1, "per_page": 20},
        )
        with _make_client() as c:
            c.list_journals()
        request = httpx_mock.get_request()
        assert request.headers["Authorization"] == f"Bearer {TOKEN}"

    def test_401_raises_permission_error(self, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/api/v1/journals?page=1&per_page=20",
            status_code=401,
            json={"error": "無効なトークンです。"},
        )
        with _make_client() as c, pytest.raises(PermissionError, match="認証"):
            c.list_journals()

    def test_403_raises_with_server_error_message(self, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/api/v1/reports/trial-balance?period_from=0&period_to=15",
            status_code=403,
            json={"error": "この API キーには reports:read 権限がありません。"},
        )
        with _make_client() as c, pytest.raises(
            PermissionError, match="reports:read"
        ):
            c.trial_balance()


class TestListJournals:
    def test_passes_filters(self, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/api/v1/journals?page=2&per_page=50&date_from=2026-01-01&date_to=2026-03-31",
            json={"ok": True, "journals": [], "total": 0, "page": 2, "per_page": 50},
        )
        with _make_client() as c:
            data = c.list_journals(
                date_from="2026-01-01",
                date_to="2026-03-31",
                page=2, per_page=50,
            )
        assert data["page"] == 2

    def test_default_pagination(self, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/api/v1/journals?page=1&per_page=20",
            json={"ok": True, "journals": [{"id": 1}], "total": 1,
                  "page": 1, "per_page": 20},
        )
        with _make_client() as c:
            data = c.list_journals()
        assert len(data["journals"]) == 1


class TestGetJournal:
    def test_get(self, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/api/v1/journals/42",
            json={"ok": True, "journal": {"id": 42, "description": "test"}},
        )
        with _make_client() as c:
            data = c.get_journal(42)
        assert data["journal"]["id"] == 42


class TestReports:
    def test_trial_balance_with_year(self, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/api/v1/reports/trial-balance?period_from=0&period_to=15&year=2026",
            json={"ok": True, "year": 2026, "balances": []},
        )
        with _make_client() as c:
            data = c.trial_balance(year=2026)
        assert data["year"] == 2026

    def test_trial_balance_with_period_range(self, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/api/v1/reports/trial-balance?period_from=4&period_to=6",
            json={"ok": True, "year": 2026, "balances": []},
        )
        with _make_client() as c:
            data = c.trial_balance(period_from=4, period_to=6)
        assert data["ok"] is True

    def test_income_statement_full_year(self, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/api/v1/reports/income-statement",
            json={"ok": True, "year": 2026, "month": None,
                  "income_total": 0, "expense_total": 0, "net_income": 0,
                  "income_breakdown": [], "expense_breakdown": []},
        )
        with _make_client() as c:
            data = c.income_statement()
        assert data["month"] is None

    def test_income_statement_month(self, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/api/v1/reports/income-statement?year=2026&month=6",
            json={"ok": True, "year": 2026, "month": 6,
                  "income_total": 100000, "expense_total": 30000,
                  "net_income": 70000,
                  "income_breakdown": [], "expense_breakdown": []},
        )
        with _make_client() as c:
            data = c.income_statement(year=2026, month=6)
        assert data["net_income"] == 70000

    def test_monthly_comparison(self, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/api/v1/reports/monthly?year=2026",
            json={"ok": True, "year": 2026,
                  "expense_accounts": [], "income_accounts": [],
                  "expense_totals": [0] * 12, "income_totals": [0] * 12},
        )
        with _make_client() as c:
            data = c.monthly_comparison(year=2026)
        assert len(data["expense_totals"]) == 12

    def test_tax_summary(self, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/api/v1/reports/tax",
            json={"ok": True, "year": 2026,
                  "tax_summary": {}, "medical_summary": {}},
        )
        with _make_client() as c:
            data = c.tax_summary()
        assert "tax_summary" in data

    def test_tax_summary_with_year(self, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/api/v1/reports/tax?year=2025",
            json={"ok": True, "year": 2025,
                  "tax_summary": {}, "medical_summary": {}},
        )
        with _make_client() as c:
            data = c.tax_summary(year=2025)
        assert data["year"] == 2025

    def test_monthly_comparison_default(self, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/api/v1/reports/monthly",
            json={"ok": True, "year": 2026,
                  "expense_accounts": [], "income_accounts": [],
                  "expense_totals": [0] * 12, "income_totals": [0] * 12},
        )
        with _make_client() as c:
            data = c.monthly_comparison()
        assert data["ok"] is True

    def test_income_statement_year_only(self, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/api/v1/reports/income-statement?year=2025",
            json={"ok": True, "year": 2025, "month": None,
                  "income_total": 0, "expense_total": 0, "net_income": 0,
                  "income_breakdown": [], "expense_breakdown": []},
        )
        with _make_client() as c:
            data = c.income_statement(year=2025)
        assert data["year"] == 2025
