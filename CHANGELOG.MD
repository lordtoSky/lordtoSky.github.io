# 变更记录（CHANGELOG）

本文件记录本站（<https://lordtosky.github.io/>，仓库 `lordtoSky/lordtoSky.github.io`）的每一次改动。

> **强制约定：每次更新都必须在这里追加一条记录。**
> 新增/修改文章、改配置、改样式脚本、改图片素材、改部署方式、修复线上问题、回滚——全部算“更新”。
> 漏记 = 本次改动未完成。

## 记录规则

1. **新记录加在最上面**（按日期倒序），历史记录只增不删。
2. 日期用北京时间 `YYYY-MM-DD`。
3. 每条至少写清：**日期 / 类型 / 做了什么 / 涉及文件 / 如何验证**。
4. 一条记录可以对应多个提交；建议附 commit 短 hash 方便追溯。
5. 旧记录写错了，**追加一条更正**，不要直接抹掉。
6. 提交前的最后一件事：确认本文件已追加。

**模板：**

```markdown
## 2026-11-27 · 类型（新增文章 / 修改内容 / 样式 / 配置 / 修复 / 文档）

- 内容：这次改了什么、为什么改。
- 文件：涉及哪些文件。
- 验证：本地预览 / 线上页面 / 构建日志的确认方式。
- 提交：commit 短 hash（可选）。
```

---

## 2026-11-27 · 修复自定义 404 与上线验证

- 内容：`404.html` 增加 `permalink: /404.html`。此前 `permalink: pretty` 把它输出成 `/404/`，GitHub Pages 找不到根目录的 `404.html`，线上缺失页面显示的是 GitHub 默认 404，而不是本站自定义页。
- 内容：线上验证 2026-11-27 两次推送（`0ce74e3`、`3bcc6b0`）均构建成功：`/archive/` 已出现 2026-11-05《RTL 状态机重构》；首页每页 5 篇（Page 1 of 5）；站点标题/作者/导航/页脚/搜索域名已切换为本站；文章页无 Disqus 脚本；`/CHANGELOG/`、`/CHANGELOG.MD`、`/Gemfile`、`/serve.bat`、`/tmp/*`、`/2018/04/29/…` 均 404；`sitemap.txt` 过滤后共 32 条（8 页面 + 24 文章），域名全部为 `https://lordtosky.github.io`。
- 遗留：`/assets/css/style.css` 仍返回 200（旧主题 CSS，模板无引用，每次部署重新出现，已从 sitemap 过滤，可忽略）。
- 文件：`404.html`、`README.md`、`CHANGELOG.MD`
- 验证：推送后请求一个不存在的 URL，确认返回本站自定义 404（含 `site:lordtosky.github.io` 搜索链接）；同时复查 `/404.html` 为 200。
- 提交：见本次推送

## 2026-11-27 · 修复文章元数据与时间

- 内容：为两篇 DLL 文章和体系结构文章补齐 `layout`、`title`、`date`、`tags`；为空的 Flit Mode 重传文章补元数据并设置 `published: false`，避免生成空页面；将 RTL 状态机文章的 16:00 标明为北京时间 `+0800`。
- 文件：`_posts/2026-08-15-DLL概述.md`、`_posts/2026-08-15-DLL概述-LAPTOP-TENF55MD.md`、`_posts/2026-08-28-PCIE-FM-Retransmission.md`、`_posts/体系结构/2026-11-16-体系结构基础知识.md`、`_posts/2026-11-05-RTL-FSM-Register-Ownership-Style.md`、`CHANGELOG.MD`。
- 验证：检查文章开头元数据、日期与文件名一致性及 `git diff --check`；本机未安装 Ruby/Bundler，未运行 Jekyll 构建。

## 2026-11-27 · 补充修复：sitemap 过滤与残留样式

- 内容：`sitemap.txt` 改为只输出 HTML 页面与文章，跳过 `.xml` / `.txt` / `.css` 页面（此前会把 `atom.xml`、`rss.xml`、`sitemap.txt` 自身，以及一个残留的 `/assets/css/style.css` 写进 sitemap）。
- 内容：`exclude` 追加 `assets/css/style.css`，尝试清除该残留样式（内容为旧主题的 normalize/primer CSS，模板里并无引用）。
- 文件：`sitemap.txt`、`_config.yml`
- 验证：推送后检查 `/sitemap.txt` 是否只含 HTML 页面与文章；检查 `/assets/css/style.css` 是否变为 404（若仍存在，说明它来自构建缓存或 CDN，而不是本仓库文件）。
- 提交：本次推送

