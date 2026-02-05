"""
Batch operations for Ghost posts.

This script helps you create, update, and delete Ghost posts from local Markdown files.
"""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path
from typing import Any

import dotenv
from aioghost import GhostAdminAPI
from aioghost.exceptions import GhostError


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from content.

    Args:
        content: File content with optional frontmatter.

    Returns:
        Tuple of (metadata dict, content without frontmatter).
    """
    lines = content.split("\n")

    if not lines or not lines[0].startswith("---"):
        return {}, content

    # Find end of frontmatter
    end_idx = -1
    for i, line in enumerate(lines[1:], start=1):
        if line == "---":
            end_idx = i
            break

    if end_idx == -1:
        return {}, content

    # Parse frontmatter (simple key: value parsing)
    metadata: dict[str, Any] = {}
    for line in lines[1:end_idx]:
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()

    # Join remaining content
    body = "\n".join(lines[end_idx + 1 :])
    return metadata, body


async def create_post_from_file(api: GhostAdminAPI, file_path: Path, dry_run: bool = False) -> None:
    """Create a post from a Markdown file.

    Args:
        api: GhostAdminAPI instance.
        file_path: Path to the Markdown file.
        dry_run: If True, only print what would be done.
    """
    content = file_path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(content)

    title = metadata.get("title", file_path.stem)
    status = metadata.get("status", "draft")
    slug = metadata.get("slug")
    tags = metadata.get("tags", "").split(",") if metadata.get("tags") else None
    excerpt = metadata.get("excerpt")
    feature_image = metadata.get("feature_image")
    published_at = metadata.get("published_at")

    if dry_run:
        print(f"[DRY RUN] Would create post: {title}")
        print(f"  Status: {status}")
        print(f"  Slug: {slug or 'auto-generated'}")
        if tags:
            print(f"  Tags: {', '.join(tags)}")
        return

    try:
        post = await api.create_post(
            title=title,
            content=body,
            status=status,
            slug=slug,
            excerpt=excerpt,
            feature_image=feature_image,
            tags=tags,
            published_at=published_at,
        )
        print(f"✓ Created post: {title} (ID: {post.get('id')})")
    except GhostError as e:
        print(f"✗ Failed to create {title}: {e}")


async def update_post_from_file(api: GhostAdminAPI, post_id: str, file_path: Path, dry_run: bool = False) -> None:
    """Update a post from a Markdown file.

    Args:
        api: GhostAdminAPI instance.
        post_id: The post ID to update.
        file_path: Path to the Markdown file.
        dry_run: If True, only print what would be done.
    """
    content = file_path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(content)

    if dry_run:
        print(f"[DRY RUN] Would update post: {post_id}")
        return

    try:
        post = await api.update_post(
            post_id=post_id,
            title=metadata.get("title"),
            content=body,
            status=metadata.get("status"),
            slug=metadata.get("slug"),
            excerpt=metadata.get("excerpt"),
            feature_image=metadata.get("feature_image"),
            tags=metadata.get("tags", "").split(",") if metadata.get("tags") else None,
            published_at=metadata.get("published_at"),
        )
        if post:
            print(f"✓ Updated post: {post.get('title', post_id)}")
        else:
            print(f"✗ Post not found: {post_id}")
    except GhostError as e:
        print(f"✗ Failed to update {post_id}: {e}")


async def delete_post(api: GhostAdminAPI, post_id: str, dry_run: bool = False) -> None:
    """Delete a post by ID.

    Args:
        api: GhostAdminAPI instance.
        post_id: The post ID to delete.
        dry_run: If True, only print what would be done.
    """
    if dry_run:
        print(f"[DRY RUN] Would delete post: {post_id}")
        return

    try:
        success = await api.delete_post(post_id)
        if success:
            print(f"✓ Deleted post: {post_id}")
        else:
            print(f"✗ Post not found: {post_id}")
    except GhostError as e:
        print(f"✗ Failed to delete {post_id}: {e}")


async def batch_create(
    api: GhostAdminAPI,
    directory: str,
    pattern: str = "*.md",
    dry_run: bool = False,
) -> None:
    """Create multiple posts from Markdown files in a directory.

    Args:
        api: GhostAdminAPI instance.
        directory: Path to directory containing Markdown files.
        pattern: File pattern to match (default: *.md).
        dry_run: If True, only print what would be done.
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        print(f"✗ Directory not found: {directory}")
        return

    files = sorted(dir_path.glob(pattern))
    if not files:
        print(f"No files found matching pattern: {pattern}")
        return

    print(f"Found {len(files)} file(s) to process\n")

    tasks = [create_post_from_file(api, f, dry_run) for f in files]
    await asyncio.gather(*tasks)


