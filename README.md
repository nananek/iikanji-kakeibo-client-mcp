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

## トークンの取得

### 推奨: OAuth 読み取り専用トークン (Device Flow)

ブラウザで「読み取り専用で承認」して取得した OAuth トークン (`ikt_*`) なら、書き込み系エンドポイント (`POST /journals` 等) はサーバー側で 403 拒否されるため、MCP 経由で誤って書き込まれる構造的リスクなし。

#### A. curl で実行

```bash
SERVER=https://kakeibo.example.com

# 1. device_code / user_code を発行
curl -sX POST "$SERVER/oauth/device" \
  -H "Content-Type: application/json" \
  -d '{"client_name": "Claude MCP"}'
# → {"device_code":"...","user_code":"XXXX-YYYY",
#    "verification_uri_complete":"...","interval":5, ...}

# 2. verification_uri_complete をブラウザで開く
#    → ログインして [読み取り専用で承認] を押す

# 3. アクセストークンを取得 (interval 秒間隔で承認後にリトライ)
curl -sX POST "$SERVER/oauth/token" \
  -H "Content-Type: application/json" \
  -d '{
    "grant_type":"urn:ietf:params:oauth:grant-type:device_code",
    "device_code":"<step 1 の device_code>"
  }'
# → {"access_token":"ikt_...","token_type":"Bearer","expires_in":31536000}
```

承認直後は `{"error":"authorization_pending"}` が返るので、5秒待って再試行。

#### B. iikanji-tui で実行

[iikanji-tui](https://github.com/nananek/iikanji-kakeibo-client-tui) をインストール済みなら:

```bash
iikanji-tui login --api-url "$SERVER"
```

ブラウザが自動で開きます。承認画面で **「読み取り専用で承認」** を選択。発行されたトークンは TUI の設定ファイル (`~/.config/iikanji-tui/config.toml` 等) に保存されるので、その値を `IIKANJI_API_TOKEN` にコピーしてください。

### 代替: API キー (rw)

設定 → APIキー で発行。MCP には write 系ツールがないので実用上は read 操作のみですが、トークン自体は rw 権限を持つ点に注意。スコープに `reports:read` を含めること。

## Claude Desktop 設定

設定ファイルに追記:

| OS | パス |
|---|---|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |

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
