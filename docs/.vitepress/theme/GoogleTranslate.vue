<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
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

    const script = document.createElement('script')
    script.id = 'google-translate-script'
    script.src = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit'
    script.async = true
    script.onerror = () => reject(new Error('Google Translate failed to load.'))
    document.head.appendChild(script)
  })

  return googleTranslateLoader
}

const status = ref('')
const { lang } = useData()

const copy = computed(() => {
  if (lang.value.startsWith('ja')) {
    return { more: 'その他の言語', unavailable: '翻訳を読み込めませんでした。' }
  }
  if (lang.value.startsWith('en')) {
    return { more: 'More languages', unavailable: 'Translation unavailable' }
  }
  return { more: '更多语言', unavailable: '翻译服务加载失败。' }
})

async function mountTranslateControl(id: string) {
  await nextTick()
  const element = document.getElementById(id)
  if (!element || element.childElementCount) return

  try {
    const TranslateElement = await loadGoogleTranslate()
    new TranslateElement({
      pageLanguage: document.documentElement.lang || 'zh-CN',
      includedLanguages: 'zh-TW,ko,fr,de,es,th,vi,id',
      autoDisplay: false
    }, id)
  } catch {
    status.value = copy.value.unavailable
  }
}

onMounted(() => {
  void mountTranslateControl('google_translate_nav')
  void mountTranslateControl('google_translate_screen')
})
</script>

<template>
  <Teleport to=".VPNavBarTranslations .items">
    <div class="google-translate-menu">
      <p class="google-translate-title">{{ copy.more }}</p>
      <div id="google_translate_nav" class="google-translate-control" />
      <p v-if="status" class="google-translate-status">{{ status }}</p>
    </div>
  </Teleport>

  <Teleport to=".VPNavScreenTranslations .list">
    <li class="google-translate-screen-item">
      <p class="google-translate-title">{{ copy.more }}</p>
      <div id="google_translate_screen" class="google-translate-control" />
      <p v-if="status" class="google-translate-status">{{ status }}</p>
    </li>
  </Teleport>
</template>
