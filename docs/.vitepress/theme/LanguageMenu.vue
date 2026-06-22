<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useData } from 'vitepress'

const props = defineProps<{
  surface: 'navbar' | 'screen'
}>()

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

    const existingScript = document.getElementById('google-translate-script')
    if (existingScript) return

    const script = document.createElement('script')
    script.id = 'google-translate-script'
    script.src = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit'
    script.async = true
    script.onerror = () => reject(new Error('Google Translate failed to load.'))
    document.head.appendChild(script)
  })

  return googleTranslateLoader
}

const { hash, lang, localeIndex, page, site, theme } = useData()
const menu = ref<HTMLElement | null>(null)
const isOpen = ref(false)
const translateStatus = ref('')
const translateElementId = `google_translate_${props.surface}`

const currentLocale = computed(() => {
  const locale = site.value.locales[localeIndex.value]
  return {
    label: locale?.label || 'Language',
    link: locale?.link || (localeIndex.value === 'root' ? '/' : `/${localeIndex.value}/`)
  }
})

const localeLinks = computed(() => {
  const currentLink = currentLocale.value.link
  const relativePath = page.value.relativePath
    .slice(currentLink.length - 1)
    .replace(/(^|\/)index\.md$/, '$1')
    .replace(/\.md$/, '')

  return Object.entries(site.value.locales).flatMap(([key, locale]) => {
    const link = locale.link || (key === 'root' ? '/' : `/${key}/`)
    if (locale.label === currentLocale.value.label) return []

    const target = theme.value.i18nRouting === false
      ? link
      : `${link.replace(/\/$/, '')}/${relativePath}`.replace(/\/$/, '/')

    return { label: locale.label, link: `${target}${hash.value}` }
  })
})

const copy = computed(() => {
  if (lang.value.startsWith('ja')) {
    return { site: 'サイトの言語', more: 'その他の言語', unavailable: '翻訳を読み込めませんでした。' }
  }
  if (lang.value.startsWith('en')) {
    return { site: 'Site language', more: 'More languages', unavailable: 'Translation could not be loaded.' }
  }
  return { site: '网站语言', more: '更多语言', unavailable: '翻译服务加载失败。' }
})

async function openMenu() {
  isOpen.value = !isOpen.value
  if (!isOpen.value) return

  await nextTick()
  const element = document.getElementById(translateElementId)
  if (!element || element.childElementCount) return

  try {
    const TranslateElement = await loadGoogleTranslate()
    new TranslateElement({
      pageLanguage: document.documentElement.lang || 'zh-CN',
      includedLanguages: 'zh-CN,zh-TW,en,ja,ko,fr,de,es,th,vi,id',
      autoDisplay: false
    }, translateElementId)
  } catch {
    translateStatus.value = copy.value.unavailable
  }
}

function closeOnOutsideClick(event: MouseEvent) {
  if (menu.value && !menu.value.contains(event.target as Node)) isOpen.value = false
}

function closeOnEscape(event: KeyboardEvent) {
  if (event.key === 'Escape') isOpen.value = false
}

onMounted(() => {
  document.addEventListener('click', closeOnOutsideClick)
  document.addEventListener('keydown', closeOnEscape)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', closeOnOutsideClick)
  document.removeEventListener('keydown', closeOnEscape)
})
</script>

<template>
  <div ref="menu" class="language-menu" :class="`language-menu--${surface}`">
    <button
      class="language-menu-trigger"
      type="button"
      :aria-expanded="isOpen"
      :aria-controls="`${translateElementId}-panel`"
      @click.stop="openMenu"
    >
      <span class="vpi-languages" aria-hidden="true" />
      <span>{{ currentLocale.label }}</span>
      <span class="vpi-chevron-down language-menu-chevron" aria-hidden="true" />
    </button>

    <div
      v-show="isOpen"
      :id="`${translateElementId}-panel`"
      class="language-menu-panel"
    >
      <section class="language-menu-section">
        <p class="language-menu-title">{{ copy.site }}</p>
        <a
          v-for="locale in localeLinks"
          :key="locale.link"
          class="language-menu-link"
          :href="locale.link"
        >
          {{ locale.label }}
        </a>
      </section>

      <section class="language-menu-section language-menu-section--translate">
        <p class="language-menu-title">{{ copy.more }}</p>
        <div :id="translateElementId" class="google-translate-control" />
        <p v-if="translateStatus" class="language-menu-status">{{ translateStatus }}</p>
      </section>
    </div>
  </div>
</template>
