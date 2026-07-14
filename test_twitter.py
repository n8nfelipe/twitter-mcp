import json
from unittest.mock import MagicMock, patch

from auth import TwitterAuth, load_auth
from twitter_client import TwitterClient


def test_auth_loading():
    with patch("auth.load_dotenv"):
        auth = TwitterAuth(auth_token="test_token", ct0="test_ct0")
        assert auth.is_valid is True
        assert auth.auth_token == "test_token"
        assert auth.ct0 == "test_ct0"


def test_auth_invalid():
    auth = TwitterAuth()
    assert auth.is_valid is False


def test_auth_cookies():
    auth = TwitterAuth(auth_token="tok", ct0="ct")
    cookies = auth.cookies
    assert cookies["auth_token"] == "tok"
    assert cookies["ct0"] == "ct"


def test_auth_headers():
    auth = TwitterAuth(ct0="ct0_val")
    headers = auth.headers
    assert headers["X-Csrf-Token"] == "ct0_val"
    assert "Bearer" in headers["Authorization"]


def test_auth_cookies_with_user_id():
    auth = TwitterAuth(auth_token="tok", ct0="ct", user_id="999")
    assert auth.cookies["user_id"] == "999"


def test_auth_headers_without_ct0():
    auth = TwitterAuth(auth_token="tok")
    headers = auth.headers
    assert headers["X-Csrf-Token"] == ""
    assert "twitter.com" in headers["Origin"]


def test_load_auth(monkeypatch):
    monkeypatch.setenv("TWITTER_AUTH_TOKEN", "tok")
    monkeypatch.setenv("TWITTER_CT0", "ct")
    monkeypatch.setenv("TWITTER_USER_ID", "42")
    auth = load_auth()
    assert auth.is_valid is True
    assert auth.user_id == "42"
    assert auth.cookies["auth_token"] == "tok"


@patch("twitter_client.httpx.Client")
def test_post_tweet(MockClient):
    mock_instance = MagicMock()
    MockClient.return_value = mock_instance
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"create_tweet": {"tweet_results": {"result": {"rest_id": "123"}}}}}
    mock_instance.post.return_value = mock_response

    auth = TwitterAuth(auth_token="tok", ct0="ct")
    client = TwitterClient(auth)
    result = client.post_tweet("Hello World")
    data = json.loads(result)
    assert "create_tweet" in data["data"]


@patch("twitter_client.httpx.Client")
def test_search_tweets(MockClient):
    mock_instance = MagicMock()
    MockClient.return_value = mock_instance
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"search_by_raw_query": {"search_timeline": {"timeline": {"instructions": []}}}}}
    mock_instance.post.return_value = mock_response

    auth = TwitterAuth(auth_token="tok", ct0="ct")
    client = TwitterClient(auth)
    result = client.search_tweets("AI", count=5)
    data = json.loads(result)
    assert "search_by_raw_query" in data["data"]


@patch("twitter_client.httpx.Client")
def test_get_trends(MockClient):
    mock_instance = MagicMock()
    MockClient.return_value = mock_instance
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"trends": [{"name": "#AI"}], "locations": [{"woeid": 1}]}]
    mock_instance.get.return_value = mock_response

    auth = TwitterAuth(auth_token="tok", ct0="ct")
    client = TwitterClient(auth)
    result = client.get_trends()
    data = json.loads(result)
    assert "trends" in data
    assert data["trends"][0]["name"] == "#AI"


@patch("twitter_client.httpx.Client")
def test_delete_tweet(MockClient):
    mock_instance = MagicMock()
    MockClient.return_value = mock_instance
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"delete_tweet": {"result": {"tweet_results": {}}}}}
    mock_instance.post.return_value = mock_response

    auth = TwitterAuth(auth_token="tok", ct0="ct")
    client = TwitterClient(auth)
    result = client.delete_tweet("123")
    data = json.loads(result)
    assert "delete_tweet" in data["data"]


