# Lang-Agent

LangChain + LangGraph 构建的智能体项目，支持 CLI 与 Web 聊天页面。

## 项目结构

- `app/agent.py`: 智能体核心逻辑与工具编排
- `app/main.py`: 命令行交互入口
- `app/api/server.py`: FastAPI 应用入口
- `app/api/routes/chat.py`: 聊天与健康检查路由
- `app/api/services/chat_service.py`: 业务服务层（调用 Agent）
- `app/api/schemas/chat.py`: API 请求/响应模型
- `frontend/`: React + Vite 前端聊天页面

## 启动方式（MVP）

### 1) 启动后端

```bash
pip install -r requirements.txt
uvicorn app.api.server:app --reload --host 0.0.0.0 --port 8000
```

如需跨域白名单可配置：

```bash
export API_ALLOW_ORIGINS="http://localhost:5173"
```

### 2) 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认请求 `http://127.0.0.1:8000`，如需修改可设置：

```bash
export VITE_API_BASE_URL="http://127.0.0.1:8000"
```

## API 说明（MVP）

- `GET /api/health`: 健康检查
- `POST /api/chat`: 发送一轮问答
  - 请求体:
    - `user_id`: 用户 ID（用于记忆隔离）
    - `thread_id`: 会话 ID（用于会话上下文）
    - `message`: 用户输入
