from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import ai_news_daily as dai
from ai_news_daily import (
    build_tweet,
    fetch_source,
    load_state,
    save_state,
    _extract_items,
    _parse_pubdate,
)


# ---------- load_state / save_state ----------

def test_load_state_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(dai, "STATE_FILE", tmp_path / "missing.json")
    posted, last = load_state()
    assert posted == set() and last == -1


def test_load_state_corrupt(tmp_path, monkeypatch):
    f = tmp_path / "state.json"
    f.write_text("{not valid")
    monkeypatch.setattr(dai, "STATE_FILE", f)
    posted, last = load_state()
    assert posted == set() and last == -1


def test_load_state_old_format(tmp_path, monkeypatch):
    f = tmp_path / "state.json"
    f.write_text('["http://a", "http://b"]')
    monkeypatch.setattr(dai, "STATE_FILE", f)
    posted, last = load_state()
    assert posted == {"http://a", "http://b"} and last == -1


def test_load_state_new_format(tmp_path, monkeypatch):
    f = tmp_path / "state.json"
    f.write_text('{"posted": ["http://a"], "last_source": 2}')
    monkeypatch.setattr(dai, "STATE_FILE", f)
    posted, last = load_state()
    assert posted == {"http://a"} and last == 2


def test_save_state(tmp_path, monkeypatch):
    f = tmp_path / "state.json"
    monkeypatch.setattr(dai, "STATE_FILE", f)
    save_state({"http://a", "http://b"}, 1)
    posted, last = load_state()
    assert posted == {"http://a", "http://b"} and last == 1


def test_save_state_truncates_history(tmp_path, monkeypatch):
    f = tmp_path / "state.json"
    monkeypatch.setattr(dai, "STATE_FILE", f)
    posted = {f"http://{i}" for i in range(300)}
    save_state(posted, 0)
    posted, _ = load_state()
    assert len(posted) == dai.MAX_POSTED_HISTORY


# ---------- _parse_pubdate ----------

def test_parse_pubdate_empty():
    assert _parse_pubdate("") is None


def test_parse_pubdate_valid():
    dt = _parse_pubdate("Wed, 02 Oct 2002 13:00:00 GMT")
    assert dt is not None and dt.year == 2002


def test_parse_pubdate_naive_is_utc():
    dt = _parse_pubdate("Wed, 02 Oct 2002 13:00:00")
    assert dt.tzinfo == timezone.utc


def test_parse_pubdate_invalid():
    assert _parse_pubdate("not-a-date") is None


# ---------- _extract_items ----------

RSS_XML = """<?xml version="1.0"?>
<rss version="2.0"><channel>
<item><title>News - Site</title><link>http://news</link><pubDate>Wed, 02 Oct 2002 13:00:00 GMT</pubDate></item>
</channel></rss>"""

ATOM_XML = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>Atom Title</title><link href="http://atom"/></entry>
</feed>"""


def test_extract_items_rss():
    items = _extract_items(RSS_XML)
    assert items == [("News - Site", "http://news", "Wed, 02 Oct 2002 13:00:00 GMT")]


def test_extract_items_rss_strips_source_suffix(monkeypatch):
    resp = MagicMock()
    resp.text = RSS_XML
    resp.raise_for_status = MagicMock()
    monkeypatch.setattr(dai.httpx, "get", lambda *a, **k: resp)
    items = fetch_source({"name": "Site", "url": "http://rss"})
    assert items[0]["title"] == "News"


def test_fetch_source_strips_suffix(monkeypatch):
    resp = MagicMock()
    resp.text = RSS_XML
    resp.raise_for_status = MagicMock()
    monkeypatch.setattr(dai.httpx, "get", lambda *a, **k: resp)
    items = fetch_source({"name": "Site", "url": "http://rss"})
    assert items[0]["title"] == "News"


def test_extract_items_atom():
    items = _extract_items(ATOM_XML)
    assert items == [("Atom Title", "http://atom", "")]


# ---------- build_tweet ----------

def test_build_tweet_normal():
    t = build_tweet("Headline here", "TechCrunch")
    assert "Headline here" in t and "TechCrunch" in t and "🤖" in t


def test_build_tweet_truncates_long():
    long_title = "x" * 400
    t = build_tweet(long_title, "Src")
    assert len(t) <= 270 and t.endswith("...")


# ---------- fetch_source ----------

def test_fetch_source(monkeypatch):
    src = {"name": "Test", "url": "http://rss"}
    resp = MagicMock()
    resp.text = RSS_XML
    resp.raise_for_status = MagicMock()
    monkeypatch.setattr(dai.httpx, "get", lambda *a, **k: resp)
    items = fetch_source(src)
    assert len(items) == 1
    assert items[0]["title"] == "News"
    assert items[0]["source"] == "Test"


def test_fetch_source_raises(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("network")
    monkeypatch.setattr(dai.httpx, "get", boom)
    with pytest.raises(RuntimeError):
        fetch_source({"name": "X", "url": "http://x"})


# ---------- post (async) ----------

def _run_post(body_text, is_error):
    import asyncio
    result = MagicMock()
    result.content = [MagicMock(text=body_text)]
    result.isError = is_error
    session = AsyncMock()
    session.call_tool.return_value = result
    with patch("ai_news_daily.stdio_client") as mock_stdio, \
         patch("ai_news_daily.ClientSession", return_value=session):
        mock_stdio.return_value.__aenter__.return_value = (MagicMock(), MagicMock())
        session.__aenter__.return_value = session
        return asyncio.run(dai.post("hello"))


def test_post_ok():
    status, msg = _run_post("tweet posted id 1", False)
    assert status == "ok"


def test_post_duplicate():
    status, _ = _run_post("duplicate key error", False)
    assert status == "duplicate"


def test_post_error():
    status, _ = _run_post("error: bad", True)
    assert status == "error"
