# 政府公文智能写作助手

基于 Agent Harness 架构的智能公文写作系统。

## 项目结构

```
gov-writing-assistant/
├── backend/              # Python 后端服务
│   ├── app/
│   │   ├── core/        # Harness 核心引擎
│   │   ├── api/         # REST API
│   │   ├── services/    # 业务服务
│   │   └── tools/       # Agent 工具集
│   ├── knowledge/       # 知识库
│   └── requirements.txt
├── desktop/             # Tauri 桌面端
│   ├── src/
│   └── src-tauri/
├── mobile/              # React Native 移动端 (Phase 2)
├── docs/                # 文档
└── README.md
```

## 快速开始

### 后端服务

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 桌面端

```bash
cd desktop
npm install
npm run tauri dev
```

## 技术栈

- **后端**: Python 3.11 + FastAPI + LangGraph + Deep Agents
- **桌面端**: Tauri (Rust + Web)
- **向量数据库**: Qdrant
- **缓存**: Redis
- **LLM**: GPT-5 / Claude / Kimi (多模型路由)

## 文档

- [PRD & 技术方案](./docs/PRD.md)
- [API 文档](./docs/API.md) (待完善)
- [部署指南](./docs/DEPLOY.md) (待完善)

## 开发阶段

- [x] Phase 0: 项目初始化
- [ ] Phase 1: MVP (6-8 周)
  - [ ] Harness 引擎核心
  - [ ] 基础写作功能
  - [ ] 知识库管理
- [ ] Phase 2: 功能完善 (8-10 周)
- [ ] Phase 3: 规模化

## License

MIT