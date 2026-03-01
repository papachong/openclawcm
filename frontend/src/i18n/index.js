import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN.js'
import enUS from './locales/en-US.js'

// Detect browser language, fallback to localStorage, then default to zh-CN
function getDefaultLocale() {
  // 1. Check localStorage
  const saved = localStorage.getItem('locale')
  if (saved && ['zh-CN', 'en-US'].includes(saved)) {
    return saved
  }
  // 2. Check browser language
  const browserLang = navigator.language || navigator.userLanguage
  if (browserLang.startsWith('en')) {
    return 'en-US'
  }
  // 3. Default to Chinese
  return 'zh-CN'
}

const i18n = createI18n({
  legacy: false, // Use Composition API
  locale: getDefaultLocale(),
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS,
  },
})

export default i18n

// Helper to set locale and persist
export function setLocale(locale) {
  i18n.global.locale.value = locale
  localStorage.setItem('locale', locale)
  // Update document language attribute
  document.documentElement.setAttribute('lang', locale)
}

export function getLocale() {
  return i18n.global.locale.value
}
