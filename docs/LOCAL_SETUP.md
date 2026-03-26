# 本地运行测试指南

**文档版本**: v1.0  
**更新日期**: 2026-03-26  

---

## 📋 环境要求

### 必需环境
| 组件 | 版本要求 | 用途 |
|-----|---------|------|
| Python | 3.11+ | 后端服务 |
| Node.js | 18+ | 桌面端构建 |
| Rust | 最新版 | Tauri 桌面端 |
| Git | 任意 | 代码管理 |

### 可选服务
| 服务 | 用途 | 说明 |
|-----|------|------|
| Qdrant | 向量检索 | 不配置则回退到关键词搜索 |
| Redis | 缓存 | 不配置则使用内存缓存 |
| PostgreSQL | 文档存储 | Phase 2 需要 |

---

## 🚀 快速开始

### 方式 1: 仅后端 + Web 测试（推荐入门）

适合先测试 API 功能，不需要桌面端界面。

```bash
# 1. 克隆代码
git clone https://github.com/RyanX0198/WWD.git
cd WWD

# 2. 配置后端
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key

# 5. 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

服务启动后：
- API 文档: http://localhost:8000/docs
- API 端点: http://localhost:8000

---

### 方式 2: 完整体验（后端 + 桌面端）

#### Step 1: 启动后端（同上）

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Step 2: 启动桌面端（新开终端）

```bash
cd desktop

# 安装依赖
npm install

# 开发模式（推荐）
npm run tauri-dev

# 或者先单独启动前端
npm run dev
```

桌面端启动后：
- 应用窗口自动打开
- 前端开发服务器: http://localhost:5173

---

## ⚙️ 详细配置

### 1. API Key 配置

编辑 `backend/.env`:

```bash
# 国内模型（至少配置一个）
KIMI_API_KEY=sk-your-kimi-key-here          # https://platform.moonshot.cn/
DASHSCOPE_API_KEY=sk-your-qwen-key-here     # https://dashscope.aliyun.com/
ZHIPU_API_KEY=your-glm-key-here             # https://open.bigmodel.cn/
MINIMAX_API_KEY=your-minimax-key-here       # https://www.minimaxi.com/

# 国外模型（可选，作为备用）
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
```

**推荐**: 优先配置 Kimi，稳定性和中文能力较好。

---

### 2. 向量数据库（可选）

如果需要语义搜索功能，启动 Qdrant：

```bash
# Docker 启动
docker run -p 6333:6333 qdrant/qdrant

# 或下载本地版本
# https://github.com/qdrant/qdrant/releases
```

配置 `backend/.env`:
```bash
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

---

### 3. Redis（可选）

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Docker
docker run -p 6379:6379 redis
```

---

## 🧪 功能测试

### 测试 1: 基础 API

```bash
# 健康检查
curl http://localhost:8000/health

# 查看文档列表
curl http://localhost:8000/api/documents
```

### 测试 2: 生成公文

```bash
curl -X POST http://localhost:8000/api/writing/generate \
  -H "Content-Type: application/json" \
  -d '{
    "document_type": "讲话稿",
    "topic": "2026年全省经济工作会议讲话",
    "requirements": "重点强调经济发展和民生改善"
  }'
```

### 测试 3: 知识库操作

```bash
# 获取人物列表
curl http://localhost:8000/api/knowledge/people

# 获取人物详情
curl http://localhost:8000/api/knowledge/people/张三
```

### 测试 4: 导出功能

```bash
# 导出 Markdown
curl "http://localhost:8000/api/documents/test/export?format=markdown&title=测试文档&content=测试内容"

# 导出 Word
curl "http://localhost:8000/api/documents/test/export?format=word&title=测试文档&content=测试内容" \
  --output test.docx
```

---

## 🐛 常见问题

### 问题 1: 模型调用失败

**现象**: 生成文档时返回错误  
**解决**:
1. 检查 `.env` 是否配置了 API Key
2. 检查网络是否能访问模型 API
3. 查看后端日志确认具体错误

```bash
# 测试模型连接
curl https://api.moonshot.cn/v1/models \
  -H "Authorization: Bearer $KIMI_API_KEY"
```

---

### 问题 2: 向量检索不可用

**现象**: 搜索返回空结果  
**解决**: 这是正常的，如果没有配置 Qdrant，系统会回退到关键词搜索。如需语义搜索，启动 Qdrant 即可。

---

### 问题 3: 前端无法连接后端

**现象**: 桌面端提示 API 错误  
**解决**:
1. 确认后端已启动在 `http://localhost:8000`
2. 检查 `desktop/vite.config.ts` 中的代理配置
3. 检查浏览器控制台网络请求

---

### 问题 4: Tauri 构建失败

**现象**: `npm run tauri-dev` 报错  
**解决**:
1. 确保 Rust 已安装: `rustc --version`
2. 安装 Tauri 依赖:
   ```bash
   # macOS
   brew install llvm
   
   # Ubuntu
   sudo apt-get install libwebkit2gtk-4.0-dev
   ```

---

## 📊 验证清单

启动后检查以下功能：

### 后端验证
- [ ] API 文档可访问 (http://localhost:8000/docs)
- [ ] 健康检查返回 OK
- [ ] 文档生成接口正常工作
- [ ] 知识库查询正常

### 桌面端验证
- [ ] 应用窗口正常打开
- [ ] 侧边栏导航正常
- [ ] 智能写作页面可输入主题
- [ ] 生成大纲功能正常
- [ ] AI 写作功能正常
- [ ] 知识库页面可查看人物

---

## 🔧 开发调试

### 后端调试
```bash
# 详细日志
uvicorn app.main:app --reload --log-level debug

# 指定模块调试
LOG_LEVEL=debug uvicorn app.main:app --reload
```

### 前端调试
```bash
# 单独启动前端（不启动 Tauri）
cd desktop
npm run dev

# 然后在浏览器打开 http://localhost:5173
```

### 热重载
- 后端: 修改代码自动重启
- 前端: 修改代码自动刷新
- Tauri: 修改 Rust 代码自动重建

---

## 📚 相关文档

- [API 文档](http://localhost:8000/docs) (服务启动后访问)
- [项目计划](../PROJECT_PLAN.md)
- [看板](../KANBAN.md)

---

**遇到问题？** 查看 GitHub Issues 或联系开发团队。
