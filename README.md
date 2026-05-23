# AI 恋爱伴侣 App 🌸

一个基于 Flask + Claude API 的 AI 虚拟恋爱对话应用。

## 功能
- 4 个不同性格的 AI 恋人（小雅、陈默、晴天、苏沫）
- 保留对话历史，上下文连续
- 快捷话题按钮
- 支持 Enter 发送

## 快速启动

### 第一步：安装依赖
```bash
pip install -r requirements.txt
```

### 第二步：设置 API Key
**Windows：**
```cmd
set ANTHROPIC_API_KEY=你的APIKey
```

**Mac / Linux：**
```bash
export ANTHROPIC_API_KEY=你的APIKey
```

> 获取 API Key：https://console.anthropic.com/

### 第三步：运行
```bash
python app.py
```

### 第四步：打开浏览器
访问 http://localhost:5000

## 项目结构
```
ai_romance/
├── app.py               # Flask 后端
├── requirements.txt     # 依赖
├── README.md
└── templates/
    └── index.html       # 前端页面
```

## 部署到服务器（可选）
使用 gunicorn 部署：
```bash
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```
