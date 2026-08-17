#!/usr/bin/env python3
"""Minimal static site generator for a personal homepage + blog.

Usage:
    python3 build.py

Reads site.json and posts/*.md (Markdown + front matter), then writes:
    index.html, posts.html, about.html, post/<slug>.html, feed.xml, 404.html
"""

from __future__ import annotations

import datetime
import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
POSTS_DIR = ROOT / "posts"
OUT_DIR = ROOT


# ---------------------------------------------------------------- markdown

def esc(text: str) -> str:
    return html.escape(text, quote=True)


def inline(text: str) -> str:
    """Render the inline subset of Markdown (after HTML escaping)."""
    text = esc(text)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img alt="\1" src="\2">', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*\s][^*]*)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"(?<!_)_([^_\s][^_]*)_(?!_)", r"<em>\1</em>", text)
    return text


def render_markdown(text: str) -> str:
    """Render a useful subset of Markdown: headings, lists, code, quotes, etc."""
    lines = text.splitlines()
    out: list[str] = []
    para: list[str] = []
    i = 0

    def flush_para() -> None:
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()

    while i < len(lines):
        line = lines[i]

        if not line.strip():
            flush_para()
            i += 1
            continue

        if line.lstrip().startswith("```"):
            flush_para()
            lang = line.strip()[3:].strip()
            code: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].lstrip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            cls = f' class="language-{esc(lang)}"' if lang else ""
            out.append(f"<pre><code{cls}>{esc(chr(10).join(code))}</code></pre>")
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            flush_para()
            level = len(heading.group(1))
            out.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
            i += 1
            continue

        if re.match(r"^(\s*[-*_]\s*){3,}$", line):
            flush_para()
            out.append("<hr>")
            i += 1
            continue

        if line.lstrip().startswith(">"):
            flush_para()
            quote: list[str] = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                quote.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote>" + render_markdown("\n".join(quote)) + "</blockquote>")
            continue

        if re.match(r"^\s*[-*+]\s+", line):
            flush_para()
            items: list[str] = []
            while i < len(lines) and re.match(r"^\s*[-*+]\s+", lines[i]):
                items.append(inline(re.sub(r"^\s*[-*+]\s+", "", lines[i])))
                i += 1
            out.append("<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>")
            continue

        if re.match(r"^\s*\d+\.\s+", line):
            flush_para()
            items = []
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i]):
                items.append(inline(re.sub(r"^\s*\d+\.\s+", "", lines[i])))
                i += 1
            out.append("<ol>" + "".join(f"<li>{item}</li>" for item in items) + "</ol>")
            continue

        para.append(line.strip())
        i += 1

    flush_para()
    return "\n".join(out)


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    """Parse a small YAML-like front matter block at the top of a file."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    meta: dict[str, str] = {}
    for line in text[3:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip().strip("\"'")
        if value.startswith("[") and value.endswith("]"):
            value = value[1:-1].strip()
        meta[key.strip()] = value
    return meta, text[end + 4:].lstrip("\n")


def split_tags(raw: str) -> list[str]:
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


# ---------------------------------------------------------------- data

def load_config() -> dict:
    return json.loads((ROOT / "site.json").read_text(encoding="utf-8"))


def load_posts() -> list[dict]:
    posts = []
    if not POSTS_DIR.is_dir():
        return posts
    for path in sorted(POSTS_DIR.glob("*.md")):
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
        if meta.get("draft", "").strip().lower() in ("true", "1", "yes"):
            continue
        posts.append(
            {
                "title": meta.get("title", path.stem),
                "date": meta.get("date", "1970-01-01"),
                "tags": split_tags(meta.get("tags", "")),
                "description": meta.get("description", ""),
                "slug": path.stem,
                "html": render_markdown(body),
            }
        )
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


# ---------------------------------------------------------------- pages

NAV_ITEMS = [
    ("index.html", "首页"),
    ("posts.html", "博客"),
    ("about.html", "关于"),
]


def base_page(site: dict, prefix: str, active: str, title: str, description: str, content: str) -> str:
    nav = []
    for href, label in NAV_ITEMS:
        cls = ' class="active"' if href == active else ""
        nav.append(f'<a href="{prefix}{href}"{cls}>{label}</a>')
    nav.append(
        f'<a class="github-link" href="{esc(site["github"])}" target="_blank" rel="noopener">GitHub</a>'
    )

    full_title = title if title == site["title"] else f"{title} · {site['title']}"
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(full_title)}</title>
  <meta name="description" content="{esc(description)}">
  <link rel="stylesheet" href="{prefix}assets/style.css">
  <link rel="alternate" type="application/rss+xml" title="{esc(site["title"])} RSS" href="{prefix}feed.xml">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📜</text></svg>">
</head>
<body>
  <div class="grid"></div>
  <div class="blob blob-1"></div>
  <div class="blob blob-2"></div>
  <div class="blob blob-3"></div>

  <header class="site-header">
    <a class="logo" href="{prefix}index.html">{esc(site["avatar"])}</a>
    <nav class="site-nav">{''.join(nav)}</nav>
  </header>

  <main class="container">
{content}
  </main>

  <footer class="site-footer">
    <span>{esc(site["footer"])} · 由 <code>build.py</code> 生成</span>
    <a href="{prefix}feed.xml">RSS</a>
  </footer>
</body>
</html>
"""


