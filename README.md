# AI 恋爱伴侣 🌸

一个基于 Flask + Claude API 的 AI 虚拟恋爱对话应用，支持 4 个不同性格的 AI 伴侣、流式输出、完整对话历史。

本仓库包含两个版本：**网页版**（根目录，Flask 应用，已部署到 Render）和**微信小程序版**（`wechat-miniprogram/` 目录，微信云开发 + DeepSeek）。

## 功能特性

- 4 个性格各异的 AI 伴侣：小雅 🌸、陈默 🎸、晴天 ☀️、苏沫 🌙
- 流式输出，文字逐字出现更像真人打字
- 保留对话历史，上下文连续
- 快捷话题按钮
- Enter 键快速发送

## 微信小程序版（wechat-miniprogram/）

微信小程序前端 + 云函数 `ai-proxy` 的 AI 聊天小程序，2026-11-12 接入 DeepSeek：

- 云函数按模型转发：DeepSeek（`deepseek-v4-flash` 默认、`deepseek-v4-pro` 深度思考）走 `DEEPSEEK_API_KEY`；GPT（`gpt-3.5-turbo`、`gpt-4`）走 `OPENAI_API_KEY`
- 前端支持模型切换、夜间模式；对话最多带最近 12 条上下文
- 使用前需在云开发控制台为 ai-proxy 配置环境变量，并上传部署云函数，详见 `wechat-miniprogram/README.md`

## 快速启动

### 1. 克隆项目

```bash
git clone https://github.com/Pikerty/ai-romance.git
cd ai-romance
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

```bash
cp .env.example .env
```

```
ANTHROPIC_API_KEY=你的 Anthropic API Key
```

> 获取 API Key：https://console.anthropic.com/

### 4. 运行

```bash
python app.py
```

访问 http://localhost:5000

## 项目结构

```
ai-romance/
├── app.py               # Flask 后端（含流式输出）
├── requirements.txt     # 依赖（锁定版本）
├── Procfile             # 云部署配置
├── .env.example         # 环境变量模板
├── .gitignore           # Git 忽略规则
├── LICENSE              # MIT 开源协议
├── README.md
├── templates/
│   └── index.html       # 前端页面
└── wechat-miniprogram/  # 微信小程序版（云函数 ai-proxy，已接入 DeepSeek）
```

## 部署到云平台

### Railway（推荐，免费额度）

1. 前往 https://railway.app 注册
2. 新建项目 → 从 GitHub 导入此仓库
3. 在 Variables 面板添加：`ANTHROPIC_API_KEY`
4. 自动部署完成，获得公网 URL

### Render

1. 前往 https://render.com 注册
2. New → Web Service → 连接此仓库
3. Start Command：`gunicorn app:app`
4. 在 Environment 添加 `ANTHROPIC_API_KEY`

## 注意事项

- **不要**将 `.env` 文件提交到 Git
- 生产环境请确保 `FLASK_DEBUG` 未设置或设为 `false`
- API Key 请妥善保管，泄露后立即在 Anthropic 控制台重置

## 更新日志

### 2026-11-12

- 新增微信小程序版（`wechat-miniprogram/`）：小程序前端 + 云函数 ai-proxy，已接入 DeepSeek（deepseek-v4-flash / deepseek-v4-pro），保留 GPT 备选；代码由用户上传的 zip 整理入库，未把无关项目（亲密日记 ZL、腾讯云 Agent-UI 模板）混入
- 小程序审查结论：原代码只接了 OpenAI 且仓库内没有任何 key，聊天实际上调不通；无流式输出、对话不保存、无人设系统，详见 `wechat-miniprogram/README.md`

## License

cdcas © Pikerty
