# hexinzxq/blog

个人站。每天 20:00（北京时间）由 GitHub Actions 自己重建一次：读我的公开仓库，把最近两周的 commit 贴出来，顺便重新发布。

线上地址：<https://hexinzxq.github.io/blog/>

## 为什么是「构建日志」而不是作品集

作品集靠回忆，构建日志靠时间戳。前者容易写成「热爱技术、擅长协作」，后者会诚实地暴露我这一周到底动了哪些文件——包括那些只改了一个 typo 的提交。

## 结构

```
index.html            一个页面，没有前端框架
assets/styles.css     设计计划在文件头注释里（配色/排版/栅格/动效/风险各一行）
assets/app.js         读 JSON 渲染项目列表和日志
data/site.json        手工维护：三个特色项目、各自的「为什么值得看」
data/updates.json     自动生成：最近 14 天的 commit，别手改
scripts/collect.py    抓 GitHub API，纯标准库
.github/workflows/    每天 12:00 UTC 生成 → 提交 → 部署 Pages
```

## 本地看

```bash
python3 -m http.server 8000
# 打开 http://localhost:8000
```

直接双击 `index.html` 看不到内容——`fetch` 读本地 JSON 会被 CORS 拦，必须起个静态服务器。

## 改内容

- **换项目**：改 `data/site.json`，字段是 `name / url / why / stack / note`。
- **换时间窗口**：`scripts/collect.py` 顶部的 `WINDOW_DAYS`。
- **换配色排版**：`assets/styles.css` 顶部的设计计划注释先改，再改 token——先有理由，再有效果。

## 设计约束

按 [skillforge 的 frontend-design](https://github.com/hexinzxq/skillforge/blob/main/skills/frontend-design/SKILL.md) 走：

- 六个颜色角色，一个 accent，正文对比度 ≥ 4.5:1
- 排版只有一个家族加一个等宽，数字全部 tabular-nums
- 唯一一个编排动效（日志逐条入场），`prefers-reduced-motion` 下关掉
- 键盘可达，`:focus-visible` 有 2px 琥珀描边
- 手机断点 760px，时间轴缩进同步收窄
