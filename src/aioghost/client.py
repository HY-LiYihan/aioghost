"""Ghost Admin API client."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import aiohttp
import jwt

from .exceptions import (
    GhostAuthError,
    GhostConnectionError,
    GhostError,
    GhostNotFoundError,
    GhostValidationError,
)

_LOGGER = logging.getLogger(__name__)


def _convert_to_mobiledoc(content: str) -> str:
    """Convert plain text/HTML to Ghost mobiledoc format.

    Args:
        content: The content to convert.

    Returns:
        JSON string of mobiledoc format.
    """
    # Ghost mobiledoc basic structure for plain text/HTML
    mobiledoc = {
        "version": "0.3.1",
        "markups": [],
        "atoms": [],
        "cards": [],
        "sections": [
            [10, 0]  # Markdown card with content
        ]
    }
    # Using HTML card for simplicity
    mobiledoc["cards"] = [["html", content]]
    mobiledoc["sections"] = [[10, 0]]
    return json.dumps(mobiledoc)

JWT_EXPIRY_MINUTES = 5


class GhostAdminAPI:
    """Async client for the Ghost Admin API."""

    def __init__(
        self,
        api_url: str,
        admin_api_key: str,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize the API client.

        Args:
            api_url: The Ghost API URL (e.g., https://example.ghost.io)
            admin_api_key: The Admin API key (format: id:secret)
            session: Optional aiohttp session. If not provided, one will be created.

        Raises:
            ValueError: If api_url does not use HTTPS.
        """
        if not api_url.startswith("https://"):
            raise ValueError("api_url must use HTTPS")
        self.api_url = api_url.rstrip("/")
        self.admin_api_key = admin_api_key
        self._session = session
        self._owns_session = session is None

    def _generate_token(self) -> str:
        """Generate a JWT token for Ghost Admin API authentication."""
        try:
            key_id, secret = self.admin_api_key.split(":")
        except ValueError as err:
            raise GhostAuthError("Invalid API key format. Expected 'id:secret'") from err

        try:
            secret_bytes = bytes.fromhex(secret)
        except ValueError as err:
            raise GhostAuthError("Invalid API key secret. Expected hex string.") from err

        now = datetime.now(UTC)
        payload = {
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=JWT_EXPIRY_MINUTES)).timestamp()),
            "aud": "/admin/",
        }

        headers = {
            "alg": "HS256",
            "kid": key_id,
            "typ": "JWT",
        }

        return jwt.encode(payload, secret_bytes, algorithm="HS256", headers=headers)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self._session

    async def close(self) -> None:
        """Close the session if we own it."""
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> GhostAdminAPI:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    def _get_auth_headers(self) -> dict[str, str]:
        """Get authorization headers for Ghost Admin API."""
        return {
            "Authorization": f"Ghost {self._generate_token()}",
            "Accept-Version": "v5.0",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated request to the Ghost Admin API.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint (e.g., /ghost/api/admin/posts/)
            params: Query parameters
            json: JSON body for POST/PUT requests

        Returns:
            JSON response as a dictionary

        Raises:
            GhostAuthError: If authentication fails
            GhostNotFoundError: If the resource is not found
            GhostValidationError: If the request is invalid
            GhostConnectionError: If the connection fails
            GhostError: For other API errors
        """
        session = await self._get_session()
        url = f"{self.api_url}{endpoint}"
        headers = self._get_auth_headers()

        if json:
            headers["Content-Type"] = "application/json"

        try:
            async with session.request(
                method, url, headers=headers, params=params, json=json
            ) as response:
                if response.status == 401:
                    raise GhostAuthError("Authentication failed. Check your API key.")
                if response.status == 404:
                    raise GhostNotFoundError(f"Resource not found: {endpoint}")
                if response.status == 422:
                    data = await response.json()
                    errors = data.get("errors", [{}])
                    message = errors[0].get("message", "Validation failed")
                    raise GhostValidationError(message)
                if response.status >= 400:
                    text = await response.text()
                    raise GhostError(f"API error {response.status}: {text}")

                result: dict[str, Any] = await response.json()
                return result

        except aiohttp.ClientError as err:
            raise GhostConnectionError(f"Connection failed: {err}") from err

    async def _get(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make a GET request."""
        return await self._request("GET", endpoint, params=params)

    async def _post(
        self, endpoint: str, json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make a POST request."""
        return await self._request("POST", endpoint, json=json)

    async def _delete(self, endpoint: str) -> dict[str, Any]:
        """Make a DELETE request."""
        return await self._request("DELETE", endpoint)

    async def _put(
        self, endpoint: str, json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make a PUT request."""
        return await self._request("PUT", endpoint, json=json)

    # -------------------------------------------------------------------------
    # Site
    # -------------------------------------------------------------------------

    async def get_site(self) -> dict[str, Any]:
        """Get site information.

        Returns:
            Site info dict with title, description, url, etc.
        """
        data = await self._get("/ghost/api/admin/site/")
        return cast(dict[str, Any], data.get("site", {}))

    # -------------------------------------------------------------------------
    # Posts
    # -------------------------------------------------------------------------

    async def get_posts_count(self) -> dict[str, int]:
        """Get post counts by status.

        Returns:
            Dict with 'published', 'drafts', 'scheduled' counts.
        """
        published, drafts, scheduled = await asyncio.gather(
            self._get("/ghost/api/admin/posts/", {"limit": 1, "filter": "status:published"}),
            self._get("/ghost/api/admin/posts/", {"limit": 1, "filter": "status:draft"}),
            self._get("/ghost/api/admin/posts/", {"limit": 1, "filter": "status:scheduled"}),
        )

        return {
            "published": int(published.get("meta", {}).get("pagination", {}).get("total", 0)),
            "drafts": int(drafts.get("meta", {}).get("pagination", {}).get("total", 0)),
            "scheduled": int(scheduled.get("meta", {}).get("pagination", {}).get("total", 0)),
        }

    async def get_latest_post(self) -> dict[str, Any] | None:
        """Get the most recently published post.

        Returns:
            Post dict or None if no posts exist.
        """
        data = await self._get(
            "/ghost/api/admin/posts/",
            {"limit": 1, "order": "published_at desc", "filter": "status:published"},
        )
        posts = data.get("posts", [])
        return posts[0] if posts else None

    async def get_post(self, post_id: str) -> dict[str, Any] | None:
        """Get a post by ID.

        Args:
            post_id: The post ID.

        Returns:
            Post dict or None if not found.
        """
        try:
            data = await self._get(f"/ghost/api/admin/posts/{post_id}/")
            posts = data.get("posts", [])
            return posts[0] if posts else None
        except GhostNotFoundError:
            return None

    async def create_post(
        self,
        title: str,
        content: str,
        status: str = "draft",
        slug: str | None = None,
        excerpt: str | None = None,
        feature_image: str | None = None,
        tags: list[str] | None = None,
        published_at: str | None = None,
    ) -> dict[str, Any]:
        """Create a new post.

        Args:
            title: Post title.
            content: Post content (HTML or Markdown).
            status: Post status ('draft', 'published', 'scheduled').
            slug: Optional URL slug.
            excerpt: Optional post excerpt.
            feature_image: Optional feature image URL.
            tags: Optional list of tag names.
            published_at: Optional ISO 8601 datetime string for scheduled posts.

        Returns:
            Created post dict.
        """
        post_data: dict[str, Any] = {
            "title": title,
            "mobiledoc": _convert_to_mobiledoc(content),
            "status": status,
        }

        if slug:
            post_data["slug"] = slug
        if excerpt:
            post_data["custom_excerpt"] = excerpt
        if feature_image:
            post_data["feature_image"] = feature_image
        if tags:
            post_data["tags"] = [{"name": tag} for tag in tags]
        if published_at:
            post_data["published_at"] = published_at

        data = await self._post("/ghost/api/admin/posts/", {"posts": [post_data]})
        posts = data.get("posts", [])
        return posts[0] if posts else {}

    async def update_post(
        self,
        post_id: str,
        title: str | None = None,
        content: str | None = None,
        status: str | None = None,
        slug: str | None = None,
        excerpt: str | None = None,
        feature_image: str | None = None,
        tags: list[str] | None = None,
        published_at: str | None = None,
    ) -> dict[str, Any] | None:
        """Update an existing post.

        Args:
            post_id: The post ID to update.
            title: Optional new title.
            content: Optional new content (HTML or Markdown).
            status: Optional new status ('draft', 'published', 'scheduled').
            slug: Optional new URL slug.
            excerpt: Optional new excerpt.
            feature_image: Optional new feature image URL.
            tags: Optional new list of tag names.
            published_at: Optional new published_at timestamp.

        Returns:
            Updated post dict or None if not found.
        """
        post_data: dict[str, Any] = {}

        if title is not None:
            post_data["title"] = title
        if content is not None:
            post_data["mobiledoc"] = _convert_to_mobiledoc(content)
        if status is not None:
            post_data["status"] = status
        if slug is not None:
            post_data["slug"] = slug
        if excerpt is not None:
            post_data["custom_excerpt"] = excerpt
        if feature_image is not None:
            post_data["feature_image"] = feature_image
        if tags is not None:
            post_data["tags"] = [{"name": tag} for tag in tags]
        if published_at is not None:
            post_data["published_at"] = published_at

        try:
            data = await self._put(f"/ghost/api/admin/posts/{post_id}/", {"posts": [post_data]})
            posts = data.get("posts", [])
            return posts[0] if posts else None
        except GhostNotFoundError:
            return None

    async def delete_post(self, post_id: str) -> bool:
        """Delete a post by ID.

        Args:
            post_id: The post ID to delete.

        Returns:
            True if deleted successfully, False otherwise.
        """
        try:
            await self._delete(f"/ghost/api/admin/posts/{post_id}/")
            return True
        except GhostNotFoundError:
            return False

    # -------------------------------------------------------------------------
    # Members
    # -------------------------------------------------------------------------

    async def get_members_count(self) -> dict[str, int]:
        """Get member counts from stats endpoint.

        Returns:
            Dict with 'total', 'paid', 'free', 'comped' counts.
        """
        data = await self._get("/ghost/api/admin/members/stats/count/")

        total = data.get("total", 0)
        history = data.get("data", [])

        if history:
            latest = history[-1]
            return {
                "total": total,
                "paid": latest.get("paid", 0),
                "free": latest.get("free", 0),
                "comped": latest.get("comped", 0),
            }

        return {"total": total, "paid": 0, "free": 0, "comped": 0}

    async def get_mrr(self) -> dict[str, int]:
        """Get MRR (Monthly Recurring Revenue) data.

        Returns:
            Dict with currency keys and MRR values in cents.
            E.g., {"usd": 12284, "eur": 5000}
        """
        data = await self._get("/ghost/api/admin/members/stats/mrr/")

        result: dict[str, int] = {}
        for currency_data in data.get("data", []):
            currency = currency_data.get("currency", "usd")
            values = currency_data.get("data", [])
            if values:
                latest = values[-1]
                result[currency] = latest.get("value", 0)

        return result

    # -------------------------------------------------------------------------
    # Newsletters
    # -------------------------------------------------------------------------

    async def get_newsletters(self) -> list[dict[str, Any]]:
        """Get newsletters with subscriber counts.

        Returns:
            List of newsletter dicts.
        """
        data = await self._get(
            "/ghost/api/admin/newsletters/",
            {"include": "count.members"},
        )
        return cast(list[dict[str, Any]], data.get("newsletters", []))

    # -------------------------------------------------------------------------
    # Email / Latest Email
    # -------------------------------------------------------------------------

    def _build_email_stats(self, post: dict[str, Any]) -> dict[str, Any]:
        """Build email stats dict from post with email data."""
        email = post["email"]
        email_count = email.get("email_count", 0)
        opened_count = email.get("opened_count", 0)
        count_data = post.get("count", {})
        clicked_count = count_data.get("clicks", 0) or 0

        return {
            "title": post.get("title"),
            "slug": post.get("slug"),
            "published_at": post.get("published_at"),
            "email_count": email_count,
            "delivered_count": email.get("delivered_count", 0),
            "opened_count": opened_count,
            "clicked_count": clicked_count,
            "failed_count": email.get("failed_count", 0),
            "open_rate": round(opened_count / email_count * 100) if email_count > 0 else 0,
            "click_rate": round(clicked_count / email_count * 100) if email_count > 0 else 0,
            "subject": email.get("subject"),
            "submitted_at": email.get("submitted_at"),
        }

    async def get_latest_email(self) -> dict[str, Any] | None:
        """Get the most recently sent email newsletter.

        Returns:
            Email stats dict or None if no emails have been sent.
        """
        data = await self._get(
            "/ghost/api/admin/posts/",
            {
                "limit": 10,
                "order": "published_at desc",
                "filter": "status:published",
                "include": "email,count.clicks",
            },
        )

        for post in data.get("posts", []):
            if post.get("email"):
                return self._build_email_stats(post)

        return None

    # -------------------------------------------------------------------------
    # Comments
    # -------------------------------------------------------------------------

    async def get_comments_count(self) -> int:
        """Get total comments count.

        Returns:
            Total number of comments.
        """
        data = await self._get("/ghost/api/admin/comments/", {"limit": 1})
        return int(data.get("meta", {}).get("pagination", {}).get("total", 0))

    # -------------------------------------------------------------------------
    # Tiers
    # -------------------------------------------------------------------------

    async def get_tiers(self) -> list[dict[str, Any]]:
        """Get subscription tiers.

        Returns:
            List of tier dicts.
        """
        data = await self._get("/ghost/api/admin/tiers/")
        return cast(list[dict[str, Any]], data.get("tiers", []))

    # -------------------------------------------------------------------------
    # ActivityPub / Social Web
    # -------------------------------------------------------------------------

    async def get_activitypub_stats(self) -> dict[str, int]:
        """Get ActivityPub follower/following counts (public endpoints).

        Returns:
            Dict with 'followers' and 'following' counts.
        """
        session = await self._get_session()
        headers = {"Accept": "application/activity+json"}

        stats = {"followers": 0, "following": 0}

        async def fetch_count(endpoint: str, key: str) -> None:
            try:
                url = f"{self.api_url}/.ghost/activitypub/{endpoint}/index"
                async with session.get(url, headers=headers) as response:
                    if response.ok:
                        data = await response.json()
                        stats[key] = data.get("totalItems", 0)
            except Exception as err:
                _LOGGER.debug("ActivityPub %s not available: %s", endpoint, err)

        await asyncio.gather(
            fetch_count("followers", "followers"),
            fetch_count("following", "following"),
        )

        return stats

    # -------------------------------------------------------------------------
    # Webhooks
    # -------------------------------------------------------------------------

    async def create_webhook(self, event: str, target_url: str) -> dict[str, Any]:
        """Create a webhook in Ghost.

        Ghost automatically associates the webhook with the integration
        that owns the API key being used.

        Args:
            event: Event type (e.g., 'member.added', 'post.published')
            target_url: URL to POST webhook payloads to

        Returns:
            Created webhook dict.
        """
        data = await self._post(
            "/ghost/api/admin/webhooks/",
            {"webhooks": [{"event": event, "target_url": target_url}]},
        )
        webhooks = cast(list[dict[str, Any]], data.get("webhooks", [{}]))
        return webhooks[0]

    async def delete_webhook(self, webhook_id: str) -> None:
        """Delete a webhook from Ghost.

        Args:
            webhook_id: The webhook ID to delete.
        """
        await self._delete(f"/ghost/api/admin/webhooks/{webhook_id}/")

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    async def validate_credentials(self) -> bool:
        """Validate the API credentials.

        Returns:
            True if credentials are valid, False otherwise.
        """
        try:
            await self.get_site()
            return True
        except GhostError:
            return False
