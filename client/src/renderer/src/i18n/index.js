import { reactive, computed } from 'vue'
import zhCN from './zh-CN.js'
import en from './en.js'

const locales = { 'zh-CN': zhCN, en }

const STORAGE_KEY = 'autodev:locale'

function loadLocale() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved && locales[saved]) return saved
  } catch {}
  // Detect browser language
  const navLang = (navigator.language || 'en').toLowerCase()
  if (navLang.startsWith('zh')) return 'zh-CN'
  return 'en'
}

const state = reactive({
  locale: loadLocale(),
})

export const currentLocale = computed(() => state.locale)

export function setLocale(locale) {
  if (!locales[locale]) return
  state.locale = locale
  try { localStorage.setItem(STORAGE_KEY, locale) } catch {}
}

export function getAvailableLocales() {
  return [
    { key: 'zh-CN', label: '中文' },
    { key: 'en', label: 'English' },
  ]
}

/**
 * Resolve nested key like 'settings.language.title' to its localized string.
 * Supports {variable} interpolation.
 */
export function t(key, params = {}) {
  const messages = locales[state.locale] || en
  const parts = key.split('.')
  let value = messages
  for (const part of parts) {
    if (value == null) break
    value = value[part]
  }
  if (typeof value !== 'string') {
    console.warn(`[i18n] Missing translation: ${key} (${state.locale})`)
    return key
  }
  // Interpolate {var} placeholders
  return value.replace(/\{(\w+)\}/g, (_, name) =>
    params[name] !== undefined ? String(params[name]) : `{${name}}`
  )
}

/**
 * Vue plugin: exposes $t globally and provides reactive locale state.
 */
export default {
  install(app) {
    app.config.globalProperties.$t = t
    app.config.globalProperties.$locale = currentLocale
    app.provide('i18n', { t, locale: currentLocale, setLocale, getAvailableLocales })
  },
}

export { t as $t }
