# Novel Rank Data

中文网文市场热点分析工具，用来采集主流小说平台的榜单信号，归一化为可分析数据，再生成选题机会报告、Hermes 写作 brief 和发布反馈报告。

这个项目适合做“市场雷达”，帮助你判断不同平台近期更热的题材、hook 和标题信号。它不会直接保证盈利，收益判断需要结合你发布后的阅读、收藏、追读、评论和收入数据继续校准。

## 功能

- 抓取起点、晋江、番茄、七猫、纵横等平台的榜单/首页信号
- 提取小说标题、作者、分类、简介、标签、排名等字段
- 归一化为 JSONL 和 SQLite 数据
- 生成市场简报和日间变化报告
- 按平台、题材、hook 生成机会评分
- 导出 Hermes 可直接使用的写作 brief
- 手动记录作品发布反馈，并生成反馈分析报告
- 提供降低 AI 味、适配平台风格的写作 skill

## 目录结构

```text
src/novel_rank_data/     核心 Python 模块
scripts/                 抓取、归一化、报告和反馈脚本
skills/                  Hermes/Codex 可用的网文市场与写作 skill
publish/                 可发布的 skill 包
tests/                   标准库 unittest 测试
docs/superpowers/        功能设计和实现计划
data/                    本地数据目录，默认不提交
reports/                 生成报告目录，默认不提交
```

## 环境要求

- Python 3.11 或更高版本
- Node.js，可选，用于 Playwright 浏览器抓取
- npm，可选，用于运行封装命令

安装 Node 依赖：

```bash
npm install
```

## 快速开始

抓取并生成基础市场报告：

```bash
npm run fetch
npm run normalize
npm run brief
npm run delta
```

生成机会评分报告：

```bash
npm run opportunities -- --limit 20
```

导出某个平台的 Hermes 写作 brief：

```bash
npm run hermes -- --platform fanqie
npm run hermes -- --platform qidian
npm run hermes -- --platform jjwxc
```

指定题材和 hook：

```bash
npm run hermes -- --platform fanqie --genre 历史古代 --hook 经营种田
```

## Hermes 使用方式

Hermes 可以把这个项目当成“市场情报 + 写作约束生成器”使用。

推荐流程：

```bash
npm install
npm run fetch
npm run normalize
npm run opportunities -- --limit 20
npm run hermes -- --platform fanqie
```

生成后，让 Hermes 读取：

```text
reports/opportunities.md
reports/hermes_brief_fanqie.md
```

可以给 Hermes 这样的指令：

```text
请读取 reports/opportunities.md 和 reports/hermes_brief_fanqie.md，
根据里面的平台、题材、hook、市场证据和写作约束，
生成 10 个书名候选、5 个一句话卖点、前 20 章主线承诺，
以及第一章 1500 字开篇。

要求：
- 不要复制榜单作品的书名、人物、设定或桥段
- 前 200 字进入压力场景
- 解释比例控制在 15% 以内
- 对白承担冲突、信息差或情绪变化
- 只输出可用正文和创作材料，不要解释创作思路
```

如果想换平台：

```bash
npm run hermes -- --platform qidian
npm run hermes -- --platform jjwxc
npm run hermes -- --platform qimao
npm run hermes -- --platform zongheng
```

如果已经确定赛道：

```bash
npm run hermes -- --platform fanqie --genre 历史古代 --hook 经营种田
```

发布后，把作品反馈录回项目：

```bash
npm run feedback:add -- \
  --title "作品名" \
  --platform fanqie \
  --genre 历史古代 \
  --hook 经营种田 \
  --chapters 10 \
  --words 20000 \
  --views 1000 \
  --favorites 80 \
  --comments 12 \
  --revenue 35.5

npm run feedback:report
```

下一轮创作时，可以让 Hermes 同时参考：

```text
reports/feedback_report.md
```

这样选题会从“榜单热度判断”逐步变成“榜单热度 + 自己作品真实反馈”的闭环。

## 发布反馈闭环

发布作品后，手动记录关键数据：

```bash
npm run feedback:add -- \
  --title "作品名" \
  --platform fanqie \
  --genre 都市 \
  --hook 经营种田 \
  --chapters 10 \
  --words 20000 \
  --views 1000 \
  --favorites 80 \
  --comments 12 \
  --revenue 35.5
```

生成反馈报告：

```bash
npm run feedback:report
```

## 常用脚本

```bash
npm run fetch            # 抓取平台榜单/首页信号
npm run normalize        # 标准化数据并写入 SQLite
npm run brief            # 生成市场简报
npm run delta            # 生成最新两天变化报告
npm run opportunities    # 生成赛道机会评分报告
npm run hermes           # 生成 Hermes 写作 brief
npm run feedback:add     # 记录发布反馈
npm run feedback:report  # 生成发布反馈报告
```

也可以直接运行 Python 脚本：

```bash
python3 scripts/fetch_rankings.py --platforms qidian jjwxc fanqie qimao zongheng
python3 scripts/normalize_rankings.py
python3 scripts/build_opportunity_report.py
python3 scripts/export_hermes_brief.py --platform fanqie
```

## 测试

项目使用 Python 标准库 `unittest`，不需要额外安装 `pytest`：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## 数据和隐私

以下内容默认不会提交到公开仓库：

- `data/raw/` 原始网页和 JSON 快照
- `data/normalized/` 标准化数据
- `data/feedback/` 手动录入的作品反馈
- `data/*.sqlite` 本地数据库
- `reports/` 生成报告
- `node_modules/` 本地依赖

公开仓库主要保存代码、脚本、测试、skill 和文档。请在公开发布前确认没有提交平台后台数据、个人收益数据、未公开作品正文或账号信息。

## 工作流建议

1. 每天抓取一次榜单数据。
2. 连续积累 2 到 4 周后观察变化趋势。
3. 用机会报告选择平台、题材和 hook。
4. 用 Hermes brief 生成大纲、开篇或章节约束。
5. 发布后记录阅读、收藏、评论和收入。
6. 用反馈报告校准下一轮选题。

## 免责声明

本项目只做公开网页信号采集和本地分析，不提供盈利承诺。请遵守各平台服务条款、版权规则和 AI 内容相关规范。