@patch("twitter_client.httpx.Client")
def test_like_tweet(MockClient):
    mock_instance = MagicMock()
    MockClient.return_value = mock_instance
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"favorite_tweet": "ok"}}
    mock_instance.post.return_value = mock_response

    auth = TwitterAuth(auth_token="tok", ct0="ct")
    client = TwitterClient(auth)
    result = client.like_tweet("123")
    data = json.loads(result)
    assert "favorite_tweet" in data["data"]


@patch("twitter_client.httpx.Client")
def test_retweet(MockClient):
    mock_instance = MagicMock()
    MockClient.return_value = mock_instance
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"create_retweet": "ok"}}
    mock_instance.post.return_value = mock_response

    auth = TwitterAuth(auth_token="tok", ct0="ct")
    client = TwitterClient(auth)
    result = client.retweet("123")
    data = json.loads(result)
    assert "create_retweet" in data["data"]


@patch("twitter_client.httpx.Client")
def test_get_user_by_screen_name(MockClient):
    mock_instance = MagicMock()
    MockClient.return_value = mock_instance
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"user": {"result": {"legacy": {"screen_name": "test"}}}}}
    mock_instance.post.return_value = mock_response

    auth = TwitterAuth(auth_token="tok", ct0="ct")
    client = TwitterClient(auth)
    result = client.get_user_by_screen_name("test")
    data = json.loads(result)
    assert data["data"]["user"]["result"]["legacy"]["screen_name"] == "test"


@patch("twitter_client.httpx.Client")
def test_get_authenticated_user(MockClient):
    mock_instance = MagicMock()
    MockClient.return_value = mock_instance
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"viewer": {"user_results": {"result": {"legacy": {"screen_name": "me"}}}}}}
    mock_instance.post.return_value = mock_response

    auth = TwitterAuth(auth_token="tok", ct0="ct")
    client = TwitterClient(auth)
    result = client.get_authenticated_user()
    data = json.loads(result)
    assert data["data"]["viewer"]["user_results"]["result"]["legacy"]["screen_name"] == "me"


@patch("twitter_client.httpx.Client")
def test_get_home_timeline(MockClient):
    mock_instance = MagicMock()
    MockClient.return_value = mock_instance
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"id": 1, "text": "hello"}]
    mock_instance.get.return_value = mock_response

    auth = TwitterAuth(auth_token="tok", ct0="ct")
    client = TwitterClient(auth)
    result = client.get_home_timeline()
    data = json.loads(result)
    assert isinstance(data, list)


@patch("twitter_client.httpx.Client")
def test_graphql_429(MockClient):
    mock_instance = MagicMock()
    MockClient.return_value = mock_instance
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_instance.post.return_value = mock_response

    auth = TwitterAuth(auth_token="tok", ct0="ct")
    client = TwitterClient(auth)
    import pytest
    with pytest.raises(Exception, match="Rate limited"):
        client.post_tweet("test")


@patch("twitter_client.httpx.Client")
def test_graphql_401(MockClient):
    mock_instance = MagicMock()
    MockClient.return_value = mock_instance
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_instance.post.return_value = mock_response

    auth = TwitterAuth(auth_token="tok", ct0="ct")
    client = TwitterClient(auth)
    import pytest
    with pytest.raises(Exception, match="Authentication failed"):
        client.post_tweet("test")


@patch("twitter_client.httpx.Client")
def test_graphql_errors(MockClient):
    mock_instance = MagicMock()
    MockClient.return_value = mock_instance
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"errors": [{"message": "Something went wrong"}]}
    mock_instance.post.return_value = mock_response

    auth = TwitterAuth(auth_token="tok", ct0="ct")
    client = TwitterClient(auth)
    import pytest
    with pytest.raises(Exception, match="Something went wrong"):
        client.post_tweet("test")


@patch("twitter_client.httpx.Client")
def test_graphql_403(MockClient):
    mock_instance = MagicMock()
    MockClient.return_value = mock_instance
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_instance.post.return_value = mock_response

    auth = TwitterAuth(auth_token="tok", ct0="ct")
    client = TwitterClient(auth)
    import pytest
    with pytest.raises(Exception, match="Forbidden"):
        client.post_tweet("test")


