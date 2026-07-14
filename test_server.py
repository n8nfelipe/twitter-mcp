import importlib
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def server(monkeypatch):
    monkeypatch.setenv("TWITTER_AUTH_TOKEN", "tok")
    monkeypatch.setenv("TWITTER_CT0", "ct")
    with patch("twitter_client.TwitterClient", return_value=MagicMock()) as MockClient:
        import server as s
        importlib.reload(s)
        s.client = MockClient.return_value
        yield s


def test_server_post_tweet(server):
    server.client.post_tweet.return_value = "ok"
    assert server.post_tweet("hello") == "ok"
    server.client.post_tweet.assert_called_once_with("hello")


def test_server_delete_tweet(server):
    server.client.delete_tweet.return_value = "del"
    assert server.delete_tweet("123") == "del"


def test_server_like_tweet(server):
    server.client.like_tweet.return_value = "like"
    assert server.like_tweet("123") == "like"


def test_server_retweet(server):
    server.client.retweet.return_value = "rt"
    assert server.retweet("123") == "rt"


def test_server_search_tweets(server):
    server.client.search_tweets.return_value = "res"
    assert server.search_tweets("AI", 5) == "res"
    server.client.search_tweets.assert_called_once_with("AI", 5)


def test_server_get_home_timeline(server):
    server.client.get_home_timeline.return_value = "tl"
    assert server.get_home_timeline(10) == "tl"


def test_server_get_user_timeline(server):
    server.client.get_user_timeline.return_value = "ut"
    assert server.get_user_timeline("42", 10) == "ut"


def test_server_get_user_by_username(server):
    server.client.get_user_by_screen_name.return_value = "u"
    assert server.get_user_by_username("foo") == "u"


def test_server_get_tweet_detail(server):
    server.client.get_tweet_detail.return_value = "d"
    assert server.get_tweet_detail("555") == "d"


def test_server_get_trends(server):
    server.client.get_trends.return_value = "t"
    assert server.get_trends() == "t"


def test_server_get_authenticated_user(server):
    server.client.get_authenticated_user.return_value = "me"
    assert server.get_authenticated_user() == "me"


def test_server_follow_user(server):
    server.client.follow_user.return_value = "f"
    assert server.follow_user("42") == "f"


def test_server_invalid_auth(monkeypatch):
    monkeypatch.delenv("TWITTER_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("TWITTER_CT0", raising=False)
    with patch("sys.exit") as mock_exit, patch("twitter_client.TwitterClient", return_value=MagicMock()):
        import server as s
        importlib.reload(s)
        mock_exit.assert_called_once_with(1)
