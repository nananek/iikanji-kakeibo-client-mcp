"""エントリポイント — MCP stdio サーバーとして起動する"""

from .server import build_server


def main() -> None:
    mcp = build_server()
    mcp.run()


if __name__ == "__main__":
    main()
