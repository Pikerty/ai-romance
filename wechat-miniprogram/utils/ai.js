const MAX_CONTEXT_MESSAGES = 12

/**
 * 调用云函数 ai-proxy，统一返回助手回复文本
 */
async function chatWithAI(messages, model) {
  const context = (messages || []).slice(-MAX_CONTEXT_MESSAGES)
  const res = await wx.cloud.callFunction({
    name: 'ai-proxy',
    data: { model, messages: context }
  })

  const result = res.result || {}
  if (result.error) {
    throw new Error(result.error)
  }
  if (!result.text) {
    throw new Error('AI 未返回有效内容')
  }
  return result.text
}

module.exports = {
  chatWithAI,
  MAX_CONTEXT_MESSAGES
}
