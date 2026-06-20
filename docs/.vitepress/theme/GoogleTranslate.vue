<script setup lang="ts">
import { onMounted } from 'vue'

declare global {
  interface Window {
    googleTranslateElementInit?: () => void
    google?: {
      translate?: {
        TranslateElement?: new (
          options: Record<string, unknown>,
          element: string
        ) => void
      }
    }
  }
}

onMounted(() => {
  const id = 'google_translate_element'
  window.googleTranslateElementInit = () => {
    const TranslateElement = window.google?.translate?.TranslateElement
    if (!TranslateElement || !document.getElementById(id)) return
    new TranslateElement({
      pageLanguage: 'zh-CN',
      includedLanguages: 'zh-CN,zh-TW,en,ja,ko,fr,de,es,th,vi,id',
      autoDisplay: false
    }, id)
  }

  if (document.getElementById('google-translate-script')) return
  const script = document.createElement('script')
  script.id = 'google-translate-script'
  script.src = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit'
  script.async = true
  document.head.appendChild(script)
})
</script>

<template>
  <div class="google-translate-wrap">
    <span class="google-translate-label">Translate</span>
    <div id="google_translate_element"></div>
  </div>
</template>
