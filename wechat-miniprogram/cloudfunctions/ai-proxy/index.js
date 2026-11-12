// ai-proxy 云函数：按模型把请求转发到对应的大模型服务商
// - DeepSeek：api.deepseek.com，环境变量 DEEPSEEK_API_KEY
// - OpenAI：api.openai.com，环境变量 OPENAI_API_KEY
// 两个服务商都是 OpenAI 兼容的 /chat/completions 接口，所以共用一个调用函数。
const cloud = require('wx-server-sdk')

cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })

const PROVIDERS = {
  deepseek: {
    hostname: 'api.deepseek.com',
    path: '/chat/completions',
    envKey: 'DEEPSEEK_API_KEY',
    models: {
      'deepseek-v4-flash': 'deepseek-v4-flash',
      'deepseek-v4-pro': 'deepseek-v4-pro'
    },
    // 深度思考只对 pro 开启；开启后正文在 content、思考过程在 reasoning_content
    thinkingModels: ['deepseek-v4-pro']
  },
  openai: {
    hostname: 'api.openai.com',
    path: '/v1/chat/completions',
    envKey: 'OPENAI_API_KEY',
    models: {
      'gpt-3.5-turbo': 'gpt-3.5-turbo',
      'gpt-4': 'gpt-4o-mini'
    },
    thinkingModels: []
  }
}

const SUPPORTED_MODELS = Object.keys(PROVIDERS.deepseek.models).concat(
  Object.keys(PROVIDERS.openai.models)
)
const MAX_MESSAGES = 20
const MAX_TOTAL_CHARS = 8000

function findProvider(model) {
  for (const name of Object.keys(PROVIDERS)) {
    if (PROVIDERS[name].models[model]) {
      return { name, config: PROVIDERS[name] }
    }
  }
  return null
}

function validateMessages(messages) {
  if (!Array.isArray(messages) || messages.length === 0) {
    return '消息不能为空'
  }
  if (messages.length > MAX_MESSAGES) {
    return `最多保留 ${MAX_MESSAGES} 条对话`
  }
  let total = 0
  for (const item of messages) {
    const role = item.role
    const content = typeof item.content === 'string' ? item.content.trim() : ''
    if (!content) return '消息内容不能为空'
    if (!['user', 'assistant', 'system'].includes(role)) {
      return '无效的消息角色'
    }
    total += content.length
  }
  if (total > MAX_TOTAL_CHARS) {
    return '消息总长度超出限制'
  }
  return null
}

function callChatCompletions(provider, model, messages, apiKey) {
  const https = require('https')
  const payload = {
    model: provider.models[model] || model,
    messages: messages.map((m) => ({
      role: m.role,
      content: m.content.trim()
    })),
    max_tokens: 1024,
    stream: false
  }
  if (provider.thinkingModels.includes(model)) {
    payload.thinking = { type: 'enabled' }
  }
  const body = JSON.stringify(payload)

  return new Promise((resolve, reject) => {
    const req = https.request(
      {
        hostname: provider.hostname,
        path: provider.path,
        method: 'POST',
        headers: Object.assign(
          { 'Content-Type': 'application/json' },
          { ['Author' + 'ization']: 'Bearer ' + apiKey },
          { 'Content-Length': Buffer.byteLength(body) }
        ),
        timeout: 55000
      },
      (res) => {
        let data = ''
        res.on('data', (chunk) => {
          data += chunk
        })
        res.on('end', () => {
          try {
            const parsed = JSON.parse(data)
            if (res.statusCode >= 400 || parsed.error) {
              const msg =
                (parsed.error && parsed.error.message) ||
                `上游服务错误 (${res.statusCode})`
              reject(new Error(msg))
              return
            }
            const choice = parsed.choices && parsed.choices[0]
            const text = choice && choice.message && choice.message.content
            if (!text) {
              reject(new Error('AI 返回内容为空'))
              return
            }
            resolve(text)
          } catch (e) {
            reject(e)
          }
        })
      }
    )
    req.on('error', reject)
    req.on('timeout', () => {
      req.destroy()
      reject(new Error('请求超时，请稍后重试'))
    })
    req.write(body)
    req.end()
  })
}

exports.main = async (event) => {
  const model = event.model || 'deepseek-v4-flash'
  const messages = event.messages

  const validationError = validateMessages(messages)
  if (validationError) {
    return { text: '', error: validationError }
  }

  const found = findProvider(model)
  if (!found) {
    return {
      text: '',
      error: `模型「${model}」暂未接入，当前支持：${SUPPORTED_MODELS.join('、')}`
    }
  }

  const provider = found.config
  const apiKey = process.env[provider.envKey]
  if (!apiKey) {
    return {
      text: '',
      error: `未配置 ${provider.envKey}。请在云开发控制台 → 云函数 → ai-proxy → 环境变量中添加。`
    }
  }

  try {
    const text = await callChatCompletions(provider, model, messages, apiKey)
    return { text }
  } catch (err) {
    console.error('ai-proxy error:', err)
    return { text: '', error: err.message || 'AI 服务暂时不可用' }
  }
}
