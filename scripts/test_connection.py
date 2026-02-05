"""Test script to verify Ghost Admin API connection."""

from __future__ import annotations

import asyncio
import os
import sys

import dotenv
from aioghost import GhostAdminAPI, GhostAuthError, GhostConnectionError, GhostError


async def test_connection() -> int:
    """Test connection to Ghost Admin API.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    print("Testing Ghost Admin API connection...")
    print("-" * 40)

    # Load environment variables
    dotenv.load_dotenv()

    api_url = os.getenv("GHOST_API_URL")
    admin_api_key = os.getenv("GHOST_ADMIN_API_KEY")

    if not api_url or not admin_api_key:
        print("[ERROR] Missing environment variables")
        print("  Make sure .env file exists with:")
        print("    GHOST_API_URL")
        print("    GHOST_ADMIN_API_KEY")
        return 1

    print(f"API URL: {api_url}")
    print()

    try:
        async with GhostAdminAPI(api_url=api_url, admin_api_key=admin_api_key) as api:
            # Test basic connection
            site = await api.get_site()
            print("[OK] Connection successful!")
            print()
            print(f"Site:  {site.get('title', 'N/A')}")
            print(f"URL:   {site.get('url', 'N/A')}")
            print(f"Desc:  {site.get('description', 'N/A')[:50]}...")
            print()

            # Test getting post counts
            posts_count = await api.get_posts_count()
            print(f"Posts:")
            print(f"  Published: {posts_count.get('published', 0)}")
            print(f"  Drafts:    {posts_count.get('drafts', 0)}")
            print(f"  Scheduled: {posts_count.get('scheduled', 0)}")
            print()

            # Test latest post
            latest = await api.get_latest_post()
            if latest:
                print(f"Latest post: {latest.get('title', 'N/A')}")
            else:
                print("No published posts yet")

        print()
        print("-" * 40)
        print("[OK] All tests passed!")
        return 0

    except GhostAuthError as e:
        print(f"[ERROR] Authentication failed: {e}")
        print()
        print("Please check your API key in .env file")
        return 1
    except GhostConnectionError as e:
        print(f"[ERROR] Connection failed: {e}")
        print()
        print("Please check your API URL and network connection")
        return 1
    except GhostError as e:
        print(f"[ERROR] API error: {e}")
        return 1
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(test_connection()))
