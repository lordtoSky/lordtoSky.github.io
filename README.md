# 博客运维手册 · lordtoSky.github.io

本站是一个以 PCIe / RTL / 体系结构为主线的个人技术博客，源码即站点：仓库推到 GitHub 后由 **GitHub Pages 自动构建发布**。

> 状态核查时间：**2026-11-27**（本文中的数字、链接、构建时间均以该次核查为准；配置或线上状态变化后请以实际为准，并更新本文件）

| 项目 | 值 |
|---|---|
| 线上地址 | <https://lordtosky.github.io/> |
| 仓库 | <https://github.com/lordtoSky/lordtoSky.github.io>（公开，默认分支 `main`） |
| 构建方式 | GitHub Pages「Deploy from a branch」→ `main` / 根目录，使用 Jekyll 3.9（safe mode）自动构建 |
| 主题 | [Soot Spirits](https://sootspirits.github.io)（Jekyll 主题 + Bulma CSS）+ 本地定制 |
| 站点标题 | `lordtoSky`（`_config.yml` 的 `title`），副标题 `PCIe · RTL · 体系结构 · 随笔` |
| 文章规模 | 工作区 25 个带日期前缀的文章文件；本次推送后线上 24 篇 |
| 首页分页 | 每页 5 篇（`_config.yml` 中 `paginate: 5`，24 篇约 5 页） |
| 评论 | 已关闭（`provider: false`）；要启用就在 `_config.yml` 填自己在 disqus.com 的 shortname |
| 搜索 | 页头搜索走 Google `site:lordtosky.github.io` |
| 统计 | 未接入任何统计代码 |
| 时区 | 构建机按 **UTC**；写作按北京时间（+0800） |
| 备份 | 以 Git 仓库为唯一真源（本地 `D:\onedrive\block` + GitHub 各一份） |

---

## ⚠️ 三条硬性规则（每次改动都适用）

1. **每次改动都必须追加变更记录** → 写入根目录的 [`CHANGELOG.MD`](CHANGELOG.MD)。新记录加在最上面，不删除历史记录。这是本仓库的强制约定，细则见第 10 节。
2. **文章文件名必须是 `YYYY-MM-DD-短标题.md`**，并且带完整 front matter（`layout` / `title` / `date`）。没有日期前缀的 `.md` 放进 `_posts/` 也不会被发布。
3. **不要手改、不要提交 `_site/`**。它是本地构建产物；线上页面由 GitHub Pages 重新构建，仓库里残留的旧 `_site` 只会在线上产生“幽灵页面”（见 6.3）。

---

## 目录

1. [30 秒速查](#1-30-秒速查)
2. [项目结构与文件地图](#2-项目结构与文件地图)
3. [文章：写作、预览、发布](#3-文章写作预览发布)
4. [上线：GitHub Pages 构建机制](#4-上线github-pages-构建机制)
5. [更新、回滚与发布检查清单](#5-更新回滚与发布检查清单)
6. [当前状态与已知问题（2026-11-27）](#6-当前状态与已知问题2026-11-27)
7. [站点经营指南](#7-站点经营指南)
8. [个性化配置速查](#8-个性化配置速查)
9. [故障排查](#9-故障排查)
10. [变更记录制度（必读）](#10-变更记录制度必读)
11. [交给 AI / 自动化代理维护时的约定](#11-交给-ai--自动化代理维护时的约定)
12. [主题来源、许可与致谢](#12-主题来源许可与致谢)

---

## 1. 30 秒速查

**写一篇新文章并上线：**

```text
1) 在 _posts/ 新建 2026-11-27-my-topic.md（front matter 见 3.2）
2) 本地预览（可选，需先装 Ruby）：运行 serve.bat → http://127.0.0.1:5555
3) 打开 CHANGELOG.MD，在最上面追加本次记录（必做）
4) git add -A
   git commit -m "post: my-topic"
   git push origin main
5) 等 1–3 分钟，验证 https://lordtosky.github.io/ 与 /archive/ 出现新文章
```

**只看命令：**

```powershell
cd D:\onedrive\block
git status
.\serve.bat                                  # 本地预览（需要 Ruby，见 3.4）
git add -A
git commit -m "docs: 更新说明与变更记录"
git push origin main
```

> 推送后如果线上没变化，先看第 9 节「发布后线上不更新」，不要反复空提交。

---

## 2. 项目结构与文件地图

```text
D:\onedrive\block\
├─ _posts\                 # 文章源文件（唯一内容入口；可含子目录）
│  ├─ 2026-11-02-xxx.md
│  └─ rtl优化\             # 子目录仅用于组织；无日期前缀 = 不会发布
├─ _drafts\                # 草稿目录（当前不存在）
├─ _layouts\               # default / page / post 三套布局
├─ _includes\              # head、分页、JB 系列辅助模板（tags/archive/评论等）
├─ _plugins\               # 本地 Jekyll 插件（GitHub Pages safe mode 下不加载）
├─ assets\                 # css / js / images / diagrams 静态资源
├─ index.html              # 首页（分页文章列表）
├─ archive.html            # 归档页 /archive
├─ tags.html               # 标签页 /tags
├─ 404.html                # 404 页
├─ atom.xml / rss.xml      # 订阅源（使用 production_url）
├─ sitemap.txt             # 纯文本站点地图（使用 production_url）
├─ quotes.txt              # 页头随机语录（前端 JS 拉取）
├─ _config.yml             # 站点配置（标题/域名/分页/评论/exclude）
├─ Gemfile / Gemfile.lock  # 本地依赖（Pages 构建不使用仓库的 Gemfile）
├─ serve.bat               # Windows 本地预览脚本
├─ Rakefile                # 主题遗留脚本（已被 exclude，不发布）
├─ tmp\                    # 主题截图等临时素材（已 exclude，不发布）
├─ _site\                  # 本地构建产物（已停止跟踪，见 6.3，勿改）
├─ CHANGELOG.MD            # ★ 变更记录，每次改动必须追加
├─ README.md               # 本手册（被 exclude，不发布）
└─ *.pptx / make_*.py      # 文章配套幻灯片与生成脚本（已 exclude，不发布）
```

| 路径 | 作用 | 是否出现在线上 |
|---|---|---|
| `_posts/**/*.md`（带日期前缀） | 文章 | ✅ 是 |
| `_posts/` 子目录中的无日期文件 | 不会被 Jekyll 读取 | ❌ 否 |
| `_layouts/` `_includes/` | 模板，生成 HTML | 仅产物 |
| `_plugins/` | 本地插件（`ruby_compat.rb`、`debug.rb`） | ❌ Pages 不加载 |
| `assets/` | 样式、脚本、图片、图表 | ✅ 是 |
| `index.html` `archive.html` `tags.html` `404.html` | 页面 | ✅ 是 |
| `atom.xml` `rss.xml` `sitemap.txt` | 订阅/地图 | ✅ 是 |
| `quotes.txt` | 语录数据 | ✅ 是 |
| `tmp/` | 主题截图 | ❌ 已 exclude |
| `Gemfile` `Gemfile.lock` `serve.bat` | 工程文件 | ❌ 已 exclude |
| `LICENSE` | 许可文件 | ✅ 是 |
| `_site/` | 构建产物 | ❌ 已停止跟踪并写入 `.gitignore`（见 6.3） |
| `README.md` `CHANGELOG.MD` | 本手册与变更记录 | ❌ 被 exclude |
| `Rakefile` | 主题脚本 | ❌ 被 exclude |
| `*.pptx` / `make_*.py` | 幻灯片与生成脚本 | ❌ 已 exclude |

**关键机制说明**

- **`_posts` 会递归读取**：`_posts/子目录/2026-11-14-xxx.md` 会被当作文章，但文件名仍必须带日期前缀。
- **没有日期前缀 = 完全不读取**：例如 `_posts/rtl优化/动态时钟axi配置.md` 目前不会成为文章。
- **带日期但没有 front matter 也会发布**：Jekyll 会用文件名推断标题/日期（例如线上的 `2026-08-28-PCIE-FM-Retransmission.md` 是空文件，仍生成了一个文章页）。这种“裸文章”无法设置 tags/description，不要这样写。
- **文件名决定 URL 的一部分**（`permalink: pretty`）：`/年/月/日/文件名去掉日期前缀/`。改文件名或改 `date` 都会改 URL，旧链接会 404。

---

## 3. 文章：写作、预览、发布

### 3.1 新建文章

1. 在 `_posts/` 下新建文件，命名格式：

   ```text
   YYYY-MM-DD-slug.md
   ```

   - `slug` 建议用英文/数字/连字符：`2026-11-27-pcie-retry-buffer-in-practice.md`
   - 中文文件名可用，但会变成 `%E4%B8%AD%E6%96%87` 形式的长 URL，不推荐；标题中文放在 `title` 里即可。
   - 避免空格、`&`、`#`、`%` 等特殊字符（仓库里已有 `2026-08-04-PCIE-LCRC&ECRC.md`，虽然能用，但后续引用容易出错）。

2. 复制下面的模板：

   ```markdown
   ---
   layout: post
   title: "文章标题（中文即可）"
   date: 2026-11-27 10:00:00 +0800
   description: "一句话摘要，便于日后检索（当前模板不渲染）"
   tags: [PCIe, RTL, SystemVerilog]
   ---

   正文从二级标题开始：

   ## 背景

   ……
   ```

3. 需要公式时在 front matter 加 `math: true`，页面会加载 MathJax（`_includes/head.html:30`）。

### 3.2 front matter 字段

| 字段 | 是否必填 | 说明 |
|---|---|---|
| `layout` | 必填 | 固定 `post` |
| `title` | 必填 | 文章标题；缺省时 Jekyll 用文件名自动生成（效果差） |
| `date` | 强烈建议 | 推荐 `2026-11-27 10:00:00 +0800` 或只写 `2026-11-27`；**不要写未来时间**（见 6.1） |
| `description` | 可选 | 当前 post 模板未输出，仅供存档/后续 SEO |
| `tags` | 建议 | `[PCIe, DLL, Retry]`，决定 `/tags` 页的聚合 |
| `math` | 可选 | `true` 时加载 MathJax |
| `categories` | 可选 | 会进入 URL 占位符，一般不用 |
| `permalink` | 可选 | 单篇覆盖 URL，慎用 |

### 3.3 正文规范

| 事项 | 约定 |
|---|---|
| 图片 | 放在 `assets/images/<主题>/`，正文用绝对路径 `/assets/images/PCIE/xxx.png` |
| 代码 | 用围栏代码块并标语言（`text` / `systemverilog` / `bash` / `python`），由 rouge 高亮 |
| 表格 | 正常 Markdown 表格即可，样式已有表格边框（见提交 `37a90ff`） |
| 标题 | 从 `##` 开始；同一页不要重复同名标题（历史 bug：`29167e8` 修过重复标题） |
| 链接 | 站内用 `/archive/` 这类绝对路径；站外用完整 URL |
| 长度 | 长文（3000 字以上）建议加目录/分节；面试题类单独成文（参考 `2026-08-26-PCIE-Non-Flit-Mode-Replay-Interview-Questions.md`） |

### 3.4 本地预览

**当前机器状态（2026-11-27 核查）**：`serve.bat` 期望的 Ruby 位于 `D:\exe_file\Ruby40-x64\bin`，该目录**不存在**；`PATH` 中没有 `ruby` / `bundle`；Docker Desktop 未启动。所以现在**无法直接本地预览**，需要先补环境（三选一）。

**方案 A：安装 Ruby（推荐，和 `serve.bat` 一致）**

1. 安装 RubyInstaller（含 MSYS2/DevKit），例如 Ruby 3.3.x；官方页：<https://rubyinstaller.org/downloads/>。
2. 打开新的 PowerShell：

   ```powershell
   cd D:\onedrive\block
   ruby -v
   bundle -v
   bundle install
   bundle exec jekyll serve -P 5555 --watch
   ```

3. 浏览器打开 <http://127.0.0.1:5555>。改文件会自动重建。
4. 若把 Ruby 装在别处，修改 `serve.bat:6` 的 `RUBY_BIN`，之后双击 `serve.bat` 即可。

> `Gemfile` 第 3 行 `require_relative "_plugins/ruby_compat"` 是给新版 Ruby 打补丁（Liquid 4 仍调用已移除的 taint API），**不要删除** `_plugins/ruby_compat.rb`。

**方案 B：Docker（本机需先启动 Docker Desktop）**

```powershell
cd D:\onedrive\block
docker run --rm -v "${PWD}:/srv/jekyll" -p 5555:4000 -w /srv/jekyll jekyll/jekyll:3.9 `
  jekyll serve --host 0.0.0.0 --watch
```

（镜像 tag 若拉取失败，改用 `jekyll/jekyll:latest`，注意其 Jekyll 版本与 Pages 的 3.9 有差异。）

**方案 C：不预览，直接推**

风险是构建失败或样式异常。至少先自查：文件名有日期前缀、front matter 是否闭合、UTF-8 无 BOM、正文没有写坏 Liquid 语法（`{{` / `{%`）。推送后按第 4 节验证。

> 注意：`jekyll serve` / `jekyll build` 会往仓库的 `_site/` 写文件。由于 `_site` 已被误提交（见 6.3），每次构建都会让 `git status` 变脏，提交时务必排除。

### 3.5 发布

```powershell
cd D:\onedrive\block
git status                     # 先确认改了什么
git add -A
git commit -m "post: 文章标题 / fix: 修复点"
git push origin main
```

- 分支必须是 `main`（Pages 的构建源）。
- 推送即触发 Pages 构建，不需要手动上传。
- 中文文件名提交没问题（Git 支持）；引用含 `&` 的路径时加引号。

### 3.6 修改 / 删除已有文章

| 操作 | 影响 | 注意 |
|---|---|---|
| 只改正文 | URL 不变 | 最安全；改了事实性内容要追加 CHANGELOG |
| 改 `title` | URL 不变（URL 由文件名+date 决定） | 归档页/RSS 标题会变 |
| 改 `date` | **URL 会变**，旧链接 404 | 尽量不改；确需改则同时考虑旧链接 |
| 改文件名 | **URL 会变** | 同上 |
| 删除文章 | 旧 URL 404 | Jekyll 无内置重定向插件（Pages 又不加载自定义插件），建议保留旧文件并加一句“本文已迁移”，或接受 404 |

---

## 4. 上线：GitHub Pages 构建机制

### 4.1 当前配置

- 仓库 **Settings → Pages → Build and deployment**
  - Source：**Deploy from a branch**
  - Branch：`main` / `(root)`
  - 无 `CNAME` 文件 → 使用 GitHub 默认域名 <https://lordtosky.github.io/>（已启用 HTTPS）
- 无 `.nojekyll` → 构建时启用 Jekyll 处理
- 无 `.github/workflows/` → 没有自定义 Actions 部署流程

> 若某天要接自定义插件（例如 `jekyll-redirect-from`、`jekyll-archives`），必须改为 GitHub Actions 部署，Pages 的 legacy 构建是 safe mode，只用白名单插件。

### 4.2 一次 `git push` 之后会发生什么

```text
push 到 main
  → GitHub 触发 "pages build and deployment" 工作流
  → 检出 main、用内置 Jekyll 3.9（github-pages gem）执行 jekyll build
  → 上传产物并切换线上版本
  → 1–3 分钟后生效（CDN 可能有额外缓存）
```

- 构建状态查看：仓库 **Actions** 页 → `pages build and deployment`；或 **Deployments** 页 → `github-pages`。
- 构建失败会发邮件给仓库 owner，线上会**继续保留上一次成功的版本**（不会变成 404）。

### 4.3 构建时间与「未来日期」

- 构建机时间是 **UTC**。front matter 里不带时区的 `date: "2026-11-05 16:00:00"` 会被当作 UTC 16:00。
- Jekyll 默认 `future: false`：构建时刻早于文章时间 → **该文章被跳过**，但构建本身成功。
- 因为 Pages 只在 push 时构建，被跳过的文章会一直不出现，直到下一次 push。

**写法建议：**

```yaml
date: 2026-11-27                 # 最简单，只写日期
date: 2026-11-27 10:00:00 +0800  # 或显式写明时区
```

不要写“今天晚些时候”这样的时间；当天上午推送会把文章判成未来时间。

### 4.4 手动触发重建

| 方法 | 操作 |
|---|---|
| 空提交（最简单） | `git commit --allow-empty -m "chore: rebuild" && git push` |
| 重跑工作流 | 仓库 Actions → 选中上一次 `pages build and deployment` → Re-run jobs |
| 改仓库设置 | Settings → Pages 里切换分支再切回，会触发构建（不推荐频繁操作） |

### 4.5 自定义域名（可选）

1. 在仓库根目录新增 `CNAME` 文件，内容为域名（如 `blog.example.com`）。
2. DNS 配置：`CNAME` 记录指向 `lordtosky.github.io`；裸域名用 A 记录指向 GitHub Pages IP。
3. Settings → Pages → 填写 Custom domain → 勾选 **Enforce HTTPS**。
4. 同步修改 `_config.yml` 的 `production_url`，让 `sitemap.txt` / `atom.xml` 使用新域名。
5. 追加一条 `CHANGELOG.MD` 记录。

### 4.6 Pages 的限制（知道这些能少踩坑）

- **safe mode**：不执行 `_plugins/`；仓库 `Gemfile` 也不会被用于构建，Pages 用自带的 `github-pages` 版本。
- 只支持 whitelist 插件；分页能用是因为 `github-pages` 自带 `jekyll-paginate`。
- 单次构建有时长/仓库大小限制；大体积 PPTX/图片尽量压缩（目前仓库里已有 13 MB 的 PPTX）。
- 没有服务端逻辑、不能跑脚本；评论/统计/搜索都靠前端第三方 JS。

---

## 5. 更新、回滚与发布检查清单

### 5.1 常规更新命令

```powershell
cd D:\onedrive\block
git pull --rebase origin main        # 先同步（多设备写作时尤其重要）
# …编辑文件…
git status
git add -A
git commit -m "feat: 新增 AXI 握手笔记；更新 CHANGELOG"
git push origin main
```

### 5.2 回滚

```powershell
git log --oneline -10                 # 找到要撤销的提交
git revert <commit>                   # 生成一个反向提交，保留历史（推荐）
git push origin main
```

不要对已发布的 `main` 做 `push --force`（除非明确知道后果）。

### 5.3 发布检查清单（每次推送前过一遍）

- [ ] 新文章文件名有 `YYYY-MM-DD-` 前缀
- [ ] front matter 以 `---` 开始/结束，`layout: post`、`title`、`date` 齐全
- [ ] `date` 不是未来时间（必要时加 `+0800`）
- [ ] 图片路径存在，`/assets/images/...` 拼写正确
- [ ] 文中没有误写的 `{{` / `{%`（会被 Liquid 解析）
- [ ] 文件是 UTF-8（无 BOM），中文不乱码
- [ ] **`CHANGELOG.MD` 已追加本次记录**
- [ ] `git status` 里没有 `_site/` 新产物
- [ ] 推送后打开线上页面、`/archive/`、`/atom.xml` 各确认一次

---

## 6. 当前状态与已知问题（2026-11-27）

### 6.1 为什么线上的最新文章停在 2026-11-02？

| 事实 | 依据 |
|---|---|
| 线上归档里日期最新的文章是 2026-11-02 的 HDMI 日志 | <https://lordtosky.github.io/archive/> |
| 2026-11-05 的《RTL 状态机重构》在仓库中存在，但线上 404 | 该文 `date: "2026-11-05 16:00:00"` |
| 11-05 的两次 Pages 构建都成功（UTC 07:54、08:49） | GitHub Actions / Deployments 记录 |
| 构建时刻（UTC 08:49）早于文章时间（UTC 16:00） | Jekyll `future: false` → 文章被跳过 |
| 之后没有新的 push，所以没有新的构建 | 线上一直缺这篇 |
| 同样地，日期为 11-02 11:00 的 HDMI 日志也是到 11-05 那次构建才补发的 | 11-02 的构建发生在 UTC 03:17，当时它同样是“未来文章” |

**结论**：不是构建失败，也不是文件丢失，而是“未来日期 + 没有后续构建”。**处理**：本次推送（2026-11-27）会触发新构建，该日期已过去，文章会自动补发，不需要改文件；以后写作时别把 `date` 写成当天晚些的时间即可（要显式写时用 `2026-11-27 10:00:00 +0800`）。

### 6.2 工作区状态（2026-11-27）

| 状态 | 文件 | 说明 |
|---|---|---|
| 已推送 | `561135f` `20a120f` `3377514` | 修改 HDMI 日志；新增 AXI 握手/动态时钟笔记 |
| 仍为本地修改 | `_posts/rtl优化/动态时钟axi配置.md` | 内容改动（该文件无日期前缀，本就不会发布） |
| 仍未跟踪 | `_posts/体系结构/2026-11-16-体系结构基础知识.md` | 有日期前缀但无 front matter；提交前请补 front matter |

### 6.3 `_site/` 误提交（已修正）

`_site/` 曾是 2026-08-23 的旧构建产物却留在 Git 里（59 个文件）。线上实测发现旧文件会被一起发布，例如：

- `/CHANGELOG/` 能打开，但源仓库里并没有这个页面（只有 `CHANGELOG.MD` 原文）——来自 `_site/CHANGELOG/index.html`；
- `/assets/css/style.css` 能访问，但 `assets/css/` 下没有这个文件——来自旧 `_site`。

**2026-11-27 已处理**：`git rm -r --cached _site` 停止跟踪，并在 `.gitignore` 里加入 `_site/` 与 Jekyll 缓存目录。推送后实测：`/CHANGELOG/`、`/2018/04/29/…`、`/Gemfile`、`/serve.bat`、`/tmp/*` 等旧产物均已 404；**但 `/assets/css/style.css` 仍然 200**——每次部署都会以新的修改时间重新出现，模板里没有任何引用，配置里也已 `exclude`，推测是 GitHub Pages 对 `assets/` 旧资源的保留策略。该文件已从 `sitemap.txt` 过滤，留在线上不影响页面，可忽略。本地 `_site/` 目录仍保留，方便查看旧产物，只是不再进入仓库。

### 6.4 主题作者默认值（2026-11-27 已修正）

| 位置 | 原值 | 现改为 |
|---|---|---|
| `_config.yml` `production_url` | `https://www.nagekar.com` | `https://lordtosky.github.io` |
| `assets/js/custom.js` 搜索 | `site:nagekar.com` | `site:lordtosky.github.io` |
| `_config.yml` 评论 `short_name` | `nagekar` | 评论已关闭（`provider: false`） |
| `_config.yml` `title` / `tagline` / `author` | Soot Spirits / 主题 tagline / Abhishek Nagekar | `lordtoSky` / `PCIe · RTL · 体系结构 · 随笔` / `lordtoSky` |
| `_layouts/default.html` 导航与页脚 | `github.com/abhn`、abhn 的 LinkedIn / 邮箱 | `github.com/lordtoSky`、`1979968187@qq.com`（LinkedIn 已移除） |
| `index.html` | 硬编码 `disqus_shortname = 'nagekar'` 的评论计数 | 已删除 |
| `404.html` | 没有固定 `permalink`，`permalink: pretty` 使其产出 `/404/`，GitHub Pages 找不到自定义 404 | 增加 `permalink: /404.html` |
| `sitemap.txt` | 会把 `atom.xml`、`rss.xml`、`sitemap.txt` 本身等非 HTML 页面写进站点地图 | 过滤 `.xml` / `.txt` / `.css`，只留页面与文章 |
| `404.html` | 指向主题作者 Google CSE 的搜索链接 | 改为本站 Google `site:` 搜索 |
| `_includes/head.html` | 无 description / canonical / OG，RSS 链接重复 | 已补 description、canonical、Open Graph，去重 |
| `_config.yml` `paginate` | `1`（每页 1 篇） | `5` |

**副作用提醒**：`paginate` 从 1 改成 5 后，原来的 `/blog/page2/` … `/blog/page23/` 会被重新编号，旧的深链接可能 404。

**仍需你决定**：站点正式名称/副标题是否就用 `lordtoSky`；是否启用评论（需要自己在 disqus.com 注册并填 shortname）。

### 6.5 仍待处理的问题

| # | 问题 | 位置 | 建议 |
|---|---|---|---|
| 1 | 空文章页面 | `_posts/2026-08-28-PCIE-FM-Retransmission.md`（0 字节） | 补内容或删除（删除前确认没有外链引用） |
| 2 | 4 个文章文件没有 front matter（靠文件名推断标题） | `2026-08-15-DLL概述.md`、`2026-08-15-DLL概述-LAPTOP-TENF55MD.md`、`2026-08-28-PCIE-FM-Retransmission.md`、`体系结构/2026-11-16-体系结构基础知识.md` | 补齐 front matter（至少 `layout` / `title` / `date` / `tags`） |
| 3 | 3 个 `.md` 无日期前缀，永远不会发布 | `_posts/rtl优化/*.md`、`_posts/axi2chi_orderbuffer/设计思路.md` | 要发布就重命名为 `YYYY-MM-DD-xxx.md` 并加 front matter；否则移入 `_drafts/` |
| 4 | 同题双份文件 | `2026-08-15-DLL概述.md` 与 `2026-08-15-DLL概述-LAPTOP-TENF55MD.md` | 保留主版本，另一份合并或加 `published: false` 隐藏 |
| 5 | 仓库体积偏大 | `_posts/PCIe_7.0_NFM_…_v3.pptx`（13 MB）、`assets/diagrams/*.html`（单文件上万行） | 大文件可移到外部网盘/对象存储，正文给链接 |
| 6 | 没有统计 | `_includes/head.html` | 可选接入 Plausible/Umami（轻量）或 GA4 |
| 7 | 修改分页参数后的旧链接 | `/blog/page2/` … `/blog/page23/` 会重新编号 | 若有外部引用，考虑接受 404 或自行加跳转说明 |

### 6.6 修复状态与后续优先级

**2026-11-27 已完成**：域名、搜索、评论归属、页脚/导航、站点标题、`exclude` 收口、首页分页、`_site` 停止跟踪、SEO meta、自定义 404、sitemap 过滤，并已推送上线。

**推送后线上验证**：Pages 构建成功；`/archive/` 出现 2026-11-05 文章；首页每页 5 篇（Page 1 of 5）；`/sitemap.txt` 共 32 条（8 个页面 + 24 篇文章）且域名均为 `https://lordtosky.github.io`；文章页无 Disqus 脚本；`/CHANGELOG/`、`/Gemfile`、`/tmp/*` 等已 404。

后续：

1. **P1**：补齐空文章与 4 个缺 front matter 的文件（见 6.5 #1、#2）；
2. **P1**：处理 3 个无日期草稿与同题双份文件（见 6.5 #3、#4）；
3. **P2**：接入统计（见 6.5 #6）；
4. **P2**：决定是否启用评论、是否使用自定义域名；
5. **P2**：压缩 / 外链大体积 PPTX 与 diagram HTML（见 6.5 #5）。

---

## 7. 站点经营指南

### 7.1 内容定位（基于现有系列文章）

当前内容已经形成四条主线，建议继续按主线积累，而不是零散发文：

| 主线 | 现有代表文章 | 选题建议 |
|---|---|---|
| **PCIe 协议栈** | TLP 格式、LCRC/ECRC、CRC、DLL 概述、DLLP 接收、Replay/重传、Retry Buffer、Flit/Non-Flit 对比 | 按“层次 + 方向”补齐：物理层/链路训练、AER、SR-IOV、Switch、时序分析、误码注入调试 |
| **RTL 设计与综合** | FSM 重构与寄存器所有权、HDL Compiler 复查、AXI 握手 | 综合 QoR、CDC、低功耗、时序收敛、lint 规则、断言与覆盖率 |
| **体系结构 / 存储** | HyperLogLog、LRU（Age Matrix）、DMA | Cache 一致性、NoC、内存模型、性能建模 |
| **项目日志 / 随笔** | HDMI DDC/EDID 项目日志、AXI2CHI 设计权衡、Exile、Echo Archive | 项目复盘固定模板：目标 → 约束 → 方案对比 → 实施 → 结果；随笔可保留个人风格 |

### 7.2 标签体系

- 每个标签页会自动聚合（`tags.html` + `_includes/JB/tags_list`），所以**标签要收敛**，不要每次发明新词。
- 建议固定一组（10–15 个）：`PCIe`、`TLP`、`DLL`、`Retry`、`AXI`、`CHI`、`RTL`、`SystemVerilog`、`FPGA`、`综合`、`体系结构`、`验证`、`面试`、`项目日志`、`随笔`。
- 每篇 3–6 个；大小写统一（现在 `SystemVerilog` / `Coding-Style` 这类写法可以沿用）。

### 7.3 节奏与选题方法

- **节奏**：每周或每两周 1 篇，比“攒大招”更利于搜索与读者回访；系列文按固定编号（如 “PCIe 重传（1/3）”）。
- **选题来源**：项目日志里踩过的坑 → 抽象成原理文；面试题 → 形成问答文；读书/规范笔记 → 对照表 + 图。
- **一稿多用**：长文可拆“原理篇 + 实战篇 + 面试题”；PPTX 讲稿可在文末给下载链接（注意仓库体积）。
- **旧文维护**：协议版本更新时在原文章补“2026-xx 更新”小节，并在 `CHANGELOG.MD` 记录；比新开一篇更有沉淀。

### 7.4 排版与质量

- 开头 3–5 行给结论/摘要，长文给目录；
- 图优先于大段文字：时序图、状态机图、表格对比；
- 代码块注明语言与关键行注释；
- 结尾固定给“参考规范章节 / 相关文章 / 待办问题”；
- 发布前通读一遍：错别字、单位、信号名大小写（协议文尤其重要）。

### 7.5 SEO 与分发

| 项 | 现状 | 建议 |
|---|---|---|
| `production_url` | 已改为本站域名 | 换域名时同步修改 |
| `sitemap.txt` | 随构建生成 | 可提交到 Google/Bing 站长平台 |
| `atom.xml` / `rss.xml` | 正常生成 | 可接到 Feedly/邮件订阅服务 |
| `<title>` | 已改为 `lordtoSky` + 页面标题 | 想换站名改 `_config.yml` 的 `title` |
| meta description / OG | 已补 description / canonical / `og:*` | 新页面记得写 `description` |
| 搜索 | Google `site:lordtosky.github.io` | 或接站内搜索（如 Pagefind/Algolia） |
| 分享按钮 | `JB.sharing.provider: false` | 需要就开，不需要保持关闭（省加载） |
| 结构化数据 | 无 | 技术文可加 Article/FAQ JSON-LD（可选） |

### 7.6 互动与数据

- **评论**：当前已关闭（`provider: false`）。启用 Disqus 需要自己的 shortname；或换 Giscus（基于 GitHub Discussions，更贴合技术博客；需要在 `_layouts/post.html` 替换 include）。
- **统计**：无。轻量方案：Plausible、Umami、Cloudflare Web Analytics；不建议塞多个。
- **反馈渠道**：文章末尾可留“问题/纠错”入口（GitHub Issue 链接或邮箱）。
- **友情链接**：`_layouts/default.html:121–145` “Recommended Websites” 可换成自己的友链。

### 7.7 备份与安全

- 真源是 Git：本地 `D:\onedrive\block`（OneDrive 再同步一份）+ GitHub 远程。
- 定期：`git fetch && git status` 确认没有长期未推送的提交；换电脑前先 push。
- 图片/PPTX 大文件避免无限增长；敏感信息（内网地址、客户名、未公开参数）不要进仓库——仓库是公开的。
- 仓库公开意味着 `README`、提交历史、`_site` 都可被搜索，清理前先想清楚。

---

## 8. 个性化配置速查

| 想改什么 | 改哪里 | 备注 |
|---|---|---|
| 站点标题 / 副标题 / 作者 | `_config.yml:27–32` | 影响 `<title>`、RSS、归档页 |
| 站点域名 | `_config.yml:42` `production_url` | 影响 sitemap、feed |
| 每页文章数 | `_config.yml:4` `paginate` | 改后分页页数变化 |
| 不发布的文件 | `_config.yml:7–21` `exclude` | 大小写敏感，按实际文件名写 |
| 评论开关/服务 | `_config.yml:96–101` | `provider: false` 关闭 |
| 页头打字机文案 | `_layouts/default.html:12` `data-type` 数组 | 中文可用，注意 JSON 双引号转义 |
| 页头随机语录 | `quotes.txt`（每行一句） | `assets/js/custom.js:16` 通过 XHR 拉取 |
| 导航图标链接 | `_layouts/default.html:36` | 换成自己的 GitHub |
| 侧栏 Recent Posts | `_layouts/default.html:83–98` | 显示最近 3 篇 |
| 侧栏 Sponsored 图片 | `_layouts/default.html:110` + `assets/images/Dust_Bunny.jpg` | 不需要可删整块 |
| 侧栏 Recommended Websites | `_layouts/default.html:121–149` | 友链 |
| 页脚社交/版权 | `_layouts/default.html:160–177` | 换成自己的 |
| 站点样式 | `assets/css/custom.css` | 主样式；`syntax.css` 管代码高亮 |
| 搜索行为 | `assets/js/custom.js:35–40` | 当前是 Google `site:` 搜索 |
| 404 页 | `404.html` | 图 `assets/images/404_minions.jpg` |
| 归档页/标签页 | `archive.html` / `tags.html` | 一般不需要动 |
| 公式支持 | `_includes/head.html:37` | front matter `math: true` 生效 |

---

## 9. 故障排查

| 症状 | 常见原因 | 处理 |
|---|---|---|
| 推送后线上完全不更新 | ① 没推到 `main`；② 构建失败；③ CDN 缓存 | `git log origin/main..HEAD` 看是否已推送；Actions/Deployments 看构建；强刷（Ctrl+F5）或换网络 |
| 构建成功但新文章没有 | 文章日期在构建时刻之后（UTC，`future: false`） | 改成过去的日期/加 `+0800`，再 push 触发构建 |
| 新文章 404 | 文件名没有 `YYYY-MM-DD-` 前缀；文件在 `_posts` 之外；文件名大小写与链接不一致 | 重命名到 `_posts/` 根或带日期前缀的子目录 |
| 页面能开但没样式/标题怪 | 缺 front matter → 用文件名当标题；`layout` 写错 | 补 front matter，`layout: post` |
| 图片不显示 | 路径写错；误用相对路径；文件在 `tmp/` | 统一 `/assets/images/...` 绝对路径 |
| 首页每页文章数不对 | `paginate` 设置 | 改 `_config.yml:4` 的 `paginate`（当前 5） |
| 评论跑到别人站点 | Disqus shortname 曾是 `nagekar`（现已关闭评论） | 启用前先在 disqus.com 注册并填自己的 shortname |
| 站内搜索跳到错误站点 | `custom.js` 的 `site:` 域名 | 改为 `site:lordtosky.github.io` |
| 中文乱码 | 文件不是 UTF-8（或带 BOM） | 用 UTF-8 无 BOM 保存；不要用 GBK 另存 |
| 构建失败（YAML/Liquid） | front matter 引号/冒号问题；正文出现 `{{` `{%` | 看构建日志里的文件名与行号；给标题加引号；代码里的 `{{` 用 `{% raw %}` 包裹 |
| `_site` 一直变脏 | 本地构建写入 | 提交时排除；按 6.3 清理跟踪 |
| `git push` 被拒 | 远程有新提交 | `git pull --rebase origin main` 后再 push |

**本地快速自检（无 Ruby 也能做）：**

```powershell
# 检查文章是否都有日期前缀
Get-ChildItem _posts -Recurse -Include *.md | Where-Object { $_.Name -notmatch '^\d{4}-\d{1,2}-\d{1,2}-' }

# 检查 front matter 是否闭合（第一行应为 ---）
Get-ChildItem _posts -Recurse -Include *.md | ForEach-Object {
  if ((Get-Content $_.FullName -TotalCount 1) -ne '---') { $_.FullName }
}

# 检查 future 日期（把 date 大于今天的列出来）
Get-ChildItem _posts -Recurse -Include *.md |
  Select-String -Pattern '^date:\s*"?(\d{4}-\d{2}-\d{2})' |
  Where-Object { $_.Matches[0].Groups[1].Value -gt (Get-Date -Format 'yyyy-MM-dd') } |
  ForEach-Object { "$($_.Filename): $($_.Line)" }
```

---

## 10. 变更记录制度（必读）

**规则：本仓库的每一次改动，都必须在 [`CHANGELOG.MD`](CHANGELOG.MD) 追加一条记录。** 包括但不限于：

- 新增 / 修改 / 删除文章；
- 改 `_config.yml`、布局、样式、脚本；
- 改图片、PPTX、素材；
- 改构建配置、部署方式、域名；
- 修复线上问题、回滚。

**写法：**

1. 新记录加在 **最上面**（按日期倒序），历史记录只增不删；
2. 每条至少写清：**日期、类型、做了什么、涉及文件、如何验证**；
3. 日期用北京时间 `YYYY-MM-DD`；一次改动可以对应多个提交，可写 commit 短 hash 便于追溯；
4. 如果之前的记录写错了，**追加一条更正**，不要直接抹掉；
5. 提交前最后一步永远是：检查 `CHANGELOG.MD` 有没有加。

**模板：**

```markdown
## 2026-11-27 · 类型（新增文章 / 修改内容 / 样式 / 配置 / 修复 / 文档）

- 内容：一句话说明这次改了什么、为什么改。
- 文件：`README.md`、`CHANGELOG.MD`
- 验证：如何确认改动生效（本地预览 / 线上页面 / 构建日志）。
- 提交：`abc1234`（可选）
```

**为什么必须做**：本站没有后台数据库，文章和配置都在 Git 里；README 负责“怎么做”，CHANGELOG 负责“做过什么、为什么”。两者一起才能在几个月后快速回答“这篇什么时候改的、为什么改、上线了吗”。

---

## 11. 交给 AI / 自动化代理维护时的约定

如果让 AI（Codex / DSH 等）或脚本代改本站，遵守下面几条可以避免事故：

1. **只改任务要求的文件**；不确定时先读，不要批量重写。
2. **每次改动都追加 `CHANGELOG.MD`**（见第 10 节），这是硬性要求。
3. **不要碰 `_site/`**；不要让本地构建产物进入提交。
4. **不要改文件名 / `date`**（会改 URL）；确需改时在 CHANGELOG 记录旧链接。
5. **保持 UTF-8 无 BOM**；中文内容不要用 GBK 写入。
6. **不要引入新插件/新依赖**：Pages 是 safe mode，白名单外的插件不会生效。
7. **推送前必须做第 5.3 节检查清单**；`git status` 里不能有意外文件。
8. **推送是发布动作**：如果任务只说“改文档/看看”，不要自动 `git push`。
9. **线上验证**：改完后至少访问一次受影响页面（文章 URL、`/archive/`、`/atom.xml`）。
10. 大文件（PPTX、GIF）不要反复重传；能外链就外链。

---

## 12. 主题来源、许可与致谢

本站基于 [Soot Spirits](https://sootspirits.github.io) Jekyll 主题（作者 Abhishek Nagekar），本地做了中文化、排版加宽、表格边框、侧栏收窄、页头打字机文案等定制。主题特性：

- 响应式双栏布局（Bulma CSS），移动端可用；
- 注重排版的字体组合（League Gothic / Roboto / Open Sans）；
- 可自定义页头文案、随机语录、导航、侧栏小部件。

**致谢**

- 页头打字机效果来自 CodePen [hi-im-si](http://codepen.io/hi-im-si/pen/DHoup)
- [Bulma CSS](https://bulma.io/) / [Jekyll](https://jekyllrb.com) / [GitHub Pages](https://pages.github.com)
- 主题原始变更记录见 `CHANGELOG.MD` 末尾“主题自带初始变更”

**许可**：MIT（见 [`LICENSE`](LICENSE)）。

---

<sub>本手册由 2026-11-27 的仓库与线上核查整理；修改本文件同样需要追加 `CHANGELOG.MD`。</sub>
