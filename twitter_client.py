from auth import TwitterAuth
import httpx
import json


API_BASE = "https://x.com/i/api/graphql"
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

QUERY_IDS = {
    "CreateTweet": "R5EPiGHgSqbTYFyozd-gFw",
    "DeleteTweet": "nxpZCY2K-I6QoFHAHeojFQ",
    "FavoriteTweet": "lI07N6Otwv1PhnEgXILM7A",
    "UnfavoriteTweet": "ZYKSe-w7KEslx3JhSIk5LA",
    "CreateRetweet": "mbRO74GrOvSfRcJnlMapnQ",
    "DeleteRetweet": "ZyZigVsNiFO6v1dEks1eWg",
    "SearchTimeline": "Bcw3RzK-PatNAmbnw54hFw",
    "TweetDetail": "jd3V43oDY9cY7obs1YMfbQ",
    "UserByScreenName": "2qvSHpkWTMS9i0zJAwDNiA",
    "UserByRestId": "DaeC_2LfMgwCujE03HSZtw",
    "Followers": "4yeuNabfz3qFlfncCAy8Yw",
    "Following": "eNoXdfXv5rU75RBzlmfuPA",
    "Likes": "tl9f_I0xyREhFd5KMzuO7w",
    "RemoveFollower": "QpNfg0kpPRfjROQ_9eOLXA",
    "ModerateTweet": "pjFnHGVqCjTcZol0xcBJjw",
    "Viewer": "u4ni7JqpqdAQxWQfkLsdUQ",
}

FEATURES = {
    "hidden_profile_likes_enabled": True,
    "hidden_profile_subscriptions_enabled": True,
    "responsive_web_graphql_exclude_directive_enabled": True,
    "verified_phone_label_enabled": False,
    "subscriptions_verification_info_is_identity_verified_enabled": True,
    "subscriptions_verification_info_verified_since_enabled": True,
    "highlights_tweets_tab_ui_enabled": True,
    "responsive_web_twitter_article_notes_tab_enabled": True,
    "creator_subscriptions_tweet_preview_api_enabled": True,
    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
    "responsive_web_graphql_timeline_navigation_enabled": True,
    "tweet_awards_web_tipping_enabled": False,
    "responsive_web_home_pinned_timelines_enabled": True,
    "communities_web_enable_tweet_community_results_fetch": True,
    "c9s_tweet_anatomy_moderator_badge_enabled": True,
    "articles_preview_enabled": True,
    "tweetypie_unmention_optimization_enabled": True,
    "responsive_web_edit_tweet_api_enabled": True,
    "graphql_is_translatable_rweb_is_translatable_enabled": True,
    "view_counts_everywhere_api_enabled": True,
    "longform_notetweets_consumption_enabled": True,
    "responsive_web_twitter_article_tweet_consumption_enabled": True,
    "tweet_awards_web_giving_enabled": False,
    "creator_subscriptions_quote_tweet_preview_enabled": False,
    "freedom_of_speech_not_reach_fetch_enabled": True,
    "standardized_nudges_misinfo": True,
    "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
    "rweb_video_timestamps_enabled": True,
    "longform_notetweets_rich_text_read_enabled": True,
    "longform_notetweets_inline_media_enabled": True,
    "responsive_web_enhance_cards_enabled": False,
}

FIELD_TOGGLES = {
    "withArticleRichContentState": True,
    "withArticlePlainText": False,
    "withGrokAnalyze": False,
    "withDisallowedReplyControls": False,
}


