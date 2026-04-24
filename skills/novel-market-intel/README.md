# Novel Market Intel

`novel-market-intel` 是一个面向中文网文市场研判的 Skill，用来分析主要小说平台的热点题材、榜单变化和读者偏好，并把这些信号整理成可直接指导写作的市场简报。

## 这个 Skill 能做什么

- 采集主流网文平台的榜单和曝光位信号
- 对比日、周、月三个时间尺度的题材变化
- 提炼题材、套路、卖点、标题包装和读者承诺
- 生成 Hermes Agent 可直接使用的市场分析结论

## 文件结构

- `SKILL.md`：Hermes Agent 的执行说明和工作流
- `references/platforms.md`：平台覆盖范围、平台差异和信号来源建议
- `references/analysis-framework.md`：标准化字段和热点分析方法
- `scripts/`：内置抓取、标准化、简报、变化报告、提示词导出脚本
- `src/novel_rank_data/`：脚本运行所需的最小 Python 模块
- `package.json`：可选的浏览器抓取依赖说明，主要用于 `起点中文网`
- `agents/openai.yaml`：Skill 展示元数据

## 推荐配套流程

建议直接在 Skill 目录中按下面顺序执行：

```bash
python3 scripts/fetch_rankings.py --platforms qidian jjwxc fanqie qimao zongheng
python3 scripts/normalize_rankings.py
python3 scripts/build_market_brief.py
python3 scripts/build_delta_report.py
```

## 产出内容

- 原始抓取快照：`data/raw/`
- 标准化结果：`data/normalized/rankings.jsonl`
- 历史数据库：`data/novel_rank_data.sqlite`
- 市场简报：`reports/market_brief.md`
- 变化报告：`reports/market_delta.md`

## Hermes 使用建议

- 优先执行内置脚本，不要默认退回手工网页抓取。
- 如果安装目录里缺少 `scripts/` 或 `src/novel_rank_data/`，应直接报“Skill 安装不完整”。
- 如果本机没有 `node` 或 `playwright-core`，仍然可以跑大部分平台；只是 `起点中文网` 可能只能拿到部分数据。
- 如果脚本报错，先反馈具体命令和报错，再缩小平台范围重试，而不是直接开多个子代理并发手工抓取。

## 适合怎样配合 Hermes Agent

建议在正式写小说之前先调用这个 Skill。Hermes 应先完成平台热点采集和赛道判断，再把选中的平台约束、题材信号和风险提示传给写作类 Skill。