## 2026-11-27 · 修复与上线

- 内容：把主题作者默认值换成本站信息——`production_url` 改为 `https://lordtosky.github.io`；`title` / `tagline` / `author` 改为 `lordtoSky`；导航与页脚 GitHub 改为 `lordtoSky`，邮箱改为 `1979968187@qq.com`，移除 LinkedIn；404 页搜索链接改为本站 Google `site:` 搜索。
- 内容：`assets/js/custom.js` 的站内搜索域名改为 `site:lordtosky.github.io`，并修正随机语录数组越界（随机下标多加 1 可能取到 `undefined`）。
- 内容：评论原本指向主题作者的 Disqus——`provider` 改为 `false`，删除首页硬编码的评论计数脚本；需要时按 README 6.4 启用自己的 shortname。
- 内容：`_config.yml` 的 `exclude` 补齐 `CHANGELOG.MD`、`Gemfile`、`Gemfile.lock`、`serve.bat`、`tmp`、`_site`、PPTX 与生成脚本；`paginate` 从 `1` 改为 `5`（副作用：旧分页链接 `/blog/pageN/` 会重新编号）。
- 内容：`_includes/head.html` 增加 description、canonical、Open Graph，并去掉重复的 RSS link。
- 内容：停止跟踪 `_site/`（`git rm -r --cached _site`），新增 `.gitignore` 忽略 `_site/`、`.jekyll-cache/`、`.sass-cache/`、`.jekyll-metadata`，消除线上幽灵页面的来源。
- 内容：把此前 3 个未推送提交一并推送；本次构建会让 2026-11-05 的 RTL 文章自动上线（该日期已过）。
- 文件：`_config.yml`、`_layouts/default.html`、`_includes/head.html`、`index.html`、`404.html`、`assets/js/custom.js`、`.gitignore`、`_site/`（移出版本库）、`README.md`、`CHANGELOG.MD`
- 验证：`_config.yml` 与全部带 front matter 的文章经 YAML 解析通过；`custom.js` 通过 `node --check`；线上以 GitHub Pages 构建结果为准（见本次推送后的部署记录）。
- 提交：本次推送

## 2026-11-27 · 文档（本次）

- 内容：把 `README.md` 从主题说明重写为可操作的博客运维手册，覆盖：项目结构、写作/预览/发布流程、GitHub Pages 上线机制、更新与回滚、当前已知问题、经营建议、个性化配置速查、故障排查、变更记录制度、AI 代理维护约定。
- 内容：把本文件从零散的主题变更列表升级为按日期记录的站点变更日志，并补充 2026-07 至 2026-11 的历史记录。
- 内容：核查并记录线上状态——线上最新文章停在 2026-11-02；11-05 文章因 front matter 中 `date: "2026-11-05 16:00:00"` 被构建机按 UTC 判为未来时间而跳过（Jekyll `future: false`）。该日期现已过去，下一次推送触发构建即可补发上线；以后写作避免写当天晚些的时间。
- 内容：记录 `_site/` 误提交导致线上“幽灵页面”（`/CHANGELOG/`、`/assets/css/style.css` 等）的问题，以及 `production_url`、搜索域名、Disqus shortname 仍为主题作者默认值的待办。
- 文件：`README.md`、`CHANGELOG.MD`（文档本身不改站点；同批次的配置/模板修正见上一条记录）。
- 验证：Markdown 结构本地校对；README 已被 `_config.yml` 排除，不会进入构建；CHANGELOG.MD 同样已加入 `exclude`。
- 提交：随 2026-11-27 的文档与修正一起推送

## 2026-11-14 · 内容（3 个提交，尚未推送）

