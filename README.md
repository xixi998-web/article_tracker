# Article Tracker — 统一论文追踪工作流

> 同时追踪 **arXiv 预印本** + **顶刊正式论文**（Nature/Science/Cell/PNAS 等），自动采集、去重、筛选、增强、多通道推送。

---

## ✨ 核心功能

| 能力 | 说明 |
|------|------|
| 🎯 **双源采集** | arXiv Atom Feed + Semantic Scholar（主搜索顶刊）→ OpenAlex（补充期刊元数据） |
| 🔄 **跨源去重** | DOI → arXiv ID → title 模糊匹配(0.85)，自动合并更完整字段 |
| 📝 **三源摘要补全** | Semantic Scholar → OpenAlex → Crossref fallback，任一成功即停止 |
| 🤖 **LLM 双语摘要** | 扩展到顶刊论文，英文+中文一段话总结（DeepSeek/SiliconFlow 等 OpenAI 兼容） |
| 🏷️ **四层筛选** | core / proxy / eco / noise，Markdown Profile 驱动关键词匹配 |
| 📬 **九通道输出** | JSON / Markdown / PDF / 邮件 / GitHub Pages / Excel / HTML 交互表 / Obsidian / Zotero |
| ⏰ **CI/CD 自动化** | GitHub Actions 每日定时（北京时间 09:30），支持手动触发 |
| 🔗 **代码链接补全** | 从 S2 元数据 + HTML 页面自动提取 GitHub/GitLab 代码仓库链接 |
| 📦 **配置迁移** | 一键从旧 Arxiv-tracker / frontier-tracker 配置迁移到统一格式 |

---

## 🚀 快速开始

### 1. Fork 或 Clone

```bash
git clone https://github.com/<你的用户名>/article_tracker.git
cd article_tracker
pip install -e ".[all]"
```

### 2. 创建配置文件

```bash
cp config.example.yaml config.yaml
# 编辑 config.yaml，调整关键词、输出通道等
```

### 3. 配置环境变量

创建 `.env` 文件（本地运行）或在 GitHub Secrets 中设置（CI/CD）：

| 变量 | 说明 | 必须 |
|------|------|:----:|
| `S2_API_KEY` | Semantic Scholar API Key | **是** |
| `OPENALEX_EMAIL` | OpenAlex 礼貌池邮箱（加速请求） | 否 |
| `DS_API_KEY` | DeepSeek/SiliconFlow LLM Key | 否 |
| `SMTP_USER` / `SMTP_PASS` | 邮件推送账号/密码 | 否 |

### 4. 运行

```bash
# 追踪全部来源（arXiv + 顶刊）
article_tracker track --config config.yaml --source all

# 仅追踪 arXiv
article_tracker track --source arxiv

# 仅追踪顶刊
article_tracker track --source top_journal

# 试运行（不产生输出文件）
article_tracker track --dry-run

# 校验配置文件
article_tracker validate --config config.yaml
```

---

## ⚙️ 配置说明

配置文件为 `config.yaml`，主要配置项：

```yaml
# arXiv 源
arxiv:
  enabled: true
  categories: ["cs.CV", "cs.AI", "cs.LG"]
  keywords: ["diffusion model", "vision-language"]
  exclude_keywords: ["survey"]
  logic: "AND"
  max_results: 50

# 顶刊源（Semantic Scholar 主搜索）
top_journal:
  enabled: true
  watchlist_path: "references/top-journal-families.md"
  since_days: 7

# 去重
dedup:
  title_threshold: 0.85      # 标题模糊匹配阈值
  prefer_source: "top_journal"  # 同一篇论文优先保留顶刊版本

# 四层筛选
screening:
  profile_path: "references/research-profile.md"
  output_tiers: ["core", "proxy", "eco"]  # 输出哪些层级

# LLM 双语摘要
llm:
  enabled: false
  base_url: ""               # DeepSeek/SiliconFlow API 地址
  model: ""
  api_key_env: "DS_API_KEY"

# 输出通道（每通道独立开关）
output:
  json_enabled: true
  md_enabled: true
  email:
    enabled: false
  ghpages:
    enabled: false
```

完整配置参考 [`config.example.yaml`](config.example.yaml)。

---

## 📖 研究 Profile

