# aioghost

Async Python client for the [Ghost Admin API](https://ghost.org/docs/admin-api/).

## Installation

```bash
pip install aioghost
```

## Quick Start

```python
import asyncio
from aioghost import GhostAdminAPI

async def main():
    async with GhostAdminAPI(
        api_url="https://your-site.ghost.io",
        admin_api_key="your-admin-api-key"
    ) as api:
        # Get site info
        site = await api.get_site()
        print(f"Site: {site['title']}")

        # Get member counts
        members = await api.get_members_count()
        print(f"Total members: {members['total']}")
        print(f"Paid members: {members['paid']}")

        # Get MRR
        mrr = await api.get_mrr()
        print(f"MRR: ${mrr.get('usd', 0) / 100:.2f}")

asyncio.run(main())
```

## Script Tools

Utility scripts for quick setup, testing, and batch operations with Ghost Admin API.

### Getting Started

#### 1. Interactive Setup

Run setup wizard to configure your credentials:

```bash
python -m scripts.setup
```

This will guide you through entering your Ghost site URL and Admin API Key, then automatically create a `.env` file.

#### 2. Test Connection

Verify your configuration works:

```bash
python -m scripts.test_connection
```

#### 3. Test Post Operations

Test creating, reading, updating, and deleting a post:

```bash
python -m scripts.test_post
```

### Batch Operations

The batch script automatically detects whether to **create** or **update** posts:
- If the Markdown file has an `id` field → **updates** the existing post
- If no `id` field → **creates** a new post and writes the ID back to the file

Output format shows the **file name** for easy identification.

#### Create Posts from Markdown Files

Create multiple posts from `.md` files in a directory:

```bash
python -m scripts.batch_posts create ./posts
```

Use a custom pattern:

```bash
python -m scripts.batch_posts create ./posts --pattern "draft-*.md"
```

Preview without creating:

```bash
python -m scripts.batch_posts create ./posts --dry-run
```

#### Update Existing Posts

Update posts by specifying their IDs:

```bash
python -m scripts.batch_posts update ./posts --post-ids "post-id-1" "post-id-2"
```

#### Delete Posts

Delete posts by their IDs:

```bash
python -m scripts.batch_posts delete "post-id-1" "post-id-2"
```

### Frontmatter Format

You can add metadata to your Markdown files using frontmatter:

```markdown
---
title: My Awesome Post
status: published
slug: my-awesome-post
url: /my-awesome-post
canonical_url: https://mysite.com/posts/my-awesome-post
tags: technology, python, ghost
excerpt: A brief summary of the post
feature_image: https://example.com/image.jpg
published_at: 2026-02-05T10:00:00.000Z
---

# My Awesome Post

This is the content of your post...
```

| Field | Description | Required |
|-------|-------------|----------|
| `title` | Post title | No (defaults to filename) |
| `status` | `draft`, `published`, or `scheduled` | No (defaults to `draft`) |
| `id` | Ghost post ID (for updates) | No (if present, updates existing post) |
| `slug` | URL slug | No |
| `url` | Canonical URL (for custom permalinks) | No |
| `canonical_url` | Canonical URL (for SEO, overrides Ghost's default) | No |
| `tags` | Comma-separated tags | No |
| `excerpt` | Post excerpt | No |
| `feature_image` | Feature image URL | No |
| `published_at` | ISO 8601 datetime (for scheduled posts) | No |

## Features

- **Fully async** — Built on `aiohttp` for non-blocking I/O
- **Type hints** — Full type annotations for IDE support
- **Context manager** — Automatic session cleanup with `async with`
- **Parallel requests** — Uses `asyncio.gather()` for efficient batching
- **Proper exceptions** — Typed exceptions for different error cases

## API Coverage

### Site

| Endpoint    | Method        |
|-------------|---------------|
| Site info   | `get_site()`  |

### Posts

| Endpoint         | Method                         |
|------------------|--------------------------------|
| Posts count      | `get_posts_count()`            |
| Latest post      | `get_latest_post()`            |
| Get post by ID   | `get_post(post_id)`            |
| Create post      | `create_post(title, content)`  |
| Update post      | `update_post(post_id, ...)`    |
| Delete post      | `delete_post(post_id)`         |

### Members

| Endpoint        | Method                 |
|-----------------|------------------------|
| Members count   | `get_members_count()`  |
| MRR             | `get_mrr()`            |

### Newsletters

| Endpoint      | Method                  |
|---------------|-------------------------|
| Newsletters   | `get_newsletters()`      |
| Latest email  | `get_latest_email()`     |

### Comments

| Endpoint         | Method                   |
|------------------|--------------------------|
| Comments count   | `get_comments_count()`   |

### Tiers

| Endpoint   | Method        |
|------------|---------------|
| Tiers      | `get_tiers()` |

### ActivityPub

| Endpoint            | Method                      |
|---------------------|-----------------------------|
| ActivityPub stats   | `get_activitypub_stats()`   |

### Webhooks

| Endpoint   | Method                                             |
|------------|----------------------------------------------------|
| Webhooks   | `create_webhook()`, `delete_webhook()`             |

### Validation

| Endpoint              | Method                     |
|-----------------------|----------------------------|
| Validate credentials  | `validate_credentials()`   |

## Getting Your Admin API Key

1. Log in to your Ghost Admin panel
2. Go to **Settings → Integrations**
3. Click **Add custom integration**
4. Copy the **Admin API Key** (format: `id:secret`)

## Exceptions

```python
from aioghost import (
    GhostError,           # Base exception
    GhostAuthError,       # Invalid API key
    GhostConnectionError, # Network error
    GhostNotFoundError,   # 404 response
    GhostValidationError, # Invalid request
)
```

## Passing Your Own Session

If you want to reuse an existing `aiohttp.ClientSession`:

```python
import aiohttp
from aioghost import GhostAdminAPI

async def main():
    async with aiohttp.ClientSession() as session:
        api = GhostAdminAPI(
            api_url="https://your-site.ghost.io",
            admin_api_key="your-key",
            session=session,
        )
        site = await api.get_site()
        # Session is NOT closed when api goes out of scope
```

&nbsp;

---

## Copyright & License

Copyright (c) 2013-2026 Ghost Foundation - Released under the [MIT license](LICENSE).
Ghost and the Ghost Logo are trademarks of Ghost Foundation Ltd. Please see our [trademark policy](https://ghost.org/trademark/) for info on acceptable usage.