def hero(site: dict, prefix: str) -> str:
    return f"""<section class="card hero">
  <div class="avatar"><span class="ring"></span><span class="face">{esc(site["avatar"])}</span></div>
  <h1>{esc(site["author"])}</h1>
  <p class="tagline">{esc(site["tagline"])}</p>
  <p class="intro">{esc(site["bio"])}</p>
  <div class="hero-actions">
    <a class="btn primary" href="{prefix}posts.html">阅读博客</a>
    <a class="btn" href="{esc(site["github"])}" target="_blank" rel="noopener">GitHub</a>
    <a class="btn" href="mailto:{esc(site["email"])}">Email</a>
  </div>
</section>"""


def tags_html(tags: list[str]) -> str:
    if not tags:
        return ""
    return '<div class="tags">' + "".join(f'<span>{esc(t)}</span>' for t in tags) + "</div>"


def post_card(post: dict, prefix: str) -> str:
    return f"""<article class="post-card">
  <time datetime="{esc(post["date"])}">{esc(post["date"])}</time>
  <h3><a href="{prefix}post/{esc(post["slug"])}.html">{esc(post["title"])}</a></h3>
  <p class="post-desc">{esc(post["description"] or "（暂无简介）")}</p>
  {tags_html(post["tags"])}
</article>"""


def post_list(posts: list[dict], prefix: str, limit: int | None = None) -> str:
    shown = posts[:limit] if limit is not None else posts
    if not shown:
        return '<p class="empty">还没有文章，去 <code>posts/</code> 写一篇吧。</p>'
    return '<div class="post-list">' + "".join(post_card(p, prefix) for p in shown) + "</div>"


def build_index(site: dict, posts: list[dict]) -> str:
    prefix = ""
    recent = post_list(posts, prefix, limit=5)
    archive_link = f'<a class="more" href="{prefix}posts.html">全部文章 →</a>' if posts else ""
    body = f"""{hero(site, prefix)}
<section class="section">
  <div class="section-head">
    <h2>最近文章</h2>
    {archive_link}
  </div>
  {recent}
</section>"""
    return base_page(site, prefix, "index.html", site["title"], site["bio"], body)


def build_archive(site: dict, posts: list[dict]) -> str:
    prefix = ""
    body = f"""<section class="section">
  <div class="section-head"><h2>全部文章</h2></div>
  {post_list(posts, prefix)}
</section>"""
    return base_page(site, prefix, "posts.html", "博客", "博客文章列表", body)


def build_post(site: dict, post: dict) -> str:
    prefix = "../"
    body = f"""<article class="post">
  <header class="post-head">
    <h1>{esc(post["title"])}</h1>
    <div class="post-meta">
      <time datetime="{esc(post["date"])}">{esc(post["date"])}</time>
      {tags_html(post["tags"])}
    </div>
  </header>
  <div class="post-body">{post["html"]}</div>
  <nav class="post-back"><a href="{prefix}posts.html">← 返回博客</a></nav>
</article>"""
    return base_page(site, prefix, "", post["title"], post["description"], body)


def build_about(site: dict) -> str:
    text = (ROOT / "about.md").read_text(encoding="utf-8")
    _, body = parse_front_matter(text)
    content = f"""<section class="section card prose-card">
  {render_markdown(body)}
</section>"""
    return base_page(site, "", "about.html", "关于", "关于我", content)


def build_404(site: dict) -> str:
    body = """<section class="card hero">
  <div class="avatar"><span class="ring"></span><span class="face">404</span></div>
  <h1>页面走丢了</h1>
  <p class="intro">你访问的页面不存在，回到首页看看吧。</p>
  <div class="hero-actions"><a class="btn primary" href="index.html">返回首页</a></div>
</section>"""
    return base_page(site, "", "", "404", "页面不存在", body)


def build_feed(site: dict, posts: list[dict]) -> str:
    items = []
    for post in posts[:20]:
        items.append(
            f"""    <item>
      <title>{esc(post["title"])}</title>
      <link>{esc(site["base_url"])}/post/{esc(post["slug"])}.html</link>
      <guid>{esc(site["base_url"])}/post/{esc(post["slug"])}.html</guid>
      <pubDate>{rfc2822(post["date"])}</pubDate>
      <description>{esc(post["description"])}</description>
    </item>"""
        )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{esc(site["title"])}</title>
    <link>{esc(site["base_url"])}</link>
    <description>{esc(site["bio"])}</description>
    <language>zh-CN</language>
{chr(10).join(items)}
  </channel>
</rss>
"""


def rfc2822(date: str) -> str:
    try:
        dt = datetime.date.fromisoformat(date)
    except ValueError:
        dt = datetime.date(1970, 1, 1)
    return dt.strftime("%a, %d %b %Y 00:00:00 +0800")


# ---------------------------------------------------------------- main

def main() -> None:
    site = load_config()
    posts = load_posts()

    (OUT_DIR / "post").mkdir(exist_ok=True)

    (OUT_DIR / "index.html").write_text(build_index(site, posts), encoding="utf-8")
    (OUT_DIR / "posts.html").write_text(build_archive(site, posts), encoding="utf-8")
    (OUT_DIR / "about.html").write_text(build_about(site), encoding="utf-8")
    (OUT_DIR / "404.html").write_text(build_404(site), encoding="utf-8")
    (OUT_DIR / "feed.xml").write_text(build_feed(site, posts), encoding="utf-8")
    for post in posts:
        (OUT_DIR / "post" / f"{post['slug']}.html").write_text(
            build_post(site, post), encoding="utf-8"
        )

    print(f"OK: {len(posts)} post(s) → {len(posts) + 5} page(s) generated.")


if __name__ == "__main__":
    main()
