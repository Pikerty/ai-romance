const CLOUD_ENV = 'cloud1-6gnc71q3b00b52ba'

App({
  globalData: {
    aiModels: [
      { id: 'deepseek-v4-flash', name: 'DeepSeek V4 Flash' },
      { id: 'deepseek-v4-pro', name: 'DeepSeek V4 Pro（深度思考）' },
      { id: 'gpt-3.5-turbo', name: 'GPT-3.5' },
      { id: 'gpt-4', name: 'GPT-4' }
    ],
    currentModel: 'deepseek-v4-flash',
    conversationHistory: [],
    userInfo: null,
    isNightMode: false
  },

  onLaunch() {
    if (!wx.cloud) {
      console.error('请使用 2.2.3 或以上的基础库以使用云能力')
      return
    }

    wx.cloud.init({
      env: CLOUD_ENV,
      traceUser: true
    })

    const config = wx.getStorageSync('userConfig') || {}
    if (typeof config.isNightMode === 'boolean') {
      this.globalData.isNightMode = config.isNightMode
    }
    if (config.currentModel) {
      this.globalData.currentModel = config.currentModel
    }

    this.checkUpdate()

    wx.onError((err) => {
      console.error('全局错误:', err)
    })
  },

  saveUserConfig(patch) {
    const config = {
      ...wx.getStorageSync('userConfig'),
      isNightMode: this.globalData.isNightMode,
      currentModel: this.globalData.currentModel,
      ...patch
    }
    wx.setStorageSync('userConfig', config)
  },

  checkUpdate() {
    if (!wx.canIUse('getUpdateManager')) return
    const updateManager = wx.getUpdateManager()
    updateManager.onCheckForUpdate((res) => {
      if (!res.hasUpdate) return
      updateManager.onUpdateReady(() => {
        wx.showModal({
          title: '更新提示',
          content: '新版本已准备好，是否重启应用？',
          success: (modalRes) => {
            if (modalRes.confirm) updateManager.applyUpdate()
          }
        })
      })
    })
  }
})
