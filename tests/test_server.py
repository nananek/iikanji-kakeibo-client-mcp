"""server.py の build_server / 環境変数チェックのテスト"""

from __future__ import annotations

import os

import pytest

from iikanji_mcp.server import _get_client, build_server


class TestGetClient:
    def test_missing_url_raises(self, monkeypatch):
        monkeypatch.delenv("IIKANJI_API_URL", raising=False)
        monkeypatch.setenv("IIKANJI_API_TOKEN", "ikt_x")
        with pytest.raises(RuntimeError, match="IIKANJI_API_URL"):
            _get_client()

    def test_missing_token_raises(self, monkeypatch):
        monkeypatch.setenv("IIKANJI_API_URL", "https://x")
        monkeypatch.delenv("IIKANJI_API_TOKEN", raising=False)
        with pytest.raises(RuntimeError, match="IIKANJI_API_TOKEN"):
            _get_client()

    def test_returns_client_when_env_set(self, monkeypatch):
        monkeypatch.setenv("IIKANJI_API_URL", "https://x")
        monkeypatch.setenv("IIKANJI_API_TOKEN", "ikt_x")
        c = _get_client()
        assert c.base_url == "https://x"
        c.close()

    def test_strips_trailing_slash(self, monkeypatch):
        monkeypatch.setenv("IIKANJI_API_URL", "https://x/")
        monkeypatch.setenv("IIKANJI_API_TOKEN", "ikt_x")
        c = _get_client()
        assert c.base_url == "https://x"
        c.close()


class TestBuildServer:
    def test_returns_fastmcp_instance(self):
        mcp = build_server()
        assert mcp.name == "iikanji-kakeibo"

    def test_registers_expected_tools(self):
        import asyncio
        mcp = build_server()
        # FastMCP の内部 API: list_tools() で登録ツールを取得
        tools = asyncio.run(mcp.list_tools())
        names = {t.name for t in tools}
        assert names == {
            "list_journals",
            "get_journal",
            "get_trial_balance",
            "get_income_statement",
            "get_monthly_comparison",
            "get_tax_summary",
        }


class TestToolsCallApi:
    """各ツールが期待通りに API を叩くか統合テスト"""

    def test_list_journals_tool(self, monkeypatch, httpx_mock):
        monkeypatch.setenv("IIKANJI_API_URL", "https://example.com")
        monkeypatch.setenv("IIKANJI_API_TOKEN", "ikt_test")
        httpx_mock.add_response(
            url="https://example.com/api/v1/journals?page=1&per_page=20",
            json={"ok": True, "journals": [], "total": 0,
                  "page": 1, "per_page": 20},
        )
        import asyncio
        mcp = build_server()
        result = asyncio.run(mcp.call_tool("list_journals", {}))
        # FastMCP は tuple (content_list, meta) を返すバージョンがあるため両対応
        text = _extract_text(result)
        assert '"ok": true' in text

    def test_get_trial_balance_tool(self, monkeypatch, httpx_mock):
        monkeypatch.setenv("IIKANJI_API_URL", "https://example.com")
        monkeypatch.setenv("IIKANJI_API_TOKEN", "ikt_test")
        httpx_mock.add_response(
            url="https://example.com/api/v1/reports/trial-balance?period_from=0&period_to=15&year=2026",
            json={"ok": True, "year": 2026, "balances": []},
        )
        import asyncio
        mcp = build_server()
        result = asyncio.run(mcp.call_tool("get_trial_balance", {"year": 2026}))
        text = _extract_text(result)
        assert '"year": 2026' in text

    def test_get_journal_tool(self, monkeypatch, httpx_mock):
        monkeypatch.setenv("IIKANJI_API_URL", "https://example.com")
        monkeypatch.setenv("IIKANJI_API_TOKEN", "ikt_test")
        httpx_mock.add_response(
            url="https://example.com/api/v1/journals/7",
            json={"ok": True, "journal": {"id": 7, "description": "test"}},
        )
        import asyncio
        mcp = build_server()
        result = asyncio.run(mcp.call_tool("get_journal", {"entry_id": 7}))
        text = _extract_text(result)
        assert '"id": 7' in text

    def test_get_income_statement_tool(self, monkeypatch, httpx_mock):
        monkeypatch.setenv("IIKANJI_API_URL", "https://example.com")
        monkeypatch.setenv("IIKANJI_API_TOKEN", "ikt_test")
        httpx_mock.add_response(
            url="https://example.com/api/v1/reports/income-statement?year=2026&month=6",
            json={"ok": True, "year": 2026, "month": 6,
                  "income_total": 0, "expense_total": 0, "net_income": 0,
                  "income_breakdown": [], "expense_breakdown": []},
        )
        import asyncio
        mcp = build_server()
        result = asyncio.run(
            mcp.call_tool("get_income_statement", {"year": 2026, "month": 6})
        )
        text = _extract_text(result)
        assert '"month": 6' in text

    def test_get_monthly_comparison_tool(self, monkeypatch, httpx_mock):
        monkeypatch.setenv("IIKANJI_API_URL", "https://example.com")
        monkeypatch.setenv("IIKANJI_API_TOKEN", "ikt_test")
        httpx_mock.add_response(
            url="https://example.com/api/v1/reports/monthly?year=2026",
            json={"ok": True, "year": 2026,
                  "expense_accounts": [], "income_accounts": [],
                  "expense_totals": [0] * 12, "income_totals": [0] * 12},
        )
        import asyncio
        mcp = build_server()
        result = asyncio.run(
            mcp.call_tool("get_monthly_comparison", {"year": 2026})
        )
        text = _extract_text(result)
        assert '"year": 2026' in text

    def test_get_tax_summary_tool(self, monkeypatch, httpx_mock):
        monkeypatch.setenv("IIKANJI_API_URL", "https://example.com")
        monkeypatch.setenv("IIKANJI_API_TOKEN", "ikt_test")
        httpx_mock.add_response(
            url="https://example.com/api/v1/reports/tax?year=2026",
            json={"ok": True, "year": 2026,
                  "tax_summary": {}, "medical_summary": {}},
        )
        import asyncio
        mcp = build_server()
        result = asyncio.run(mcp.call_tool("get_tax_summary", {"year": 2026}))
        text = _extract_text(result)
        assert '"tax_summary"' in text


class TestMain:
    """python -m iikanji_mcp エントリポイント"""

    def test_main_invokes_run(self, monkeypatch):
        from iikanji_mcp import __main__ as main_mod

        called = {"run": False}

        class FakeMCP:
            def run(self):
                called["run"] = True

        monkeypatch.setattr(main_mod, "build_server", lambda: FakeMCP())
        main_mod.main()
        assert called["run"] is True


def _extract_text(result) -> str:
    """FastMCP.call_tool の戻り値からテキストを抽出する (バージョン差異吸収)"""
    if isinstance(result, tuple):
        content_list = result[0]
    else:
        content_list = result
    parts = []
    for c in content_list:
        if hasattr(c, "text"):
            parts.append(c.text)
        elif isinstance(c, dict) and "text" in c:
            parts.append(c["text"])
    return "\n".join(parts)
