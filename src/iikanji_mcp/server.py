"""いいかんじ家計簿 MCP サーバー

環境変数:
- IIKANJI_API_URL: サーバー URL (例: https://kakeibo.example.com)
- IIKANJI_API_TOKEN: APIキー (ik_*) または OAuth トークン (ikt_*)
"""

from __future__ import annotations

import json
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import KakeiboReadClient


def _get_client() -> KakeiboReadClient:
    base_url = os.environ.get("IIKANJI_API_URL")
    token = os.environ.get("IIKANJI_API_TOKEN")
    if not base_url:
        raise RuntimeError("環境変数 IIKANJI_API_URL を設定してください。")
    if not token:
        raise RuntimeError("環境変数 IIKANJI_API_TOKEN を設定してください。")
    return KakeiboReadClient(base_url, token)


def _to_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def build_server() -> FastMCP:
    """MCP サーバーインスタンスを構築する"""
    mcp = FastMCP("iikanji-kakeibo")

    @mcp.tool()
    def list_journals(
        date_from: str | None = None,
        date_to: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> str:
        """仕訳一覧を取得する。

        Args:
            date_from: 取得開始日 (YYYY-MM-DD)
            date_to: 取得終了日 (YYYY-MM-DD)
            page: ページ番号 (1-)
            per_page: 1ページ件数 (最大100)
        """
        with _get_client() as c:
            data = c.list_journals(
                date_from=date_from, date_to=date_to,
                page=page, per_page=per_page,
            )
        return _to_json(data)

    @mcp.tool()
    def get_journal(entry_id: int) -> str:
        """指定 ID の仕訳詳細を取得する。"""
        with _get_client() as c:
            data = c.get_journal(entry_id)
        return _to_json(data)

    @mcp.tool()
    def get_trial_balance(
        year: int | None = None,
        period_from: int = 0,
        period_to: int = 15,
    ) -> str:
        """試算表を取得する。

        Args:
            year: 対象年度 (省略時は当年)
            period_from: 開始期間 (0=期首, 1-12=月, 13-15=決算整理, 16=損益振替)
            period_to: 終了期間
        """
        with _get_client() as c:
            data = c.trial_balance(
                year=year, period_from=period_from, period_to=period_to,
            )
        return _to_json(data)

    @mcp.tool()
    def get_income_statement(
        year: int | None = None,
        month: int | None = None,
    ) -> str:
        """損益計算書 (P/L) を科目別内訳付きで取得する。

        Args:
            year: 対象年度 (省略時は当年)
            month: 対象月 (1-12, 省略時は年間)
        """
        with _get_client() as c:
            data = c.income_statement(year=year, month=month)
        return _to_json(data)

    @mcp.tool()
    def get_monthly_comparison(year: int | None = None) -> str:
        """年間の月次収支比較データを取得する (収益・費用の科目別月次推移)。

        Args:
            year: 対象年度 (省略時は当年)
        """
        with _get_client() as c:
            data = c.monthly_comparison(year=year)
        return _to_json(data)

    @mcp.tool()
    def get_tax_summary(year: int | None = None) -> str:
        """確定申告用の年間集計 (社会保険料控除・医療費控除等) を取得する。

        Args:
            year: 対象年度 (省略時は当年)
        """
        with _get_client() as c:
            data = c.tax_summary(year=year)
        return _to_json(data)

    return mcp
