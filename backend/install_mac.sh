#!/bin/bash
# Mac 安装脚本 - 政府公文写作助手后端

set -e

echo "=========================================="
echo "政府公文写作助手 - Mac 安装脚本"
echo "=========================================="

# 检查 Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 python3，请先安装:"
    echo "   brew install python3"
    exit 1
fi

echo "✓ Python3 版本: $(python3 --version)"

# 检查是否在 backend 目录
if [ ! -f "requirements.txt" ]; then
    echo "❌ 请在 backend 目录下运行此脚本"
    exit 1
fi

# 创建虚拟环境
echo ""
echo "1. 创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 升级 pip
echo ""
echo "2. 升级 pip..."
pip install --upgrade pip setuptools wheel

# 安装依赖
echo ""
echo "3. 安装依赖（这可能需要几分钟）..."

# 先安装核心依赖
echo "   - 安装 FastAPI..."
pip install fastapi uvicorn pydantic pydantic-settings || true

echo "   - 安装 LangChain..."
pip install langchain langchain-openai langgraph || true

echo "   - 安装其他依赖..."
pip install python-multipart python-jose passlib pyyaml python-markdown || true

echo "   - 安装可选依赖..."
pip install qdrant-client redis python-docx pytest httpx || true

echo "   - 尝试安装 deepagents（如失败可跳过）..."
pip install deepagents || echo "⚠️ deepagents 安装失败，继续..."

# 验证安装
echo ""
echo "4. 验证安装..."
python3 -c "import fastapi; print(f'✓ FastAPI {fastapi.__version__}')" || echo "⚠️ FastAPI 可能未正确安装"
python3 -c "import langchain; print(f'✓ LangChain {langchain.__version__}')" || echo "⚠️ LangChain 可能未正确安装"

echo ""
echo "=========================================="
echo "✅ 安装完成！"
echo "=========================================="
echo ""
echo "下一步:"
echo "1. 配置 API Key:"
echo "   cp .env.example .env"
echo "   # 编辑 .env 填入 KIMI_API_KEY"
echo ""
echo "2. 启动服务:"
echo "   uvicorn app.main:app --reload"
echo ""
echo "3. 访问 API 文档:"
echo "   http://localhost:8000/docs"
echo ""

# 保持虚拟环境激活状态
echo "💡 提示: 虚拟环境已激活，可以直接运行 uvicorn"
exec bash