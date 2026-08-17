#!/usr/bin/env python3
"""Create a new blog post from the command line.

Usage:
    python3 new_post.py "文章标题" [slug]
"""

import datetime
import re
import sys
from pathlib import Path


def slugify(text: str) -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text.strip().lower()).strip("-")
    return slug or "post"


def main() -> None:
    title = sys.argv[1] if len(sys.argv) > 1 else "未命名文章"
    slug = sys.argv[2] if len(sys.argv) > 2 else slugify(title)
    date = datetime.date.today().isoformat()
    path = Path("posts") / f"{date}-{slug}.md"
    if path.exists():
        sys.exit(f"已存在：{path}")
    path.write_text(
        f"""---
title: {title}
date: {date}
tags: []
description: 一句话描述这篇文章。
---

正文从这里开始。
""",
        encoding="utf-8",
    )
    print(f"已创建：{path}")


if __name__ == "__main__":
    main()