- 内容：更新 HDMI DDC/EDID 项目日志（新增 121 行）。
- 内容：新增 AXI 通道握手完成判断笔记、动态时钟 AXI 配置笔记。
- 文件：`_posts/2026-11-02-HDMI-DDC-EDID-control-path.md`、`_posts/rtl优化/axi通道握手完成判断.md`、`_posts/rtl优化/动态时钟axi配置.md`
- 验证：两个 AXI 笔记文件名无日期前缀且无 front matter，即使推送也不会被 Jekyll 发布；如需发布需重命名为 `2026-11-14-xxx.md` 并补 front matter。
- 提交：`561135f`、`20a120f`、`3377514`

## 2026-11-05 · 内容（尚未上线）

- 内容：新增《RTL 状态机重构：状态转移与寄存器所有权分离》，并在同日补充“按 HDL Compiler for Verilog O-2018.06 复查”章节（+41 行）。
- 文件：`_posts/2026-11-05-RTL-FSM-Register-Ownership-Style.md`
- 验证：该文 `date: "2026-11-05 16:00:00"`（无时区）被构建机当作 UTC；当日两次 Pages 构建（UTC 07:54、08:49）均早于它，Jekyll 按 `future: false` 跳过，线上 404。后续无新推送，因此一直未上线；下一次推送（日期已过）会自动发布。
- 提交：`b057aa2`、`f162f08`

## 2026-11-02 · 内容 + 素材（大批量）

- 内容：新增/补齐 PCIe 重传与 DLLP 系列文章（Flit Mode Replay、Flit Mode Retransmission、Non-Flit Mode 面试题、FM Retransmission 占位文件），新增 LRU（Age Matrix）、TLP+DMA 实现、HDMI DDC/EDID 项目日志，新增 AXI2CHI 设计思路。
- 内容：新增 AXI2CHI 两份设计评审 PPTX、PCIe 7.0 NFM 完整性保护与重传 PPTX，以及配套生成脚本；新增 PCIe Flit/LRU 配图。
- 文件：`_posts/2026-08-25-PCIE-Flit-Mode-Replay.md`、`_posts/2026-08-26-PCIE-Flit-Mode-Retransmission.md`、`_posts/2026-08-26-PCIE-Non-Flit-Mode-Replay-Interview-Questions.md`、`_posts/2026-08-28-PCIE-FM-Retransmission.md`、`_posts/2026-09-21-Age-Matrix.md`、`_posts/2026-09-28-tlp-dma-implementation.md`、`_posts/2026-11-02-HDMI-DDC-EDID-control-path.md`、`_posts/axi2chi_orderbuffer/设计思路.md`、`AXI2CHI_OrderBuffer_Design_Review.pptx`、`AXI2CHI_OrderBuffer_方案权衡.pptx`、`_posts/PCIe_7.0_NFM_完整性保护与重传机制_v3.pptx`、`assets/images/LRU/lru-cache-access-flow.png`、`assets/images/PCIE/pcie-flit-mode-*.png`、`make_axi2chi_*_slide.py`
- 验证：11-02 的 Pages 构建成功；其中日期为 11-02 11:00 的 HDMI 日志在当次被当作“未来文章”跳过，由 11-05 的构建补发上线，其余带日期前缀的文章均已上线；`2026-08-28-PCIE-FM-Retransmission.md` 为 0 字节空文章，线上生成了一个空页面，待补内容或删除。
- 提交：`bdce600`

## 2026-08-17 ~ 2026-08-28 · 内容（PCIe DLL / 重传系列）

- 内容：新增 PCIe DLL 概述并逐步扩写；新增 PCIe 7.0 重传机制（Retry Buffer / Ack/Nak / Replay Timer）、Non-Flit Mode LCRC 与 Sequence Number、DLLP 接收差异、Retry Buffer 容量设计、Flit Mode Replay 等文章。
- 内容：新增 Data Link Feature Exchange、VC 工作原理、DLL 分层状态机等 SVG/PNG 配图与图表源码（`assets/diagrams/`）。
- 文件：`_posts/2026-08-15-DLL概述.md`、`_posts/2026-08-21-PCIE-Replay.md`、`_posts/2026-08-24-PCIE-DLLP-Receive.md`、`_posts/2026-08-24-PCIE-Non-Flit-LCRC-Sequence-Number.md`、`_posts/2026-08-25-PCIE-Retry-Buffer-Sizing.md`、`_posts/2026-08-25-PCIE-Flit-Mode-Replay.md`、`assets/images/PCIE/*`、`assets/diagrams/*`
- 验证：`ba7f48d` 之后的构建均已上线；`2026-08-15-DLL概述-LAPTOP-TENF55MD.md` 为同题备份副本（无 front matter），线上生成了一份重复内容。
- 提交：`ba7f48d`、`e436ff6`、`a421e01`、`b89ed59`、`1062032`、`0eea744`、`616a687`、`6d478d1`、`03682a0`、`89a9fe2`

