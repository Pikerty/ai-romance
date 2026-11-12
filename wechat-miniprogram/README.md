# ai-romance 微信小程序版

微信小程序前端 + 微信云开发云函数的 AI 聊天小程序（appid 见 project.config.json，云环境 cloud1-d5gbjght3845fd3b1）。

## 架构

- 页面：`pages/index`（聊天 + 模型切换）、`pages/chat`（聊天页）、`pages/settings`（夜间模式 + 默认模型）
- 前端通过 `utils/ai.js` 调用云函数 `ai-proxy`，最多带最近 12 条上下文
- 云函数 `cloudfunctions/ai-proxy` 按模型转发到对应服务商（OpenAI 兼容的 /chat/completions 接口）：
  - **DeepSeek**（`api.deepseek.com`）：`deepseek-v4-flash`（默认）、`deepseek-v4-pro`（开启深度思考）
  - **OpenAI**（`api.openai.com`）：`gpt-3.5-turbo`、`gpt-4`（实际调用 gpt-4o-mini）

## 使用前配置（缺一不可）

1. 在 [DeepSeek 开放平台](https://platform.deepseek.com) 创建 API key 并充值（按量付费，无永久免费额度；key 只显示一次，自己保存，不要发到聊天里）
2. 云开发控制台 → 云函数 → ai-proxy → 环境变量，添加 `DEEPSEEK_API_KEY`（用 GPT 再加 `OPENAI_API_KEY`）
3. 微信开发者工具里右键 `cloudfunctions/ai-proxy` → 「上传并部署：云端安装依赖」
4. 导入本目录为小程序项目，真机或模拟器测试

## 已知未完成（截至 2026-11-12）

- 没有人设/角色系统，与网页版 ai-romance 的定位（AI 恋爱聊天）不一致，目前只是通用 AI 助手
- 对话不落库、不保存，重启小程序即丢失；`models/` 数据层未实现
- 没有流式输出，回复需等整段生成完（云函数超时上限 60 秒）
- 首页和 chat 页是两套重复的聊天实现，还没合并
