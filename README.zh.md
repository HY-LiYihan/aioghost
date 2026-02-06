# aioghost

[Ghost 管理员 API](https://ghost.org/docs/admin-api/) 的异步 Python 客户端。

## 安装

```bash
pip install aioghost
```

## 快速开始

```python
import asyncio
from aioghost import GhostAdminAPI

async def main():
    async with GhostAdminAPI(
        api_url="https://your-site.ghost.io",
        admin_api_key="your-admin-api-key"
    ) as api:
        # 获取站点信息
        site = await api.get_site()
        print(f"站点: {site['title']}")

        # 获取会员数量
        members = await api.get_members_count()
        print(f"总会员数: {members['total']}")
        print(f"付费会员数: {members['paid']}")

        # 获取 MRR（月经常性收入）
        mrr = await api.get_mrr()
        print(f"MRR: ${mrr.get('usd', 0) / 100:.2f}")

asyncio.run(main())
```

## 功能特性

- **完全异步** — 基于 `aiohttp` 构建，非阻塞 I/O
- **类型提示** — 完整的类型注解，支持 IDE 智能提示
- **上下文管理器** — 使用 `async with` 自动清理会话
- **并行请求** — 使用 `asyncio.gather()` 实现高效批处理
- **正确异常** — 为不同错误场景提供类型化异常

## API 覆盖

### 站点

| 端点      | 方法        |
|-------------|---------------|
| 站点信息   | `get_site()`  |

### 文章

| 端点              | 方法                         |
|-------------------|--------------------------------|
| 文章数量         | `get_posts_count()`            |
| 最新文章         | `get_latest_post()`            |
| 根据 ID 获取文章 | `get_post(post_id)`            |
| 创建文章         | `create_post(title, content)`  |
| 更新文章         | `update_post(post_id, ...)`    |
| 删除文章         | `delete_post(post_id)`         |

### 会员

| 端点          | 方法                 |
|---------------|------------------------|
| 会员数量        | `get_members_count()`  |
| MRR（月收入）    | `get_mrr()`            |

### 订阅

| 端点        | 方法                  |
|--------------|-------------------------|
| 订阅列表      | `get_newsletters()`      |
| 最新邮件       | `get_latest_email()`     |

### 评论

| 端点            | 方法                   |
|-----------------|--------------------------|
| 评论数量        | `get_comments_count()`   |

### 会员等级

| 端点   | 方法        |
|---------|---------------|
| 会员等级 | `get_tiers()` |

### ActivityPub（联邦网络）

| 端点              | 方法                      |
|---------------------|-----------------------------|
| ActivityPub 统计 | `get_activitypub_stats()`   |

### Webhooks

| 端点   | 方法                                             |
|----------|----------------------------------------------------|
| Webhooks | `create_webhook()`, `delete_webhook()`             |

### 验证

| 端点               | 方法                     |
|--------------------|----------------------------|
| 验证凭据 | `validate_credentials()`   |

## 脚本工具

快速设置、测试和批量操作 Ghost 管理员 API 的实用脚本。

### 快速开始

#### 1. 交互式设置

运行设置向导配置凭据：

```bash
python -m scripts.setup
```

这将引导您输入 Ghost 站点 URL 和管理员 API 密钥，然后自动创建 `.env` 文件。

#### 2. 测试连接

验证您的配置是否正常工作：

```bash
python -m scripts.test_connection
```

#### 3. 测试文章操作

测试创建、读取、更新和删除文章：

```bash
python -m scripts.test_post
```

### 批量操作

批处理脚本会自动检测是**创建**还是**更新**文章：
- 如果 Markdown 文件有 `id` 字段 → **更新**现有文章
- 如果没有 `id` 字段 → **创建**新文章并将 ID 写回文件

输出格式显示**文件名**，便于识别。

#### 从 Markdown 文件创建文章

从目录中的 `.md` 文件创建多篇文章：

```bash
python -m scripts.batch_posts create ./posts
```

使用自定义模式：

```bash
python -m scripts.batch_posts create ./posts --pattern "draft-*.md"
```

预览而不创建：

```bash
python -m scripts.batch_posts create ./posts --dry-run
```

#### 更新现有文章

通过指定 ID 更新文章：

```bash
python -m scripts.batch_posts update ./posts --post-ids "post-id-1" "post-id-2"
```

#### 删除文章

通过 ID 删除文章：

```bash
python -m scripts.batch_posts delete "post-id-1" "post-id-2"
```

### Frontmatter 格式

您可以使用 frontmatter 在 Markdown 文件中添加元数据：

```markdown
---
title: 我的精彩文章
status: published
slug: my-awesome-post
url: /my-awesome-post
canonical_url: https://mysite.com/posts/my-awesome-post
tags: 技术, python, ghost
excerpt: 文章简要概述
feature_image: https://example.com/image.jpg
published_at: 2026-02-05T10:00:00.000Z
---

# 我的精彩文章

这是您文章的内容...
```

| 字段              | 描述                       | 必填                           |
|-----------------|-----------------------------|----------------------------------|
| `title`           | 文章标题                   | 否（默认为文件名）            |
| `status`           | `draft`、`published` 或 `scheduled` | 否（默认为 `draft`）           |
| `id`              | Ghost 文章 ID（用于更新）    | 否（如果存在，则更新现有文章） |
| `slug`            | URL slug                    | 否                               |
| `url`             | 规范 URL（用于自定义永久链接） | 否                               |
| `canonical_url`    | 规范 URL（用于 SEO，覆盖 Ghost 默认） | 否                               |
| `tags`            | 逗号分隔的标签            | 否                               |
| `excerpt`          | 文章摘要                   | 否                               |
| `feature_image`    | 特色图片 URL                | 否                               |
| `published_at`      | ISO 8601 日期时间（用于计划发布）    | 否                               |

## 获取您的管理员 API 密钥

1. 登录您的 Ghost 管理面板
2. 进入 **设置 → 集成**
3. 点击 **添加自定义集成**
4. 复制 **管理员 API 密钥**（格式：`id:secret`）

## 异常

```python
from aioghost import (
    GhostError,           # 基础异常
    GhostAuthError,       # 无效的 API 密钥
    GhostConnectionError, # 网络错误
    GhostNotFoundError,   # 404 响应
    GhostValidationError, # 无效请求
)
```

## 传递您自己的会话

如果要重用现有的 `aiohttp.ClientSession`：

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
        # api 超出作用域时不会关闭会话
```

---

## 版权与许可证

版权所有 (c) 2013-2026 Ghost Foundation - 以 [MIT 许可证](LICENSE) 发布。
Ghost 和 Ghost 徽标是 Ghost Foundation Ltd. 的商标。请参阅我们的[商标政策](https://ghost.org/trademark/)了解可接受的用法。
