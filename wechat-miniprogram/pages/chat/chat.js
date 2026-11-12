const util = require('../../utils/util.js')
const { chatWithAI } = require('../../utils/ai.js')

Page({
  data: {
    messages: [],
    inputValue: '',
    nightModeClass: '',
    isNightMode: false,
    isLoading: false,
    currentModel: 'deepseek-v4-flash'
  },

  onLoad() {
    const app = getApp()
    this.setData({ currentModel: app.globalData.currentModel })
    util.applyNightMode(this)
  },

  onShow() {
    util.applyNightMode(this)
  },

  toggleNightMode(e) {
    const isNightMode = e && e.detail ? e.detail.value : !this.data.isNightMode
    util.setNightMode(isNightMode)
    util.applyNightMode(this)
  },

  handleInput(e) {
    this.setData({ inputValue: e.detail.value })
  },

  async sendMessage() {
    const message = this.data.inputValue.trim()
    if (!message || this.data.isLoading) return

    const userMsg = {
      role: 'user',
      content: message,
      isUser: true,
      time: new Date().toLocaleTimeString()
    }
    const historyForApi = this.data.messages
      .filter((m) => m.role)
      .concat([{ role: 'user', content: message }])

    this.setData({
      messages: [...this.data.messages, userMsg],
      inputValue: '',
      isLoading: true
    })

    try {
      const reply = await chatWithAI(historyForApi, this.data.currentModel)
      const aiMsg = {
        role: 'assistant',
        content: reply,
        isUser: false,
        time: new Date().toLocaleTimeString()
      }
      this.setData({
        messages: [...this.data.messages, aiMsg]
      })
    } catch (err) {
      wx.showToast({
        title: err.message || '请求失败',
        icon: 'none',
        duration: 2500
      })
    } finally {
      this.setData({ isLoading: false })
    }
  }
})
