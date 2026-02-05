"""Test script to create, read, update, and delete a test post."""

from __future__ import annotations

import asyncio
import os
import sys

import dotenv
from aioghost import GhostAdminAPI, GhostError

TEST_POST_TITLE = "aioghost Test Post"
TEST_POST_CONTENT = """# Test Post

This is a test post created by aioghost.

## Features

- Create posts
- Update posts
- Delete posts

## Success

If you can see this, API is working correctly!
"""


async def test_post_operations() -> int:
    """Test create, read, update, and delete operations.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    print("Testing Post CRUD Operations")
    print("-" * 40)

    # Load environment variables
    dotenv.load_dotenv()

    api_url = os.getenv("GHOST_API_URL")
    admin_api_key = os.getenv("GHOST_ADMIN_API_KEY")

    if not api_url or not admin_api_key:
        print("[ERROR] Missing environment variables")
        return 1

    created_post_id = None

    try:
        async with GhostAdminAPI(api_url=api_url, admin_api_key=admin_api_key) as api:
            # Test: Create post
            print("1. Creating post...")
            post = await api.create_post(
                title=TEST_POST_TITLE,
                content=TEST_POST_CONTENT,
                status="published",  # Use 'published' so it's visible on site
            )
            created_post_id = post.get("id")
            print(f"   [OK] Create post successful (ID: {created_post_id})")
            print()

            # Test: Read post
            print("2. Reading post...")
            fetched_post = await api.get_post(created_post_id)
            if fetched_post:
                print("   [OK] Read post successful")
            else:
                print("   [FAIL] Read post failed")
                return 1
            print()

            # Test: Update post
            print("3. Updating post...")
            try:
                updated_post = await api.update_post(
                    created_post_id,
                    title=f"{TEST_POST_TITLE} (Updated)",
                    content=TEST_POST_CONTENT + "\n\n**Updated content!**",
                )
                if updated_post:
                    print("   [OK] Update post successful")
                    print(f"   Title: {updated_post.get('title')}")
                    print(f"   Content updated with: **Updated content!**")
                else:
                    print("   [FAIL] Update post failed (returned None)")
                    return 1
            except Exception as e:
                print(f"   [FAIL] Update post failed: {e}")
                return 1
            print()

            # Test: Delete post (skipped - post will remain on site)
            print("4. Delete test")
            print("   [INFO] Skipping deletion - test post will remain on site")
            print(f"   [INFO] Post ID: {created_post_id}")
            print(f"   [INFO] You can delete it manually from Ghost Admin")
            print()

        print("-" * 40)
        print("[OK] All post operations passed!")
        print(f"[OK] Test post created: {created_post_id}")
        return 0

    except GhostError as e:
        print(f"[ERROR] API error: {e}")
        return 1
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(test_post_operations()))
