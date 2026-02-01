"""Tests for the Ghost Admin API client."""

import pytest
from aioresponses import aioresponses

from aioghost import GhostAdminAPI, GhostAuthError


@pytest.fixture
def api():
    """Create a test API client."""
    return GhostAdminAPI(
        site_url="https://test.ghost.io",
        admin_api_key="650b7a9f8e8c1234567890ab:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
    )


@pytest.mark.asyncio
async def test_get_site(api: GhostAdminAPI):
    """Test getting site info."""
    with aioresponses() as m:
        m.get(
            "https://test.ghost.io/ghost/api/admin/site/",
            payload={"site": {"title": "Test Site", "url": "https://test.ghost.io"}},
        )

        async with api:
            site = await api.get_site()

        assert site["title"] == "Test Site"
        assert site["url"] == "https://test.ghost.io"


@pytest.mark.asyncio
async def test_get_members_count(api: GhostAdminAPI):
    """Test getting member counts."""
    with aioresponses() as m:
        m.get(
            "https://test.ghost.io/ghost/api/admin/members/stats/count/",
            payload={
                "total": 100,
                "data": [{"paid": 10, "free": 85, "comped": 5}],
            },
        )

        async with api:
            members = await api.get_members_count()

        assert members["total"] == 100
        assert members["paid"] == 10
        assert members["free"] == 85
        assert members["comped"] == 5


@pytest.mark.asyncio
async def test_invalid_api_key_format():
    """Test that invalid API key format raises error."""
    api = GhostAdminAPI(
        site_url="https://test.ghost.io",
        admin_api_key="invalid-key-no-colon",
    )

    with pytest.raises(GhostAuthError, match="Invalid API key format"):
        api._generate_token()


@pytest.mark.asyncio
async def test_invalid_api_key_secret():
    """Test that invalid API key secret raises error."""
    api = GhostAdminAPI(
        site_url="https://test.ghost.io",
        admin_api_key="validid:not-hex-string",
    )

    with pytest.raises(GhostAuthError, match="Invalid API key secret"):
        api._generate_token()


@pytest.mark.asyncio
async def test_validate_credentials_success(api: GhostAdminAPI):
    """Test credential validation success."""
    with aioresponses() as m:
        m.get(
            "https://test.ghost.io/ghost/api/admin/site/",
            payload={"site": {"title": "Test"}},
        )

        async with api:
            valid = await api.validate_credentials()

        assert valid is True


@pytest.mark.asyncio
async def test_validate_credentials_failure(api: GhostAdminAPI):
    """Test credential validation failure."""
    with aioresponses() as m:
        m.get(
            "https://test.ghost.io/ghost/api/admin/site/",
            status=401,
        )

        async with api:
            valid = await api.validate_credentials()

        assert valid is False
