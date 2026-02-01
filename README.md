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

## Features

- **Fully async** — Built on `aiohttp` for non-blocking I/O
- **Type hints** — Full type annotations for IDE support
- **Context manager** — Automatic session cleanup with `async with`
- **Parallel requests** — Uses `asyncio.gather()` for efficient batching
- **Proper exceptions** — Typed exceptions for different error cases

## API Coverage

| Endpoint | Method |
|----------|--------|
| Site info | `get_site()` |
| Posts count | `get_posts_count()` |
| Latest post | `get_latest_post()` |
| Members count | `get_members_count()` |
| MRR | `get_mrr()` |
| Newsletters | `get_newsletters()` |
| Latest email | `get_latest_email()` |
| Comments count | `get_comments_count()` |
| Tiers | `get_tiers()` |
| ActivityPub stats | `get_activitypub_stats()` |
| Webhooks | `create_webhook()`, `delete_webhook()` |
| Validate credentials | `validate_credentials()` |

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

## License

MIT License - see [LICENSE](LICENSE) for details.
