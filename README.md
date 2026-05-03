# iikanji-kakeibo MCP サーバー

[いいかんじ家計簿](https://github.com/nananek/iikanji-kakeibo) を Claude Desktop / その他 MCP クライアントから財務分析できるようにする read-only ブリッジ。

## 提供するツール (read-only)

| ツール | 用途 |
|---|---|
| `list_journals` | 仕訳一覧 (日付範囲・ページネーション) |
| `get_journal` | 仕訳の詳細 |
| `get_trial_balance` | 試算表 |
| `get_income_statement` | 損益計算書 (P/L) |
| `get_monthly_comparison` | 月次収支比較 |
| `get_tax_summary` | 確定申告集計 (社会保険料・医療費控除等) |

## インストール

```bash
git clone https://github.com/nananek/iikanji-kakeibo-client-mcp
cd iikanji-kakeibo-client-mcp
pip install -e .
```

## OAuth トークンの取得

1. いいかんじ家計簿で `/oauth/device` にアクセスしクライアント名を登録、device_code と user_code を取得
2. ブラウザで user_code を入力 → **「読み取り専用で承認」** を選択
3. `/oauth/token` をポーリングしてアクセストークン (`ikt_*`) を取得

詳細は [いいかんじ家計簿のリリースノート v3.7.x](https://github.com/nananek/iikanji-kakeibo/blob/master/docs/releases.md) を参照。

## Claude Desktop 設定

`~/.config/Claude/claude_desktop_config.json` (macOS は `~/Library/Application Support/Claude/claude_desktop_config.json`) に追記:

```json
{
  "mcpServers": {
    "iikanji-kakeibo": {
      "command": "iikanji-mcp",
      "env": {
        "IIKANJI_API_URL": "https://kakeibo.example.com",
        "IIKANJI_API_TOKEN": "ikt_xxxxxxxx..."
      }
    }
  }
}
```

Claude Desktop を再起動すると `iikanji-kakeibo` が MCP サーバーとして利用可能に。

## 環境変数

| 変数 | 必須 | 用途 |
|---|---|---|
| `IIKANJI_API_URL` | ✓ | サーバー URL (例: `https://kakeibo.example.com`) |
| `IIKANJI_API_TOKEN` | ✓ | API キー (`ik_*`) または OAuth トークン (`ikt_*`) |

## 使用例

Claude にこんな質問が可能:
- 「2026年の経費トップ5を教えて」 → `get_income_statement` + 集計
- 「先月の収支は?」 → `get_income_statement(month=...)`
- 「医療費控除の対象金額は?」 → `get_tax_summary`
- 「現金科目の3月の動きを見せて」 → `list_journals(date_from, date_to)`

## ローカル開発

```bash
pip install -e ".[dev]"
pytest tests/
```

## ライセンス

IKL — 詳細は `LICENSE` を参照。