在 `references/research-profile.md` 中定义研究兴趣，驱动四层筛选：

```markdown
## Core Keywords
- deep learning
- computer vision
- large language model

## Proxy Keywords
- representation learning
- contrastive learning

## Eco Keywords
- optimization
- Bayesian inference

## Exclusion
- survey
- review

## Must-Track Journals
- Nature
- Science
```

---

## 📰 顶刊 Watchlist

在 `references/top-journal-families.md` 中配置追踪的期刊家族：

```markdown
## Nature Family
- Nature
- Nature Communications
- Nature Methods

## Science Family
- Science
- Science Advances

## PNAS
- Proceedings of the National Academy of Sciences
```

---

## 🔧 CLI 命令

| 命令 | 说明 |
|------|------|
| `article_tracker track` | 运行追踪（采集→去重→增强→筛选→输出） |
| `article_tracker weekly-report` | 生成周报 |
| `article_tracker watchlist build` | 构建期刊 watchlist |
| `article_tracker watchlist show` | 显示当前 watchlist |
| `article_tracker migrate --from-arxiv <path>` | 从旧 Arxiv-tracker 迁移配置 |
| `article_tracker migrate --from-frontier <path>` | 从旧 frontier-tracker 迁移去重状态 |
| `article_tracker validate` | 校验配置文件 |

---

## 🌐 FastAPI 接口

```bash
pip install -e ".[api]"
uvicorn article_tracker.api:app --host 0.0.0.0 --port 8000
```

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/track` | POST | 触发追踪任务 |
| `/api/v1/track/{task_id}` | GET | 查询任务状态 |
| `/api/v1/articles` | GET | 查询论文列表 |
| `/api/v1/weekly-report` | POST | 触发周报生成 |
| `/api/v1/health` | GET | 健康检查 |

---

## 🔄 GitHub Actions 部署

### 1. 配置 Secrets

在仓库 **Settings → Secrets → Actions** 中添加：

| Secret | 说明 | 必须 |
|--------|------|:----:|
| `S2_API_KEY` | Semantic Scholar API Key | **是** |
| `OPENALEX_EMAIL` | OpenAlex 邮箱 | 否 |
| `DS_API_KEY` | LLM Key | 否 |
| `SMTP_USER` / `SMTP_PASS` | 邮件推送 | 否 |

### 2. 自动运行

工作流每天 **北京时间 09:30** 自动运行，流程：

```
checkout → setup-python → install → track → deploy-ghpages → notify-on-failure
```

### 3. 手动触发

```bash
gh workflow run tracker_daily.yml
# 或在 GitHub Actions 页面点击 "Run workflow"
```

---

## 🏗️ 项目结构

```
article_tracker/
├── cli.py              # CLI 统一入口 (click)
├── api.py              # FastAPI HTTP 接口
├── config/             # 配置加载 + Pydantic schema + 迁移工具
├── models/             # Article + ResearchProfile (Pydantic V2)
├── source/             # BaseSource → ArxivSource + TopJournalSource
├── collect/            # Collector 多源编排
├── dedup/              # SeenStore + Deduplicator (三级去重)
├── enrich/             # AbstractEnricher + CodeLinkEnricher + LLMEnricher
├── screen/             # ProfileLoader + TierClassifier (四层筛选)
├── output/             # OutputManager → 九通道输出
├── schedule/           # LocalScheduler + GitHub Actions 生成器
├── infra/              # http_client + retry + RunLog
└── utils/              # text similarity
```

---

## 🔄 从旧系统迁移

如果你之前使用 Arxiv-tracker 或 frontier-tracker，可以一键迁移：

```bash
# 从 Arxiv-tracker 迁移配置
article_tracker migrate --from-arxiv path/to/old/config.yaml

# 从 frontier-tracker 合并去重状态
article_tracker migrate --from-frontier path/to/old/reading_state.json
```

---

## 📊 工作流数据流

```
采集(arXiv + S2) → 去重(DOI→arXiv ID→title) → 摘要补全(S2→OA→Crossref)
  → 代码链接补全 → LLM双语摘要 → 四层筛选(core/proxy/eco/noise)
  → 九通道输出(JSON/MD/PDF/Email/GitHub Pages/Excel/HTML/Obsidian/Zotero)
```

---

## 📄 License

MIT
