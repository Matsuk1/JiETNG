// .vitepress/theme/index.ts
import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import { h } from 'vue'
import LanguageMenu from './LanguageMenu.vue'
import './custom.css'

export default {
  extends: DefaultTheme,
  Layout() {
    return h(DefaultTheme.Layout, null, {
      'nav-bar-content-after': () => h(LanguageMenu, { surface: 'navbar' }),
      'nav-screen-content-after': () => h(LanguageMenu, { surface: 'screen' })
    })
  }
} satisfies Theme
