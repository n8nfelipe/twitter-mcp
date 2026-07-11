import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class TwitterAuth:
    auth_token: str = ""
    ct0: str = ""
    user_id: str = ""
    csrf_token: str = ""

    @property
    def is_valid(self) -> bool:
        return bool(self.auth_token) and bool(self.ct0)

    @property
    def cookies(self) -> dict[str, str]:
        cookies = {
            "auth_token": self.auth_token,
            "ct0": self.ct0,
        }
        if self.user_id:
            cookies["user_id"] = self.user_id
        return cookies

    @property
    def headers(self) -> dict[str, str]:
        headers = {
            "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
            "X-Csrf-Token": self.ct0,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Origin": "https://twitter.com",
            "Referer": "https://twitter.com/",
        }
        return headers


def load_auth() -> TwitterAuth:
    return TwitterAuth(
        auth_token=os.getenv("TWITTER_AUTH_TOKEN", ""),
        ct0=os.getenv("TWITTER_CT0", ""),
        user_id=os.getenv("TWITTER_USER_ID", ""),
        csrf_token=os.getenv("TWITTER_CSRF_TOKEN", ""),
    )
