#!/usr/bin/env python3
import sys
from mcp.server.fastmcp import FastMCP
from auth import load_auth
from twitter_client import TwitterClient


auth = load_auth()
if not auth.is_valid:
    print("Error: TWITTER_AUTH_TOKEN and TWITTER_CT0 must be set in .env file.", file=sys.stderr)
    print("Copy .env.example to .env and fill in your Twitter session cookies.", file=sys.stderr)
    sys.exit(1)

client = TwitterClient(auth)
mcp = FastMCP("twitter-mcp", instructions="Interact with Twitter/X: post tweets, search, view timelines, and more.")


@mcp.tool()
def post_tweet(text: str) -> str:
    """Post a new tweet to Twitter/X.

    Args:
        text: The text content of the tweet
    """
    result = client.post_tweet(text)
    return str(result)


@mcp.tool()
def delete_tweet(tweet_id: str) -> str:
    """Delete a tweet by its ID.

    Args:
        tweet_id: The ID of the tweet to delete
    """
    result = client.delete_tweet(tweet_id)
    return str(result)


@mcp.tool()
def like_tweet(tweet_id: str) -> str:
    """Like a tweet by its ID.

    Args:
        tweet_id: The ID of the tweet to like
    """
    result = client.like_tweet(tweet_id)
    return str(result)


@mcp.tool()
def retweet(tweet_id: str) -> str:
    """Retweet a tweet by its ID.

    Args:
        tweet_id: The ID of the tweet to retweet
    """
    result = client.retweet(tweet_id)
    return str(result)


@mcp.tool()
def search_tweets(query: str, count: int = 20) -> str:
    """Search for tweets by query.

    Args:
        query: Search query string
        count: Number of results (max 50, default 20)
    """
    result = client.search_tweets(query, min(count, 50))
    return str(result)


@mcp.tool()
def get_home_timeline(count: int = 20) -> str:
    """Get your home timeline tweets.

    Args:
        count: Number of tweets to return (max 50, default 20)
    """
    result = client.get_home_timeline(min(count, 50))
    return str(result)


@mcp.tool()
def get_user_timeline(user_id: str, count: int = 20) -> str:
    """Get tweets from a specific user by their user ID.

    Args:
        user_id: The user ID to get tweets from
        count: Number of tweets (default 20)
    """
    result = client.get_user_timeline(user_id, count)
    return str(result)


@mcp.tool()
def get_user_by_username(username: str) -> str:
    """Get user profile information by username (without @).

    Args:
        username: Username (without @ symbol)
    """
    result = client.get_user_by_screen_name(username)
    return str(result)


@mcp.tool()
def get_tweet_detail(tweet_id: str) -> str:
    """Get detailed information about a specific tweet including replies.

    Args:
        tweet_id: The tweet ID to look up
    """
    result = client.get_tweet_detail(tweet_id)
    return str(result)


@mcp.tool()
def get_trends() -> str:
    """Get current trending topics on Twitter."""
    result = client.get_trends()
    return str(result)


@mcp.tool()
def get_authenticated_user() -> str:
    """Get the authenticated user's profile information."""
    result = client.get_authenticated_user()
    return result


@mcp.tool()
def follow_user(user_id: str) -> str:
    """Follow a user by their user ID.

    Args:
        user_id: The user ID to follow
    """
    result = client.follow_user(user_id)
    return str(result)


if __name__ == "__main__":
    mcp.run()
