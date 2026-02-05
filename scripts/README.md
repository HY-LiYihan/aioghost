# Batch Operations Scripts

Utilities for batch creating, updating, and deleting Ghost posts from local files.

## Setup

1. Copy `.env.example` to `.env` and fill in your Ghost credentials:

```bash
cp .env.example .env
```

2. Edit `.env`:

```env
GHOST_API_URL=https://your-site.ghost.io
GHOST_ADMIN_API_KEY=your-admin-api-key
```

## Usage

### Create posts from Markdown files

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

### Update existing posts

Update posts by specifying their IDs:

```bash
python -m scripts.batch_posts update ./posts --post-ids "post-id-1" "post-id-2" "post-id-3"
```

### Delete posts

Delete posts by their IDs:

```bash
python -m scripts.batch_posts delete "post-id-1" "post-id-2" "post-id-3"
```

## Markdown Frontmatter

You can add metadata to your Markdown files using frontmatter:

```markdown
---
title: My Awesome Post
status: published
slug: my-awesome-post
tags: technology, python, ghost
excerpt: A brief summary of the post
feature_image: https://example.com/image.jpg
published_at: 2026-02-05T10:00:00.000Z
---

# My Awesome Post

This is the content of your post...
```

### Frontmatter Fields

| Field | Description | Required |
|-------|-------------|----------|
| `title` | Post title | No (defaults to filename) |
| `status` | `draft`, `published`, or `scheduled` | No (defaults to `draft`) |
| `slug` | URL slug | No |
| `tags` | Comma-separated tags | No |
| `excerpt` | Post excerpt | No |
| `feature_image` | Feature image URL | No |
| `published_at` | ISO 8601 datetime (for scheduled posts) | No |
