"""いいかんじ家計簿 サーバーへの最小 HTTP クライアント"""

from __future__ import annotations

from typing import Any

import httpx


class KakeiboReadClient:
    """read-only HTTP クライアント

    Bearer トークン (APIキー or OAuth) で /api/v1/* を叩く。
    """

    def __init__(self, base_url: str, token: str, *, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "KakeiboReadClient":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict:
        resp = self._client.get(path, params=params or {})
        if resp.status_code == 401:
            raise PermissionError("認証に失敗しました。トークンを確認してください。")
        if resp.status_code == 403:
            body = resp.json() if "json" in resp.headers.get("content-type", "") else {}
            msg = body.get("error") if isinstance(body, dict) else None
            raise PermissionError(msg or "このトークンには権限がありません。")
        resp.raise_for_status()
        return resp.json()

    # --- 仕訳 ---

    def list_journals(
        self,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict:
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        return self._get("/api/v1/journals", params)

    def get_journal(self, entry_id: int) -> dict:
        return self._get(f"/api/v1/journals/{entry_id}")

    # --- レポート ---

    def trial_balance(
        self,
        *,
        year: int | None = None,
        period_from: int = 0,
        period_to: int = 15,
    ) -> dict:
        params: dict[str, Any] = {"period_from": period_from, "period_to": period_to}
        if year:
            params["year"] = year
        return self._get("/api/v1/reports/trial-balance", params)

    def income_statement(
        self, *, year: int | None = None, month: int | None = None
    ) -> dict:
        params: dict[str, Any] = {}
        if year:
            params["year"] = year
        if month:
            params["month"] = month
        return self._get("/api/v1/reports/income-statement", params)

    def monthly_comparison(self, *, year: int | None = None) -> dict:
        params: dict[str, Any] = {}
        if year:
            params["year"] = year
        return self._get("/api/v1/reports/monthly", params)

    def tax_summary(self, *, year: int | None = None) -> dict:
        params: dict[str, Any] = {}
        if year:
            params["year"] = year
        return self._get("/api/v1/reports/tax", params)