@patch("twitter_client.httpx.Client")
def test_graphql_unknown_operation(MockClient):
    mock_instance = MagicMock()
    MockClient.return_value = mock_instance

    auth = TwitterAuth(auth_token="tok", ct0="ct")
    client = TwitterClient(auth)
    import pytest
    with pytest.raises(Exception, match="Unknown operation"):
        client._graphql("DoesNotExist", {})


@patch("twitter_client.httpx.Client")
def test_graphql_non_json(MockClient):
    mock_instance = MagicMock()
    MockClient.return_value = mock_instance
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.text = "<html>maintenance</html>"
    mock_response.json.side_effect = json.JSONDecodeError("err", "", 0)
    mock_instance.post.return_value = mock_response

    auth = TwitterAuth(auth_token="tok", ct0="ct")
    client = TwitterClient(auth)
    import pytest
    with pytest.raises(Exception, match="Non-JSON response"):
        client._graphql("CreateTweet", {})


@patch("twitter_client.httpx.Client")
def test_get_user_timeline(MockClient):
    mock_instance = MagicMock()
    MockClient.return_value = mock_instance
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"id": 1, "text": "hi"}]
    mock_instance.get.return_value = mock_response

    auth = TwitterAuth(auth_token="tok", ct0="ct")
    client = TwitterClient(auth)
    result = client.get_user_timeline("123", count=5)
    data = json.loads(result)
    assert isinstance(data, list)
    _, kwargs = mock_instance.get.call_args
    assert kwargs["params"]["user_id"] == "123"


@patch("twitter_client.httpx.Client")
def test_get_tweet_detail(MockClient):
    mock_instance = MagicMock()
    MockClient.return_value = mock_instance
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"tweetResult": {"result": {"rest_id": "555"}}}}
    mock_instance.post.return_value = mock_response

    auth = TwitterAuth(auth_token="tok", ct0="ct")
    client = TwitterClient(auth)
    result = client.get_tweet_detail("555")
    data = json.loads(result)
    assert "tweetResult" in data["data"]


@patch("twitter_client.httpx.Client")
def test_follow_user(MockClient):
    mock_instance = MagicMock()
    MockClient.return_value = mock_instance
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"following": True, "id": "123"}
    mock_instance.post.return_value = mock_response

    auth = TwitterAuth(auth_token="tok", ct0="ct")
    client = TwitterClient(auth)
    result = client.follow_user("123")
    data = json.loads(result)
    assert data["following"] is True
    call = mock_instance.post.call_args
    assert "friendships/create.json" in call.args[0]


@patch("twitter_client.httpx.Client")
def test_get_non_200(MockClient):
    mock_instance = MagicMock()
    MockClient.return_value = mock_instance
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "boom"
    mock_instance.get.return_value = mock_response

    auth = TwitterAuth(auth_token="tok", ct0="ct")
    client = TwitterClient(auth)
    import pytest
    with pytest.raises(Exception, match="HTTP 500"):
        client.get_home_timeline()


@patch("twitter_client.httpx.Client")
def test_get_non_json(MockClient):
    mock_instance = MagicMock()
    MockClient.return_value = mock_instance
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "not json"
    mock_response.json.side_effect = json.JSONDecodeError("err", "", 0)
    mock_instance.get.return_value = mock_response

    auth = TwitterAuth(auth_token="tok", ct0="ct")
    client = TwitterClient(auth)
    import pytest
    with pytest.raises(Exception, match="Non-JSON response"):
        client.get_home_timeline()


@patch("twitter_client.httpx.Client")
def test_post_form_non_200(MockClient):
    mock_instance = MagicMock()
    MockClient.return_value = mock_instance
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "bad request"
    mock_instance.post.return_value = mock_response

    auth = TwitterAuth(auth_token="tok", ct0="ct")
    client = TwitterClient(auth)
    import pytest
    with pytest.raises(Exception, match="HTTP 400"):
        client.follow_user("123")


def test_close():
    auth = TwitterAuth(auth_token="tok", ct0="ct")
    client = TwitterClient(auth)
    with patch.object(client.client, "close") as mock_close:
        client.close()
        mock_close.assert_called_once()
