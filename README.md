# 🔮 沙斯亚尔语翻译器 / Shathyar Translator

<div align="center">

**探索虚空语言的奥秘，在人类文字与沙斯亚尔语之间架起桥梁**
*Explore the mysteries of the Void language, bridging Human Language and Shathyar*

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.0+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2+-blue.svg)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2+-blue.svg)](https://typescriptlang.org)

---

*"在无尽虚空中，语言是唯一的真理... / In the endless Void, language is the only truth..."*

</div>

## ✨ 项目简介 / Project Overview

这是一个魔兽世界粉丝项目，提供中文与沙斯亚尔语（虚空领主的虚构语言）之间的双向翻译服务。项目结合了官方词典和AI智能生成，为玩家提供沉浸式的语言探索体验。

*A World of Warcraft fan project providing bidirectional translation between Chinese and Shathyar (the fictional language of the Void Lords). The application combines official dictionary lookup with AI-powered generation to create an immersive linguistic exploration experience.*

### 🌟 核心特性 / Key Features

- **🔄 双向翻译 / Bidirectional Translation**
  - 中文 → 沙斯亚尔语（AI智能生成）
  - 沙斯亚尔语 → 中文（官方词典匹配）

- **🧠 AI驱动 / AI-Powered**
  - 使用火山引擎豆包模型进行智能翻译
  - 基于官方词典语境优化生成质量
  - 支持用户编辑确认机制

- **⚡ 配额管理 / Quota System**
  - 每IP每日500次翻译限制
  - 实时"魔力值"显示
  - UTC零点自动重置

- **🎨 神秘主题 / Mystical Theme**
  - 克苏鲁风深色界面设计
  - 棕黑卷轴配色方案
  - 沉浸式错误消息和动画

- **🛡️ 企业级功能 / Enterprise Features**
  - 完整的速率限制和熔断保护
  - 请求日志和分析统计
  - 健康检查和监控端点
  - CORS跨域支持

## 🏗️ 技术架构 / Architecture

### 后端 Backend
- **框架**: FastAPI + SQLAlchemy + Pydantic
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **AI服务**: 火山引擎豆包 (OpenAI兼容)
- **缓存**: 请求级响应缓存
- **限流**: 基于IP的令牌桶算法

### 前端 Frontend
- **框架**: React 18 + TypeScript + Vite
- **状态管理**: TanStack React Query
- **样式**: Tailwind CSS + 自定义神秘主题
- **表单**: React Hook Form + Zod验证
- **通知**: React Hot Toast

### 数据模型 Data Models
```
📊 translation_entries     # 用户生成翻译记录
📚 official_dictionary     # 官方词典 (shasiyaer.csv)
👤 user_sessions          # IP会话和配额管理
📝 translation_requests   # 请求日志和统计分析
```

## 🚀 快速开始 / Quick Start

### 环境要求 Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### 1. 克隆项目 Clone Repository
```bash
git clone https://github.com/your-username/SnathYarTranslation.git
cd SnathYarTranslation
```

### 2. 后端设置 Backend Setup
```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python scripts/init_db.py

# 启动后端服务
python -m src.main
```

### 3. 前端设置 Frontend Setup
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 4. 访问应用 Access Application
- **前端界面**: http://localhost:5173
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 📁 项目结构 / Project Structure

```
SnathYarTranslation/
├── 📁 backend/                 # 后端服务
│   ├── src/
│   │   ├── api/               # FastAPI路由
│   │   ├── models/            # SQLAlchemy数据模型
│   │   ├── services/          # 业务逻辑层
│   │   └── main.py           # 应用入口
│   ├── tests/                # 测试套件
│   └── requirements.txt      # Python依赖
├── 📁 frontend/               # 前端应用
│   ├── src/
│   │   ├── components/       # React组件
│   │   ├── pages/           # 页面组件
│   │   ├── services/        # API客户端
│   │   └── styles/          # 样式文件
│   └── package.json         # Node.js依赖
├── 📄 shasiyaer.csv          # 官方词典数据
├── 📄 CLAUDE.md              # 项目说明文档
└── 📄 README.md              # 本文件
```

## 🔧 配置选项 / Configuration

### 环境变量 Environment Variables

```bash
# 后端配置
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
DATABASE_URL=sqlite:///./shathyar.db

# AI服务配置
VOLCENGINE_API_KEY=your_api_key
VOLCENGINE_MODEL=ep-20241125110318-xxxxx

# CORS配置
FRONTEND_ORIGIN=https://your-domain.com
CORS_ALLOW_ORIGINS=https://a.com,https://b.com

# 功能开关
SHATHYAR_AI_MOCK=false        # 启用AI模拟模式
RATE_LIMIT_ENABLED=true       # 启用速率限制
```

## 📊 API接口 / API Endpoints

### 核心翻译接口
```http
POST /api/v1/translate
Content-Type: application/json

{
  "text": "你好，世界！",
  "source_language": "chinese"
}
```

### 配额查询
```http
GET /api/v1/session/quota
```

### 词典搜索
```http
GET /api/v1/dictionary/search?query=hello&limit=10
```

### 详细API文档
启动服务后访问 `/docs` 查看完整的Swagger文档。

## 🧪 测试 / Testing

### 后端测试
```bash
cd backend
python -m pytest tests/ -v
```

### 前端测试
```bash
cd frontend
npm run test
npm run test:coverage
```

### 端到端测试
```bash
# 确保后端和前端都在运行
python scripts/smoke_chain.py
```

## 🔐 安全特性 / Security Features

- **输入验证**: 全面的数据验证和清理
- **速率限制**: 防止API滥用
- **CORS保护**: 配置化的跨域访问控制
- **prompt注入防护**: AI服务安全措施
- **敏感信息保护**: API密钥环境变量管理

## 🎯 性能指标 / Performance Metrics

- **词典查询**: <100ms (P95)
- **缓存翻译**: <200ms (P95)
- **AI翻译**: <5000ms (P95)
- **并发支持**: 10+ 用户同时使用
- **成本优化**: 通过缓存降低70-80%成本

## 🛠️ 开发工具 / Development Tools

### 代码质量
```bash
# Python代码检查
cd backend
python -m flake8 src/
python -m black src/

# TypeScript代码检查
cd frontend
npm run lint
npm run lint:fix
```

### 数据库管理
```bash
# 重新初始化数据库
python backend/scripts/init_db.py

# 导入词典数据
python -c "from backend.src.services.dictionary_reader import DictionaryReader; ..."
```

## 🤝 贡献指南 / Contributing

1. **Fork项目**并创建特性分支
2. **遵循代码规范**：使用Black格式化Python代码，ESLint检查TypeScript
3. **编写测试**：确保新功能有对应测试用例
4. **提交PR**：描述清楚变更内容和测试结果

## 📜 许可证 / License

本项目采用 [MIT许可证](https://opensource.org/licenses/MIT)。

## 🙏 致谢 / Acknowledgments

- **暴雪娱乐 Blizzard Entertainment**: 魔兽世界宇宙和沙斯亚尔语言设定
- **社区贡献者**: shasiyaer.csv官方词典数据整理
- **开源社区**: FastAPI、React及相关生态系统

---

<div align="center">

**🔮 愿虚空指引你的话语 / May the Void guide your words 🔮**

Made with ❤️ for World of Warcraft fans and language enthusiasts

*[⭐ 如果这个项目对你有帮助，请给个星标！ / Star this repo if it helps you!](https://github.com/your-username/SnathYarTranslation)*

</div>