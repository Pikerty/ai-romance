const util = require('../../utils/util.js')
const { chatWithAI } = require('../../utils/ai.js')

Page({
  data: {
    messages: [],
    inputValue: '',
    isLoading: false,
    currentModel: 'deepseek-v4-flash',
    aiModels: [],
    nightModeClass: '',
    isNightMode: false
  },

  onLoad() {
    const app = getApp()
    this.setData({
      aiModels: app.globalData.aiModels,
      currentModel: app.globalData.currentModel
    })
    this.initConversation()
    util.applyNightMode(this)
  },

  onShow() {
    util.applyNightMode(this)
  },

  goSettings() {
    wx.navigateTo({ url: '/pages/settings/settings' })
  },

  initConversation() {
    this.setData({ messages: [] })
  },

  onInputChange(e) {
    this.setData({ inputValue: e.detail.value })
  },

  async sendMessage() {
    const { inputValue, messages, currentModel } = this.data
    if (!inputValue.trim() || this.data.isLoading) return

    this.setData({ isLoading: true })

    try {
      const userMessage = { role: 'user', content: inputValue.trim() }
      const updatedMessages = [...messages, userMessage]
      this.setData({ messages: updatedMessages, inputValue: '' })

      const response = await chatWithAI(updatedMessages, currentModel)
      const aiMessage = { role: 'assistant', content: response }
      this.setData({ messages: [...updatedMessages, aiMessage] })
    } catch (err) {
      wx.showToast({
        title: err.message || '请求失败，请重试',
        icon: 'none',
        duration: 2500
      })
    } finally {
      this.setData({ isLoading: false })
    }
  },

  switchModel(e) {
    const model = e.currentTarget.dataset.model
    util.setCurrentModel(model)
    this.setData({ currentModel: model })
    const item = this.data.aiModels.find((m) => m.id === model)
    wx.showToast({
      title: item ? `已切换至 ${item.name}` : '模型已切换',
      icon: 'none'
    })
  }
})