class TwitterClient:
    def __init__(self, auth: TwitterAuth):
        self.auth = auth
        self.client = httpx.Client(
            cookies=auth.cookies,
            headers={
                "authorization": f"Bearer {BEARER_TOKEN}",
                "x-csrf-token": auth.ct0,
                "content-type": "application/json",
                "x-twitter-auth-type": "OAuth2Session",
                "x-twitter-active-user": "yes",
                "x-twitter-client-language": "en",
                "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "origin": "https://x.com",
                "referer": "https://x.com/",
            },
            follow_redirects=True,
            timeout=30.0,
        )

    def _graphql(self, operation: str, variables: dict, query_id: str | None = None) -> dict:
        qid = query_id or QUERY_IDS.get(operation)
        if not qid:
            raise Exception(f"Unknown operation: {operation}")
        url = f"{API_BASE}/{qid}/{operation}"
        payload = {
            "variables": variables,
            "features": FEATURES,
            "queryId": qid,
        }
        resp = self.client.post(url, json=payload)
        if resp.status_code == 429:
            raise Exception("Rate limited by Twitter. Try again later.")
        if resp.status_code == 401:
            raise Exception("Authentication failed. Your session cookies may have expired.")
        if resp.status_code == 403:
            raise Exception("Forbidden. Your cookies may lack permissions.")
        try:
            data = resp.json()
        except json.JSONDecodeError:
            raise Exception(f"Non-JSON response ({resp.status_code}): {resp.text[:200]}")
        if "errors" in data:
            err_msg = data["errors"][0].get("message", str(data["errors"][0])) if data["errors"] else "Unknown"
            raise Exception(f"Twitter API error: {err_msg}")
        return data

    def _get(self, url: str, params: dict | None = None) -> dict:
        resp = self.client.get(url, params=params)
        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}: {resp.text[:200]}")
        try:
            return resp.json()
        except json.JSONDecodeError:
            raise Exception(f"Non-JSON response ({resp.status_code}): {resp.text[:200]}")

    def _post_form(self, url: str, data: dict) -> dict:
        headers = {"content-type": "application/x-www-form-urlencoded"}
        resp = self.client.post(url, data=data, headers=headers)
        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}: {resp.text[:200]}")
        try:
            return resp.json()
        except json.JSONDecodeError:
            raise Exception(f"Non-JSON response ({resp.status_code}): {resp.text[:200]}")

    def post_tweet(self, text: str, reply_to: str = None) -> str:
        variables = {
            "tweet_text": text,
            "dark_request": False,
            "media": {"media_entities": [], "possibly_sensitive": False},
            "semantic_annotation_ids": [],
        }
        if reply_to:
            variables["reply"] = {
                "in_reply_to_tweet_id": reply_to,
                "exclude_reply_user_ids": [],
            }
        result = self._graphql("CreateTweet", variables)
        return json.dumps(result, indent=2)

    def delete_tweet(self, tweet_id: str) -> str:
        result = self._graphql("DeleteTweet", {"tweet_id": tweet_id, "dark_request": False})
        return json.dumps(result, indent=2)

    def like_tweet(self, tweet_id: str) -> str:
        result = self._graphql("FavoriteTweet", {"tweet_id": tweet_id})
        return json.dumps(result, indent=2)

    def retweet(self, tweet_id: str) -> str:
        result = self._graphql("CreateRetweet", {"tweet_id": tweet_id, "dark_request": False})
        return json.dumps(result, indent=2)

    def search_tweets(self, query: str, count: int = 20) -> str:
        result = self._graphql("SearchTimeline", {
            "rawQuery": query,
            "count": min(count, 50),
            "product": "Latest",
        })
        return json.dumps(result, indent=2)

    def get_home_timeline(self, count: int = 20) -> str:
        # Use REST API v1.1 which works with cookies
        return json.dumps(self._get("https://api.twitter.com/1.1/statuses/home_timeline.json",
                                     params={"count": min(count, 50), "tweet_mode": "extended"}), indent=2)

    def get_user_timeline(self, user_id: str, count: int = 20) -> str:
        return json.dumps(self._get(f"https://api.twitter.com/1.1/statuses/user_timeline.json",
                                     params={"user_id": user_id, "count": min(count, 50), "tweet_mode": "extended"}), indent=2)

    def get_user_by_screen_name(self, username: str) -> str:
        result = self._graphql("UserByScreenName", {"screen_name": username})
        return json.dumps(result, indent=2)

    def get_tweet_detail(self, tweet_id: str) -> str:
        result = self._graphql("TweetDetail", {
            "focal_tweet_id": tweet_id,
            "cursor": None,
            "referrer": "tweet",
            "controller_data": None,
            "with_rux_injections": False,
            "ranking_mode": None,
            "include_hasBirdwatchNotes": False,
            "includePromotedContent": True,
        })
        return json.dumps(result, indent=2)

    def get_trends(self) -> str:
        trends = self._get("https://api.twitter.com/1.1/trends/place.json", params={"id": 1})
        if isinstance(trends, list) and len(trends) > 0:
            return json.dumps(trends[0], indent=2)
        return json.dumps(trends, indent=2)

    def get_authenticated_user(self) -> str:
        result = self._graphql("Viewer", {})
        return json.dumps(result, indent=2)

    def follow_user(self, user_id: str) -> str:
        return json.dumps(self._post_form("https://x.com/i/api/1.1/friendships/create.json",
                                          {"user_id": user_id}), indent=2)

    def close(self):
        self.client.close()
