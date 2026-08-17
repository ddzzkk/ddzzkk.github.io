# ddzzkk.github.io

个人主页 + 博客，由 GitHub Pages 托管。使用一个零依赖的 Python 静态站点生成器：
博客文章写成 Markdown，跑一条命令就生成整个站点。

## 目录结构

```text
site.json          站点配置（昵称、简介、链接等）
posts/             博客文章（Markdown + front matter）
about.md           关于页内容
build.py           静态站点生成器
new_post.py        新建文章脚本
assets/style.css   全站样式
index.html 等      生成产物，构建后出现
```

## 写一篇博客

```shell
python3 new_post.py "文章标题"
```

这会生成 `posts/2026-08-17-文章标题.md`，打开后填写 front matter（标题、日期、标签、简介）和正文即可：

```markdown
---
title: 文章标题
date: 2026-08-17
tags: [随笔, 技术]
description: 一句话简介。
---

正文从这里开始。
```

然后重新生成站点并推送：

```shell
python3 build.py
git add -A
git commit -m "post: 文章标题"
git push
```

## 本地预览

```shell
python3 build.py
python3 -m http.server 8000
```

打开 <http://localhost:8000> 即可预览。

## 部署

仓库已包含 `.nojekyll`，直接使用静态文件。在 GitHub 仓库的
**Settings → Pages** 中选择 **Deploy from a branch**，分支选 `main`、目录选 `/ (root)` 即可。

启用后访问地址为 `https://ddzzkk.github.io/`。

## 修改站点信息

昵称、头像字母、简介、GitHub/邮箱等都在 `site.json` 里改，改完重新运行 `python3 build.py`。
