# Mac 后端安装 - 简易指南

如果自动脚本失败，请按以下步骤手动安装：

## Step 1: 确保在 backend 目录
```bash
cd WWD/backend
pwd  # 确认路径正确
```

## Step 2: 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate
```

## Step 3: 逐个安装（这样可以看到哪个包出错）

### 3.1 核心框架
```bash
pip install fastapi uvicorn
```

### 3.2 Pydantic
```bash
pip install pydantic pydantic-settings
```

### 3.3 LangChain
```bash
pip install langchain langchain-openai langgraph
```

### 3.4 其他工具
```bash
pip install python-multipart python-jose passlib pyyaml python-markdown
```

### 3.5 可选（暂时不装也行）
```bash
pip install qdrant-client redis python-docx
```

## Step 4: 测试安装
```bash
python3 -c "import fastapi; print('FastAPI OK')"
python3 -c "import langchain; print('LangChain OK')"
```

## Step 5: 启动服务
```bash
uvicorn app.main:app --reload
```

---

## ⚠️ 常见问题

### 问题 1: pip 安装报错 SSL
```bash
# 尝试使用 --trusted-host
pip install fastapi --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

### 问题 2: 权限错误
```bash
# 不要加 sudo，确保在虚拟环境里
which python3  # 应该显示 venv 路径
```

### 问题 3: Python 版本太低
```bash
# 检查版本
python3 --version  # 需要 3.9+

# 如果太低，用 brew 安装新版
brew install python@3.11
```

---

## 🚀 快速测试

启动后访问:
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

---

如果还有问题，把具体的错误信息发给我！