# AI 恋爱伴侣 🌸

一个基于 Flask + Claude API 的 AI 虚拟恋爱对话应用，支持 4 个不同性格的 AI 伴侣、流式输出、完整对话历史。

## 功能特性

- 4 个性格各异的 AI 伴侣：小雅 🌸、陈默 🎸、晴天 ☀️、苏沫 🌙
- 流式输出，文字逐字出现更像真人打字
- 保留对话历史，上下文连续
- 快捷话题按钮
- Enter 键快速发送

## 快速启动

### 1. 克隆项目

\```bash
git clone https://github.com/Pikerty/ai-romance.git
cd ai-romance
\```

### 2. 安装依赖

\```bash
pip install -r requirements.txt
\```

### 3. 配置 API Key

\```bash
cp .env.example .env
\```


\```
ANTHROPIC_API_KEY=AQ.Ab8RN6KBvbsrd-030yaqIJ3jxJP6EfQIppSzalhXNUUBDnfpBg
\```

> 获取 API Key：https://console.anthropic.com/

### 4. 运行

\```bash
python app.py
\```

访问 http://localhost:5000

## 项目结构

\```
ai-romance/
├── app.py               # Flask 后端（含流式输出）
├── requirements.txt     # 依赖（锁定版本）
├── Procfile             # 云部署配置
├── .env.example         # 环境变量模板
├── .gitignore           # Git 忽略规则
├── LICENSE              # MIT 开源协议
├── README.md
└── templates/
    └── index.html       # 前端页面
\```

## 部署到云平台

### Railway（推荐，免费额度）

1. 前往 https://railway.app 注册
2. 新建项目 → 从 GitHub 导入此仓库
3. 在 Variables 面板添加：`ANTHROPIC_API_KEY=你的Key`
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

## License

MIT © Pikerty
