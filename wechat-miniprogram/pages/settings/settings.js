const util = require('../../utils/util.js')

Page({
  data: {
    isNightMode: false,
    currentModel: '',
    aiModels: []
  },

  onLoad() {
    const app = getApp()
    this.setData({
      isNightMode: app.globalData.isNightMode,
      currentModel: app.globalData.currentModel,
      aiModels: app.globalData.aiModels
    })
  },

  toggleNightMode(e) {
    const isNightMode = e.detail.value
    util.setNightMode(isNightMode)
    this.setData({ isNightMode })
  },

  onModelChange(e) {
    const model = e.detail.value
    util.setCurrentModel(model)
    this.setData({ currentModel: model })
    wx.showToast({ title: '默认模型已更新', icon: 'none' })
  }
})
