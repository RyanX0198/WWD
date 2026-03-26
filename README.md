# 政府公文智能写作助手

基于 Agent Harness 架构的智能公文写作系统。

## 项目结构

```
gov-writing-assistant/
├── backend/              # Python 后端服务
│   ├── app/
│   │   ├── core/        # Harness 核心引擎
│   │   ├── api/         # REST API
│   │   └── main.py      # 服务入口
│   ├── knowledge/       # 知识库
│   └── requirements.txt
├── desktop/             # Tauri 桌面端
│   ├── src/             # Vue3 前端代码
│   ├── src-tauri/       # Tauri 配置
│   └── package.json
└── README.md
```

## 快速开始

### 后端服务

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key

# 启动服务
uvicorn app.main:app --reload
```

### 桌面端

```bash
cd desktop
npm install

# 开发模式
npm run tauri-dev

# 构建
npm run tauri-build
```

## 技术栈

- **后端**: Python 3.11 + FastAPI + LangGraph + Deep Agents
- **桌面端**: Tauri (Rust + Vue3 + TypeScript)
- **向量数据库**: Qdrant
- **缓存**: Redis
- **LLM**: 
  - 国内主力: Kimi / 通义千问 / ChatGLM / MiniMax
  - 国外备用: GPT-5 / Claude

## 功能特性

### 核心功能
- **智能写作**: 输入主题自动生成公文初稿
- **大纲生成**: 一键生成结构化大纲
- **知识库管理**: 人物档案、政策文件、写作模板
- **模板匹配**: 智能匹配相似模板
- **文档导出**: 支持 Word / PDF / Markdown

### 支持的文档类型
- 领导讲话稿
- 工作总结
- 活动策划
- 会议纪要

## 文档

- [API 文档](http://localhost:8000/docs) (服务启动后访问)
- [PRD & 技术方案](./docs/PRD.md)

## 开发阶段

- [x] Phase 1: MVP 核心功能
  - [x] Harness 引擎核心
  - [x] 写作 API
  - [x] 知识库管理
  - [x] 向量检索
  - [x] 政策文件管理
  - [x] 模板系统
  - [x] 文档导出
  - [x] 桌面端 UI
- [ ] Phase 2: 功能完善 (8-10 周)
- [ ] Phase 3: 规模化

## License

MIT