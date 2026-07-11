<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useData, useRoute } from 'vitepress'

type LocaleCode = 'ja' | 'zh' | 'en'

const STORAGE_KEY = 'jietng-docs-locale'
const DISMISSED_KEY = 'jietng-docs-locale-dismissed'

const route = useRoute()
const { lang } = useData()
const dismissed = ref(true)
const preferredLocale = ref<LocaleCode>('ja')

const localeMeta: Record<LocaleCode, { label: string; prefix: string }> = {
  ja: { label: '日本語', prefix: '' },
  zh: { label: '简体中文', prefix: '/zh' },
  en: { label: 'English', prefix: '/en' }
}

const currentLocale = computed<LocaleCode>(() => {
  if (lang.value.startsWith('zh')) return 'zh'
  if (lang.value.startsWith('en')) return 'en'
  return 'ja'
})

const copy = computed(() => {
  if (currentLocale.value === 'zh') {
    return {
      message: '检测到你的浏览器语言更适合',
      action: '切换',
      dismiss: '保持当前语言'
    }
  }
  if (currentLocale.value === 'en') {
    return {
      message: 'Your browser language looks better suited for',
      action: 'Switch',
      dismiss: 'Keep current language'
    }
  }
  return {
    message: 'ブラウザの言語に合わせて',
    action: '切り替える',
    dismiss: 'このまま表示'
  }
})

const shouldShow = computed(() => (
  !dismissed.value &&
  preferredLocale.value !== currentLocale.value
))

const targetUrl = computed(() => localizePath(preferredLocale.value))

function detectBrowserLocale(): LocaleCode {
  const languages = navigator.languages?.length ? navigator.languages : [navigator.language]
  for (const raw of languages) {
    const value = raw.toLowerCase()
    if (value.startsWith('zh')) return 'zh'
    if (value.startsWith('en')) return 'en'
    if (value.startsWith('ja')) return 'ja'
  }
  return 'ja'
}

function pathLocale(pathname: string): LocaleCode {
  if (pathname === '/zh' || pathname.startsWith('/zh/')) return 'zh'
  if (pathname === '/en' || pathname.startsWith('/en/')) return 'en'
  return 'ja'
}

function stripLocale(pathname: string): string {
  if (pathname === '/zh' || pathname === '/en') return '/'
  if (pathname.startsWith('/zh/')) return pathname.slice(3) || '/'
  if (pathname.startsWith('/en/')) return pathname.slice(3) || '/'
  return pathname || '/'
}

function localizePath(locale: LocaleCode): string {
  const basePath = stripLocale(window.location.pathname)
  const prefix = localeMeta[locale].prefix
  const localizedPath = prefix ? `${prefix}${basePath === '/' ? '/' : basePath}` : basePath
  return `${localizedPath}${window.location.search}${window.location.hash}`
}

function isRootEntry(pathname: string): boolean {
  return pathname === '/' || pathname === '/index.html'
}

function isLocale(value: string | null): value is LocaleCode {
  return value === 'ja' || value === 'zh' || value === 'en'
}

function rememberLocale(locale: LocaleCode) {
  localStorage.setItem(STORAGE_KEY, locale)
  sessionStorage.removeItem(DISMISSED_KEY)
}

function switchLocale() {
  rememberLocale(preferredLocale.value)
  window.location.href = targetUrl.value
}

function dismissPrompt() {
  dismissed.value = true
  sessionStorage.setItem(DISMISSED_KEY, '1')
}

function syncPreference() {
  const stored = localStorage.getItem(STORAGE_KEY)
  preferredLocale.value = isLocale(stored) ? stored : detectBrowserLocale()
  dismissed.value = sessionStorage.getItem(DISMISSED_KEY) === '1'
}

onMounted(() => {
  syncPreference()

  const stored = localStorage.getItem(STORAGE_KEY)
  const browserLocale = detectBrowserLocale()
  const activeLocale = pathLocale(window.location.pathname)

  if (!stored && isRootEntry(window.location.pathname) && browserLocale !== activeLocale) {
    preferredLocale.value = browserLocale
    window.location.replace(localizePath(browserLocale))
    return
  }

  if (isLocale(stored) && stored !== activeLocale && isRootEntry(window.location.pathname)) {
    preferredLocale.value = stored
    window.location.replace(localizePath(stored))
  }
})

watch(() => route.path, () => {
  syncPreference()
})
</script>

<template>
  <div v-if="shouldShow" class="language-redirect">
    <span>{{ copy.message }} {{ localeMeta[preferredLocale].label }}。</span>
    <button type="button" class="language-redirect-action" @click="switchLocale">
      {{ copy.action }}
    </button>
    <button type="button" class="language-redirect-dismiss" @click="dismissPrompt">
      {{ copy.dismiss }}
    </button>
  </div>
</template>
