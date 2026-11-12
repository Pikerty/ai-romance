function applyNightMode(page) {
  const app = getApp()
  const isNight = !!app.globalData.isNightMode
  page.setData({
    nightModeClass: isNight ? 'night-mode' : '',
    isNightMode: isNight
  })
}

function setNightMode(enabled) {
  const app = getApp()
  app.globalData.isNightMode = enabled
  app.saveUserConfig({ isNightMode: enabled })
}

function setCurrentModel(model) {
  const app = getApp()
  app.globalData.currentModel = model
  app.saveUserConfig({ currentModel: model })
}

module.exports = {
  applyNightMode,
  setNightMode,
  setCurrentModel
}
