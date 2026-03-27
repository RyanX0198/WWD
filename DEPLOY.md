# 🚀 政府公文智能写作助手 - 部署指南

**项目地址**: https://github.com/RyanX0198/WWD

**最后更新**: 2026-03-27

---

## 📋 环境要求

### 后端 (Python)
- Python 3.11+ (推荐 3.11，避免 3.12 的依赖兼容问题)
- Conda 或虚拟环境
- 可选: Docker (用于 Qdrant 向量数据库)

### 前端 (桌面端)
- Node.js 18+
- npm 或 yarn

---

## 🔧 后端部署

### 1. 克隆项目

```bash
git clone https://github.com/RyanX0198/WWD.git
cd WWD/backend
```

### 2. 创建 Python 环境

**使用 Conda (推荐):**
```bash
conda create -n govwriting python=3.11 -y
conda activate govwriting
```

**或使用 venv:**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### 3. 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**⚠️ 已知问题 - Python 3.12 兼容性:**

如果 Python 3.12 遇到 `python-markdown` 安装失败，执行以下命令跳过该依赖：

```bash
# 单独安装核心依赖（不包含 python-markdown）
pip install fastapi uvicorn pydantic pydantic-settings \
    langchain langchain-openai langchain-anthropic langgraph \
    python-jose passlib python-multipart qdrant-client \
    anthropic openai
```

### 4. 配置环境变量

创建 `.env` 文件：

```bash
# 必需 - 选择至少一个 LLM 提供商
KIMI_API_KEY=your_kimi_api_key_here
# 或
DASHSCOPE_API_KEY=your_dashscope_api_key_here
# 或
ZHIPU_API_KEY=your_zhipu_api_key_here

# 可选 - Qdrant 向量数据库（本地开发可跳过）
QDRANT_HOST=localhost
QDRANT_PORT=6333

# 可选 - Redis（本地开发可跳过）
REDIS_URL=redis://localhost:6379/0

# JWT 密钥（生产环境必须修改）
SECRET_KEY=your-secret-key-change-in-production
```

**获取 API Key:**
- Kimi: https://platform.moonshot.cn/
- 通义千问: https://dashscope.aliyun.com/
- ChatGLM: https://open.bigmodel.cn/

### 5. 启动 Qdrant (可选)

如果需要向量检索功能：

```bash
docker run -d -p 6333:6333 --name qdrant qdrant/qdrant
```

> 注意：没有 Qdrant 时，知识库和向量检索功能会报错，但不影响基础写作功能。

### 6. 启动后端服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**验证启动成功:**
- 浏览器访问: http://localhost:8000/docs
- 应看到 Swagger API 文档页面

---

## 💻 桌面端部署

### 1. 进入桌面端目录

```bash
cd WWD/desktop
```

### 2. 配置 npm 镜像 (国内网络)

```bash
npm config set registry https://registry.npmmirror.com
```

### 3. 安装依赖

```bash
npm install
```

### 4. 配置 API 地址

编辑 `src/utils/request.ts`，确保 API 基地址正确：

```typescript
const baseURL = 'http://localhost:8000'  // 后端地址
```

### 5. 启动开发服务器

```bash
npm run dev
```

**启动成功后:**
- 浏览器自动打开: http://localhost:1420/
- 或手动访问该地址

---

## ✅ 功能验证清单

### 后端 API 测试

| 功能 | 测试地址 | 期望结果 |
|------|----------|----------|
| API 文档 | http://localhost:8000/docs | Swagger UI 正常显示 |
| 健康检查 | http://localhost:8000/health | 返回 `{"status": "ok"}` |
| 写作接口 | 在 Swagger 中测试 POST /api/writing/generate | 返回生成内容 |

### 桌面端功能测试

| 页面 | 测试项 |
|------|--------|
| **智能写作** | 选择文档类型 → 输入主题 → 点击 AI写作 → 生成内容 |
| **知识库** | 新建人物档案 → 保存 → 列表显示 |
| **文档管理** | 查看文档列表 → 点击历史版本 → 显示版本对比 |
| **协作编辑** | 打开同一文档两个窗口 → 一侧输入 → 另一侧实时同步 |

---

## 🐛 常见问题

### 1. Python SSL 证书错误

**症状:** `SSL: CERTIFICATE_VERIFY_FAILED`

**解决:**
```bash
# macOS
/Applications/Python\ 3.11/Install\ Certificates.command

# 或使用 Conda 环境（已修复证书问题）
conda activate govwriting
```

### 2. python-markdown 安装失败

**症状:** `No matching distribution found for python-markdown>=3.5.0`

**解决:** 使用 Python 3.11，或手动安装其他依赖（跳过 python-markdown）

### 3. npm install 超时

**症状:** `ETIMEDOUT` 或长时间卡住

**解决:**
```bash
npm config set registry https://registry.npmmirror.com
npm install
```

### 4. 无法连接后端

**症状:** 前端页面显示 "无法连接" 或 API 请求失败

**检查:**
1. 后端服务是否运行 (`uvicorn` 终端是否还在)
2. 后端端口是否正确 (`http://localhost:8000`)
3. 前端 `src/utils/request.ts` 中的 `baseURL` 配置

### 5. Qdrant 连接错误

**症状:** 启动时显示 `Create collection error: Unexpected Response: 502`

**解决:** 这是正常警告，不影响基础功能。如需向量检索，启动 Qdrant Docker 容器。

---

## 🏗️ 生产环境部署

### 后端生产部署

```bash
# 使用 gunicorn 多进程部署
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 桌面端构建

```bash
cd desktop
npm run build
# 构建产物在 dist/ 目录
```

---

## 📁 项目结构

```
WWD/
├── backend/              # 后端服务
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── core/        # 核心引擎 (Harness, LLM Router)
│   │   ├── services/    # 业务逻辑
│   │   └── models/      # 数据模型
│   ├── requirements.txt # Python 依赖
│   └── .env             # 环境变量 (需创建)
│
├── desktop/             # 桌面端 (Vue + Tauri)
│   ├── src/
│   │   ├── views/       # 页面组件
│   │   ├── components/  # 通用组件
│   │   └── utils/       # 工具函数
│   ├── package.json
│   └── vite.config.ts
│
└── docs/                # 项目文档
```

---

## 🔗 相关文档

- [项目计划](./docs/PROJECT_PLAN.md)
- [API 文档](./docs/API_DESIGN.md) (运行时: http://localhost:8000/docs)
- [数据库设计](./docs/DATABASE_DESIGN.md)

---

## 📞 技术支持

遇到问题请提供：
1. 操作系统版本 (macOS/Windows/Linux)
2. Python 版本 (`python --version`)
3. Node 版本 (`node --version`)
4. 完整的错误截图

---

**最后更新**: 2026-03-27
