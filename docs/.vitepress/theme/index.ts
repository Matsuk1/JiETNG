// .vitepress/theme/index.ts
import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import { h } from 'vue'
import GoogleTranslate from './GoogleTranslate.vue'
import LanguageRedirect from './LanguageRedirect.vue'
import './custom.css'

export default {
  extends: DefaultTheme,
  Layout() {
    return h(DefaultTheme.Layout, null, {
      'layout-top': () => h(LanguageRedirect),
      'nav-bar-content-after': () => h(GoogleTranslate)
    })
  }
} satisfies Theme
