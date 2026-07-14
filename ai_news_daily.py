#!/usr/bin/env python3
import asyncio
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_CMD = ["python3", "-u", "/home/felipe/infra/twitter-mcp/server.py"]
STATE_FILE = Path("/home/felipe/infra/twitter-mcp/posted_news.json")
MAX_POSTED_HISTORY = 200

ATOM_NS = "{http://www.w3.org/2005/Atom}"

SOURCES = [
    {
        "name": "Google News (BR)",
        "url": "https://news.google.com/rss/search?q=intelig%C3%AAncia+artificial&hl=pt-BR&gl=BR&ceid=BR:pt-419",
    },
    {
        "name": "Google News (US)",
        "url": "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en",
    },
    {
        "name": "Google News (ML)",
        "url": "https://news.google.com/rss/search?q=machine+learning&hl=en-US&gl=US&ceid=US:en",
    },
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
    },
    {
        "name": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    },
    {
        "name": "MIT Tech Review AI",
        "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed",
    },
]


def load_state() -> tuple[set, int]:
    """Retorna (links_postados, indice_da_ultima_fonte_usada)."""
    if not STATE_FILE.exists():
        return set(), -1
    try:
        data = json.loads(STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return set(), -1
    if isinstance(data, list):  # formato antigo: só a lista de links
        return set(data), -1
    posted = set(data.get("posted", []))
    last_source = int(data.get("last_source", -1))
    return posted, last_source


def save_state(posted: set, last_source: int) -> None:
    payload = {
        "posted": sorted(posted)[-MAX_POSTED_HISTORY:],
        "last_source": last_source,
    }
    STATE_FILE.write_text(json.dumps(payload))


def _parse_pubdate(value: str):
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (TypeError, ValueError):
        return None


def _extract_items(xml_text: str):
    root = ET.fromstring(xml_text)
    items = []
    for item in root.findall(".//item"):
        title = item.findtext("title") or ""
        link = item.findtext("link") or ""
        pub = item.findtext("pubDate") or ""
        items.append((title, link, pub))
    if items:
        return items
    for entry in root.findall(f".//{ATOM_NS}entry"):
        title = entry.findtext(f"{ATOM_NS}title") or ""
        pub = entry.findtext(f"{ATOM_NS}updated") or entry.findtext(f"{ATOM_NS}published") or ""
        link = ""
        for link_el in entry.findall(f"{ATOM_NS}link"):
            rel = link_el.get("rel")
            if rel is None or rel == "alternate":
                link = link_el.get("href") or ""
                break
        items.append((title, link, pub))
    return items


def fetch_source(src: dict) -> list[dict]:
    resp = httpx.get(src["url"], timeout=20, follow_redirects=True)
    resp.raise_for_status()
    collected = []
    for title, link, pub in _extract_items(resp.text):
        title = re.sub(r"\s*-\s*[^-]+$", "", (title or "").strip())
        link = (link or "").strip()
        if title and link:
            collected.append({
                "title": title,
                "link": link,
                "source": src["name"],
                "published": _parse_pubdate(pub),
            })
    collected.sort(
        key=lambda x: x["published"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return collected


def build_tweet(title: str, source: str) -> str:
    today = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    base = f"🤖 IA | {title} (via {source}, {today})"
    if len(base) > 270:
        base = base[:267].rstrip() + "..."
    return base


async def post(text: str) -> tuple[str, str]:
    """Retorna (status, mensagem). status em {"ok", "duplicate", "error"}."""
    params = StdioServerParameters(command=SERVER_CMD[0], args=SERVER_CMD[1:])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("post_tweet", {"text": text})
            out = "".join(c.text for c in result.content)
            if "duplicate" in out.lower():
                return "duplicate", out
            if getattr(result, "isError", False) or "error" in out.lower():
                return "error", out
            return "ok", out


async def main() -> None:
    posted, last_source = load_state()
    n = len(SOURCES)
    order = [(last_source + 1 + i) % n for i in range(n)]

    for idx in order:
        src = SOURCES[idx]
        try:
            items = fetch_source(src)
        except Exception as e:
            print(f"AVISO: falha ao ler fonte '{src['name']}': {e}")
            continue
        if not items:
            continue
        for item in items:
            if item["link"] in posted:
                continue
            text = build_tweet(item["title"], item["source"])
            status, msg = await post(text)
            if status == "duplicate":
                print(f"DUPLICATE (ignorado): {item['title']}")
                posted.add(item["link"])
                save_state(posted, idx)
                continue
            if status == "error":
                print(f"ERRO ao postar '{item['title']}': {msg}")
                return
            posted.add(item["link"])
            save_state(posted, idx)
            print(msg)
            return

    print("Nenhuma notícia nova para postar (todas as fontes esgotadas ou duplicatas).")


if __name__ == "__main__":
    asyncio.run(main())
