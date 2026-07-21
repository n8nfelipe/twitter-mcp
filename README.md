# Twitter MCP Server

MCP (Model Context Protocol) server to interact with Twitter/X directly from any MCP-compatible AI assistant (like opencode). Uses your Twitter session cookies for authentication — no API keys needed.

## Features

- Post, delete, like, and retweet tweets
- Search tweets by keyword
- View home timeline, user timeline, and tweet details
- Get current trending topics
- Look up user profiles
- Follow/unfollow users
- Authenticated user profile info
- Daily AI news automation (`ai_news_daily.py`): fetches AI news from RSS feeds and posts via the MCP server on a cron schedule

## Quick Start

### 1. Get your Twitter cookies

1. Open Twitter/X in your browser (logged in)
2. Open DevTools (`F12`) → **Application** → **Cookies** → `https://x.com`
3. Copy the values for `auth_token` and `ct0`

### 2. Configure

**Option A (recommended): Store cookies in secret-vault-mcp**

If you have [`secret-vault-mcp`](https://github.com/n8nfelipe/secret-vault-mcp) installed and running:

1. Populate the vault with a `twitter-cookies` entry:
   ```
   add_secret name=twitter-cookies username=n8nfelipe \
     password=<auth_token> \
     notes='{"ct0": "<ct0>", "user_id": "<user_id>", "csrf_token": "<csrf_token>"}'
   ```
2. Ensure `VAULT_MASTER_PASSWORD` env var is set (or in `opencode.jsonc` env block).
3. Set `TWITTER_USE_VAULT=auto` (default) — the server will check the vault first,
   then fall back to `.env`.

**Option B: `.env` file**

```bash
cp .env.example .env
```

Edit `.env`:

```
TWITTER_AUTH_TOKEN=seu_auth_token_aqui
TWITTER_CT0=seu_ct0_aqui
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

**Note**: `requirements.txt` includes `secret-vault-mcp` as an editable dependency.
If you don't use the vault, you can remove the `-e ../secret-vault-mcp` line.

### 4. Run

```bash
python server.py
```

The server will start and listen on stdio, ready for MCP connections.

## Register with opencode

Add to `~/.config/opencode/opencode.jsonc`:

```jsonc
{
  "mcpServers": {
    "twitter": {
      "command": "python3",
      "args": ["/path/to/twitter-mcp/server.py"],
      "env": {
        "VAULT_MASTER_PASSWORD": "your-passphrase",
        "TWITTER_USE_VAULT": "auto"
      }
    }
  }
}
```

When `VAULT_MASTER_PASSWORD` is set, the server loads cookies from
`secret-vault-mcp` automatically (entry name `twitter-cookies` by default).
Override with `TWITTER_VAULT_ENTRY`.

## Register with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "twitter": {
      "command": "python3",
      "args": ["/caminho/para/twitter-mcp/server.py"],
      "env": {
        "TWITTER_AUTH_TOKEN": "seu_token",
        "TWITTER_CT0": "seu_ct0"
      }
    }
  }
}
```

## Register with Codex (by Cursor)

Create/edit `~/.codex/config.json`:

```json
{
  "mcpServers": {
    "twitter": {
      "command": "python3",
      "args": ["/caminho/para/twitter-mcp/server.py"],
      "env": {
        "TWITTER_AUTH_TOKEN": "seu_token",
        "TWITTER_CT0": "seu_ct0"
      }
    }
  }
}
```

## Tools

| Tool | Description | Arguments |
|---|---|---|
| `post_tweet` | Post a tweet | `text` (string, required) |
| `delete_tweet` | Delete a tweet | `tweet_id` (string, required) |
| `like_tweet` | Like a tweet | `tweet_id` (string, required) |
| `retweet` | Retweet a tweet | `tweet_id` (string, required) |
| `search_tweets` | Search tweets | `query` (string, required), `count` (int, default 20, max 50) |
| `get_home_timeline` | Your home timeline | `count` (int, default 20, max 50) |
| `get_user_timeline` | Tweets from a user | `user_id` (string, required), `count` (int, default 20) |
| `get_user_by_username` | User profile info | `username` (string, required, without @) |
| `get_tweet_detail` | Full tweet details | `tweet_id` (string, required) |
| `get_trends` | Current trending topics | — |
| `get_authenticated_user` | Your own profile | — |
| `follow_user` | Follow a user | `user_id` (string, required) |

## How it works

The server authenticates via `auth_token` and `ct0` session cookies, then makes requests directly to the Twitter/X internal GraphQL API. Query IDs are extracted from the official Twitter web client bundle, so no API keys or OAuth are needed.

## Tests

The suite uses `pytest` with the HTTP layer fully mocked (no real Twitter calls). It covers the auth module, the GraphQL/REST client (success and error paths), the MCP server tools, and the daily AI news script.

```bash
python3 -m pytest -v
```

Measure coverage across all source modules:

```bash
python3 -m coverage run --source=auth,twitter_client,server,ai_news_daily -m pytest
python3 -m coverage report
```

Current coverage target: **≥ 80%** (currently ~88%).

## CI

On every push to `main`, GitHub Actions runs all tests and automatically creates a tag (`v1.YYYYMMDD.HHMM`).

## Project structure

```
├── server.py           # MCP server entry point (12 tools via FastMCP)
├── twitter_client.py   # HTTP client for Twitter GraphQL API
├── auth.py             # Authentication via session cookies
├── ai_news_daily.py    # Cron script: posts daily AI news via the MCP server
├── test_twitter.py     # Tests for auth + twitter_client (mocked API)
├── test_server.py      # Tests for the MCP server tools
├── test_ai_news.py     # Tests for the daily AI news script
├── requirements.txt    # Python dependencies
├── .env.example        # Cookie config template
├── .github/workflows/  # CI pipeline
└── README.md
```