## 2026-08-10 ~ 2026-08-15 · 内容 + 首页定制

- 内容：新增 PCIe TLP 结构、ECRC 生成、Flit/Non-Flit 区别、CRC 算法概述；扩写 ECRC 与 poisoning 相关章节；修复重复标题。
- 内容：定制首页页头打字机文案（改为中文语句）。
- 文件：`_posts/2026-08-06-PCIE-TLP-format.md`、`_posts/2026-08-06-PCIE-ECRC_Generate.md`、`_posts/2026-08-10-diff-between-flit-no-flit.md`、`_posts/2026-08-11-CRC算法概述.md`、`_layouts/default.html`
- 验证：线上归档页可见对应文章；首页文案已生效。
- 提交：`a4d12bf`、`c0343ec`、`a4bbdd0`、`29167e8`、`b227d85`、`f4d428c`、`67ecada`、`c2d5fb9`

## 2026-08-05 ~ 2026-08-06 · 站点样式与首批文章

- 内容：新增 HyperLogLog（含 MathJax 支持）、Echo Archive 卡牌设计、Exile 短篇、PCIe LCRC/ECRC 等文章及配图。
- 内容：站点样式系列调整——桌面布局加宽、侧栏收窄、列表与表格边框修复、PCIe 文章标题编号、重新生成静态站点与订阅源时间戳。
- 文件：`_posts/2026-07-29-HyperLogLog.md`、`_posts/2026-08-02-echo-archive-card-design.md`、`_posts/2026-08-03-excile.md`、`_posts/2026-08-04-PCIE-LCRC&ECRC.md`、`assets/css/custom.css`、`_layouts/*`、`index.html`、`atom.xml`、`rss.xml`
- 验证：线上文章与样式均已生效（注意：本阶段用本地构建产物直接提交，`_site/` 的旧文件会持续污染线上，见 README 第 6.3 节）。
- 提交：`463b804`、`ca4a4e7`、`d637a54`、`7421da5`、`8a02628`、`dc07be9`、`641f825`、`5f37ebc`、`f0ef38b`、`d55c7c5`、`5b39ad5`、`4444e4d`、`fbc9fe6`、`e927ecf`、`e3c2308`、`eb6f33d`、`b7072fc`、`49affae`、`6e6c01e`、`ba7d1be`、`472d054`、`ef7f7e9`、`2938057`、`92eddd4`、`37a90ff`、`e741a51`、`2313d8d`

## 2026-07-29 · 站点初始化

- 内容：以 Soot Spirits 主题初始化博客，首次构建成功。
- 内容：首次本地构建的产物 `_site/`（59 个文件）被一并提交进版本库，后续多次“Regenerate …”提交继续带入旧页面。
- 文件：全仓库初始导入（主题布局、样式、示例文章、`_config.yml`、`Gemfile`、`_site/` 等）。
- 验证：<https://lordtosky.github.io/> 可访问。
- 提交：`261f7bb`、`7a81c5b`

## 主题自带初始变更（无日期，保留自原 CHANGELOG）

以下为 Soot Spirits 主题开发期的变更清单，随主题一并带入本仓库，无对应日期：

- Added pagination to the main page and post pages.
- Added Gemfile and gitignore files.
- Added syntax highlighting.
- Fixed lists being misaligned.
- Fixed heading, they weren't being styled.
- Added `relative_url` to a lot of links so they'd work everywhere.
- Generally fixed links to use `relative_url` wherever possible.

---

<sub>规则回顾：下一次改动时，把新记录加在上面的第一条之前，并写清日期、类型、内容、文件、验证方式。</sub>
