---
title: 你好，世界
date: 2026-08-17
tags: [随笔, 开站]
description: 新博客的第一篇文章，介绍一下这个站是怎么运行的。
---

欢迎来到我的小站！这是我的第一篇文章。

## 这个站是怎么写的

博客文章以 Markdown 的形式放在 `posts/` 目录里，运行：

```bash
python3 build.py
```

就会生成整个静态站点，然后直接推送到 GitHub Pages 即可。

## 支持的内容

- **标题**、*斜体*、`行内代码`、[链接](https://github.com/ddzzkk)
- 有序列表和无序列表
- 代码块、引用、分隔线
- 图片

> 简单、可控，没有框架依赖。

## 写文章

```bash
python3 new_post.py "文章标题"
```

然后编辑生成的 Markdown 文件，重新 build 并推送就可以了。
