<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useData } from 'vitepress'

type TranslateElementConstructor = new (
  options: Record<string, unknown>,
  element: string
) => void

declare global {
  interface Window {
    googleTranslateElementInit?: () => void
    google?: {
      translate?: {
        TranslateElement?: TranslateElementConstructor
      }
    }
  }
}

let googleTranslateLoader: Promise<TranslateElementConstructor> | undefined

function loadGoogleTranslate() {
  if (window.google?.translate?.TranslateElement) {
    return Promise.resolve(window.google.translate.TranslateElement)
  }

  if (googleTranslateLoader) return googleTranslateLoader

  googleTranslateLoader = new Promise((resolve, reject) => {
    window.googleTranslateElementInit = () => {
      const TranslateElement = window.google?.translate?.TranslateElement
      if (TranslateElement) resolve(TranslateElement)
      else reject(new Error('Google Translate did not initialize.'))
    }

    const existingScript = document.getElementById('google-translate-script') as HTMLScriptElement | null
    const script = existingScript || document.createElement('script')
    script.id = 'google-translate-script'
    script.src = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit'
    script.async = true
    script.onerror = () => reject(new Error('Google Translate failed to load.'))
    if (!existingScript) document.head.appendChild(script)
  })

  return googleTranslateLoader
}

const status = ref('')
const { lang } = useData()
const navTargetReady = ref(false)
const screenTargetReady = ref(false)
let observer: MutationObserver | undefined

const copy = computed(() => {
  if (lang.value.startsWith('ja')) {
    return {
      more: 'その他の言語',
      unavailable: '翻訳を読み込めませんでした。',
      fallback: 'Google Translate で開く'
    }
  }
  if (lang.value.startsWith('en')) {
    return {
      more: 'More languages',
      unavailable: 'Translation unavailable',
      fallback: 'Open in Google Translate'
    }
  }
  return {
    more: '更多语言',
    unavailable: '翻译服务加载失败。',
    fallback: '用 Google 翻译打开'
  }
})

const fallbackUrl = computed(() => {
  if (typeof window === 'undefined') return 'https://translate.google.com/'
  const target = window.location.href
  return `https://translate.google.com/translate?sl=auto&tl=en&u=${encodeURIComponent(target)}`
})

function updateTargets() {
  navTargetReady.value = !!document.querySelector('.VPNavBarTranslations .items')
  screenTargetReady.value = !!document.querySelector('.VPNavScreenTranslations .list')
}

function pageLanguage() {
  if (lang.value.startsWith('zh')) return 'zh-CN'
  if (lang.value.startsWith('en')) return 'en'
  if (lang.value.startsWith('ja')) return 'ja'
  return document.documentElement.lang || 'ja'
}

async function mountTranslateControl(id: string) {
  await nextTick()
  const element = document.getElementById(id)
  if (!element || element.childElementCount) return

  try {
    const TranslateElement = await loadGoogleTranslate()
    new TranslateElement({
      pageLanguage: pageLanguage(),
      includedLanguages: 'ja,en,zh-CN,zh-TW,ko,fr,de,es,th,vi,id',
      autoDisplay: false
    }, id)
  } catch {
    status.value = copy.value.unavailable
  }
}

onMounted(() => {
  updateTargets()
  observer = new MutationObserver(() => updateTargets())
  observer.observe(document.body, { childList: true, subtree: true })
  void mountTranslateControl('google_translate_nav')
  void mountTranslateControl('google_translate_screen')
})

watch(navTargetReady, (ready) => {
  if (ready) void mountTranslateControl('google_translate_nav')
})

watch(screenTargetReady, (ready) => {
  if (ready) void mountTranslateControl('google_translate_screen')
})

onBeforeUnmount(() => {
  observer?.disconnect()
})
</script>

<template>
  <Teleport v-if="navTargetReady" to=".VPNavBarTranslations .items">
    <div class="google-translate-menu">
      <p class="google-translate-title">{{ copy.more }}</p>
      <div id="google_translate_nav" class="google-translate-control" />
      <p v-if="status" class="google-translate-status">{{ status }}</p>
      <a
        v-if="status"
        class="google-translate-fallback"
        :href="fallbackUrl"
        target="_blank"
        rel="noopener noreferrer"
      >{{ copy.fallback }}</a>
    </div>
  </Teleport>

  <Teleport v-if="screenTargetReady" to=".VPNavScreenTranslations .list">
    <li class="google-translate-screen-item">
      <p class="google-translate-title">{{ copy.more }}</p>
      <div id="google_translate_screen" class="google-translate-control" />
      <p v-if="status" class="google-translate-status">{{ status }}</p>
      <a
        v-if="status"
        class="google-translate-fallback"
        :href="fallbackUrl"
        target="_blank"
        rel="noopener noreferrer"
      >{{ copy.fallback }}</a>
    </li>
  </Teleport>
</template>