async def batch_update(
    api: GhostAdminAPI,
    directory: str,
    post_ids: list[str] | None = None,
    pattern: str = "*.md",
    dry_run: bool = False,
) -> None:
    """Update multiple posts from Markdown files.

    Args:
        api: GhostAdminAPI instance.
        directory: Path to directory containing Markdown files.
        post_ids: List of post IDs corresponding to files (by order).
        pattern: File pattern to match (default: *.md).
        dry_run: If True, only print what would be done.
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        print(f"✗ Directory not found: {directory}")
        return

    files = sorted(dir_path.glob(pattern))
    if not files:
        print(f"No files found matching pattern: {pattern}")
        return

    if post_ids is None:
        print("No post IDs provided. Cannot update.")
        return

    if len(files) != len(post_ids):
        print(f"⚠ File count ({len(files)}) doesn't match post ID count ({len(post_ids)})")

    tasks = [
        update_post_from_file(api, post_ids[i], files[i], dry_run)
        for i in range(min(len(files), len(post_ids)))
    ]
    await asyncio.gather(*tasks)


async def batch_delete(
    api: GhostAdminAPI,
    post_ids: list[str],
    dry_run: bool = False,
) -> None:
    """Delete multiple posts by ID.

    Args:
        api: GhostAdminAPI instance.
        post_ids: List of post IDs to delete.
        dry_run: If True, only print what would be done.
    """
    print(f"Deleting {len(post_ids)} post(s)\n")
    tasks = [delete_post(api, pid, dry_run) for pid in post_ids]
    await asyncio.gather(*tasks)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Batch operations for Ghost posts")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Create command
    create_parser = subparsers.add_parser("create", help="Create posts from Markdown files")
    create_parser.add_argument("directory", help="Directory containing Markdown files")
    create_parser.add_argument("--pattern", default="*.md", help="File pattern (default: *.md)")
    create_parser.add_argument("--dry-run", action="store_true", help="Show what would be done without executing")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update posts from Markdown files")
    update_parser.add_argument("directory", help="Directory containing Markdown files")
    update_parser.add_argument("post-ids", nargs="*", help="Post IDs to update (by order of files)")
    update_parser.add_argument("--pattern", default="*.md", help="File pattern (default: *.md)")
    update_parser.add_argument("--dry-run", action="store_true", help="Show what would be done without executing")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete posts by ID")
    delete_parser.add_argument("post-ids", nargs="+", help="Post IDs to delete")
    delete_parser.add_argument("--dry-run", action="store_true", help="Show what would be done without executing")

    args = parser.parse_args()

    # Load environment variables
    dotenv.load_dotenv()

    api_url = os.getenv("GHOST_API_URL")
    admin_api_key = os.getenv("GHOST_ADMIN_API_KEY")

    if not api_url or not admin_api_key:
        print("✗ Missing required environment variables: GHOST_API_URL, GHOST_ADMIN_API_KEY")
        return

    async with GhostAdminAPI(api_url=api_url, admin_api_key=admin_api_key) as api:
        if args.command == "create":
            await batch_create(api, args.directory, args.pattern, args.dry_run)
        elif args.command == "update":
            await batch_update(api, args.directory, args.post_ids, args.pattern, args.dry_run)
        elif args.command == "delete":
            await batch_delete(api, args.post_ids, args.dry_run)


if __name__ == "__main__":
    asyncio.run(main())
