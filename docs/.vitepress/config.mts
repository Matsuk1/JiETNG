import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

// https://vitepress.dev/reference/site-config
export default withMermaid(defineConfig({
  title: "JiETNG",
  description: "JiETNG · 舞萌DX 查分器 / maimai でらっくす スコア管理ボット — 支持日服与国际服的 LINE 机器人，免费 Rating 计算器和 B50 成绩图生成。",
  titleTemplate: ":title | JiETNG · 舞萌DX 查分器 / maimai でらっくす Score Tracker",

  cleanUrls: true,

  // 排除文件
  srcExclude: ['**/README.md'],

  // Base URL配置
  // GitHub Pages (username.github.io/JiETNG/): 使用 '/JiETNG/'
  // 自定义域名 (docs.jietng.com): 使用 '/'
  base: '/',

  // Sitemap 配置（用于 SEO）
  sitemap: {
    hostname: 'https://jietng.matsuk1.com'
  },

  // Markdown 配置
  markdown: {
    theme: {
      light: 'github-light',
      dark: 'github-dark'
    }
  },

  // 主题配置
  themeConfig: {
    logo: '/logo.svg',

    // 导航栏
    nav: [
      { text: '首页', link: '/' },
      { text: '指南', link: '/guide/getting-started' },
      { text: '功能', link: '/features/search' },
      { text: '命令', link: '/commands/basic' },
      { text: '网页书签', link: '/bookmarklet' }
    ],

    // 侧边栏
    sidebar: [
      {
        text: '开始使用',
        items: [
          { text: '快速开始', link: '/guide/getting-started' },
          { text: '在线体验', link: '/demo' },
          { text: '网页书签工具', link: '/bookmarklet' }
        ]
      },
      {
        text: '命令参考',
        items: [
          { text: '命令大全', link: '/commands/' },
          { text: '基础命令', link: '/commands/basic' },
          { text: '成绩命令', link: '/commands/record' }
        ]
      },
      {
        text: '功能特性',
        items: [
          { text: '成绩查询', link: '/features/search' }
        ]
      },
      {
        text: '更多',
        items: [
          { text: '常见问题', link: '/more/faq' },
          { text: '隐私政策', link: '/more/privacy' },
          { text: '支持', link: '/more/support' },
          { text: '许可证', link: '/more/license' },
          { text: '开发者 API', link: '/developer-api' }
        ]
      }
    ],

    // 社交链接
    socialLinks: [
      { icon: 'github', link: 'https://github.com/Matsuk1/JiETNG' }
    ],

    // 页脚
    footer: {
      message: '让每一次游玩都有迹可循',
      copyright: 'Copyright © 2025 Matsuki. 保留所有权利。'
    },

    // 搜索
    search: {
      provider: 'local'
    },

    // 编辑链接
    editLink: {
      pattern: 'https://github.com/Matsuk1/JiETNG/edit/main/docs/:path',
      text: '在 GitHub 上编辑此页'
    },

    // 最后更新时间
    lastUpdated: {
      text: '最后更新',
      formatOptions: {
        dateStyle: 'short',
        timeStyle: 'short'
      }
    }
  },

  // 多语言支持
  locales: {
    root: {
      label: '简体中文',
      lang: 'zh-CN',
      description: '舞萌DX 查分器 — JiETNG 是支持日服 (JP) 与国际服 (INTL) 的『maimai でらっくす』查分机器人 / LINE Bot，免费 Rating 计算器、Best 50 / B50 成绩图生成、牌子进度追踪、Recent 50 历史查询。'
    },
    en: {
      label: 'English',
      lang: 'en',
      link: '/en/',
      description: 'JiETNG -『maimai でらっくす』score management bot for LINE supporting both Japanese and International servers.',
      themeConfig: {
        nav: [
          { text: 'Home', link: '/en/' },
          { text: 'Guide', link: '/en/guide/getting-started' },
          { text: 'Features', link: '/en/features/search' },
          { text: 'Commands', link: '/en/commands/basic' },
          { text: 'Bookmarklet', link: '/en/bookmarklet' }
        ],
        sidebar: [
          {
            text: 'Getting Started',
            items: [
              { text: 'Quick Start', link: '/en/guide/getting-started' },
              { text: 'Try It Online', link: '/en/demo' },
              { text: 'Bookmarklet Tool', link: '/en/bookmarklet' }
            ]
          },
          {
            text: 'Commands',
            items: [
              { text: 'Complete Reference', link: '/en/commands/' },
              { text: 'Basic Commands', link: '/en/commands/basic' },
              { text: 'Record Commands', link: '/en/commands/record' }
            ]
          },
          {
            text: 'Features',
            items: [
              { text: 'Score Search', link: '/en/features/search' }
            ]
          },
          {
            text: 'More',
            items: [
              { text: 'FAQ', link: '/en/more/faq' },
              { text: 'Privacy', link: '/en/more/privacy' },
              { text: 'Support', link: '/en/more/support' },
              { text: 'License', link: '/en/more/license' },
              { text: 'Developer API', link: '/en/developer-api' }
            ]
          }
        ],
        editLink: {
          pattern: 'https://github.com/Matsuk1/JiETNG/edit/main/docs/:path',
          text: 'Edit this page on GitHub'
        },
        lastUpdated: {
          text: 'Updated at',
          formatOptions: {
            dateStyle: 'short',
            timeStyle: 'short'
          }
        },
        footer: {
          message: 'Making every play count',
          copyright: 'Copyright © 2025 Matsuki. All Rights Reserved.'
        }
      }
    },
    ja: {
      label: '日本語',
      lang: 'ja',
      link: '/ja/',
      description: 'JiETNG - 国内版と海外版の両方に対応した『maimai でらっくす』スコア管理ボット。無料のレーティング計算機とベスト50チャート生成器。',
      themeConfig: {
        nav: [
          { text: 'ホーム', link: '/ja/' },
          { text: 'ガイド', link: '/ja/guide/getting-started' },
          { text: '機能', link: '/ja/features/search' },
          { text: 'コマンド', link: '/ja/commands/basic' },
          { text: 'ブックマークレット', link: '/ja/bookmarklet' }
        ],
        sidebar: [
          {
            text: '始めに',
            items: [
              { text: 'クイックスタート', link: '/ja/guide/getting-started' },
              { text: '体験する', link: '/ja/demo' },
              { text: 'ブックマークレット', link: '/ja/bookmarklet' }
            ]
          },
          {
            text: 'コマンド',
            items: [
              { text: 'コマンド一覧', link: '/ja/commands/' },
              { text: '基本コマンド', link: '/ja/commands/basic' },
              { text: 'レコードコマンド', link: '/ja/commands/record' }
            ]
          },
          {
            text: '機能',
            items: [
              { text: '楽曲検索', link: '/ja/features/search' }
            ]
          },
          {
            text: 'その他',
            items: [
              { text: 'よくある質問', link: '/ja/more/faq' },
              { text: 'プライバシー', link: '/ja/more/privacy' },
              { text: 'サポート', link: '/ja/more/support' },
              { text: 'ライセンス', link: '/ja/more/license' },
              { text: '開発者 API', link: '/ja/developer-api' }
            ]
          }
        ],
        editLink: {
          pattern: 'https://github.com/Matsuk1/JiETNG/edit/main/docs/:path',
          text: 'GitHub でこのページを編集'
        },
        lastUpdated: {
          text: '最終更新',
          formatOptions: {
            dateStyle: 'short',
            timeStyle: 'short'
          }
        },
        footer: {
          message: 'すべてのプレイを記録に残そう',
          copyright: 'Copyright © 2025 Matsuki. All Rights Reserved.'
        }
      }
    }
  },

  // 头部meta标签
  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/logo.svg' }],
    ['link', { rel: 'icon', type: 'image/png', href: '/favicon.ico' }],
    ['link', { rel: 'apple-touch-icon', href: '/logo.svg' }],
    ['meta', { name: 'theme-color', content: '#2563eb' }],

    // 站长验证（中文搜索引擎；申请到 token 后填进 content）
    ['meta', { name: 'google-site-verification', content: '7wQ3HIU-rk6iSNe441mvYPgkZwuotIB3PlOx6r3xOm8' }],
    // ['meta', { name: 'baidu-site-verification', content: 'codeva-XXXXXXXX' }],   // https://ziyuan.baidu.com/
    // ['meta', { name: 'msvalidate.01',           content: 'XXXXXXXXXXXXXXXX' }],   // https://www.bing.com/webmasters
    // ['meta', { name: '360-site-verification',   content: 'XXXXXXXXXXXXXXXX' }],
    // ['meta', { name: 'sogou_site_verification', content: 'XXXXXXXXXXXXXXXX' }],

    // SEO meta 标签（含中/日/英三语长尾，覆盖典型搜索词）
    ['meta', { name: 'keywords', content: [
      // 核心 - 中文（最常搜）
      '舞萌DX查分器', '舞萌查分器', 'maimai查分器', 'maimai 查分', 'maimai dx 查分器',
      '舞萌DX', '舞萌', '舞萌dx', 'maimaiDX bot',
      '舞萌国服', '舞萌日服', '舞萌国际服', 'maimai 日服', 'maimai 国际服', '日版', '国际版', '日服', '国际服',
      '舞萌成绩', 'B50 查分', 'b50', 'best 50', 'rating 计算', 'Rating 查询', '牌子进度', '极将神舞舞', '段位查询',
      // 核心 - 日文
      'maimai でらっくす', 'maimai DX', 'maimaiでらっくす', 'スコア管理', 'スコア管理ボット', 'レーティング計算',
      'ベスト50', 'ベストスコア', 'maimaiDXボット', '日本サーバー', '国際サーバー', '海外版',
      // 核心 - 英文
      'maimai', 'maimai bot', 'maimai dx score tracker', 'score tracker', 'rating calculator',
      'best 50 generator', 'LINE bot', 'rhythm game', 'arcade game tracker',
      'Japanese server', 'International server', 'JP server', 'INTL server',
      // 项目名
      'JiETNG', 'JiETNG bot',
    ].join(', ') }],
    ['meta', { name: 'description', content: 'JiETNG · 舞萌DX 查分器 — 支持日服 (JP) 与国际服 (INTL) 的『maimai でらっくす』查分机器人 / LINE Bot，免费 Rating 计算器、Best 50 / B50 成绩图生成、牌子进度追踪、Recent 50 历史查询。' }],
    ['meta', { name: 'author', content: 'Matsuki' }],

    // Open Graph
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:site_name', content: 'JiETNG' }],
    ['meta', { property: 'og:title', content: 'JiETNG · 舞萌DX 查分器 / maimai でらっくす Score Tracker' }],
    ['meta', { property: 'og:description', content: '舞萌DX 查分器 LINE 机器人，支持日服 / 国际服，免费 Rating 计算与 B50 成绩图生成。' }],
    ['meta', { property: 'og:image', content: 'https://jietng.matsuk1.com/og-image.png' }],
    ['meta', { property: 'og:image:width', content: '1200' }],
    ['meta', { property: 'og:image:height', content: '630' }],
    ['meta', { property: 'og:image:type', content: 'image/png' }],
    ['meta', { property: 'og:url', content: 'https://jietng.matsuk1.com' }],

    // Twitter Card
    ['meta', { name: 'twitter:card', content: 'summary_large_image' }],
    ['meta', { name: 'twitter:title', content: 'JiETNG · 舞萌DX 查分器 / maimai でらっくす Score Tracker' }],
    ['meta', { name: 'twitter:description', content: '舞萌DX 查分器 LINE 机器人，支持日服 / 国际服，免费 Rating 计算与 B50 成绩图生成。' }],
    ['meta', { name: 'twitter:image', content: 'https://jietng.matsuk1.com/og-image.png' }],

    // JSON-LD 结构化数据（让 Google 知道这是个 WebApplication，不是普通博客）
    ['script', { type: 'application/ld+json' }, JSON.stringify({
      '@context': 'https://schema.org',
      '@type': 'WebApplication',
      'name': 'JiETNG',
      'alternateName': ['舞萌DX 查分器', 'maimai DX Score Tracker', 'maimai でらっくす スコア管理ボット'],
      'url': 'https://jietng.matsuk1.com',
      'description': '舞萌DX 查分器 LINE 机器人，支持 maimai でらっくす 日服与国际服的成绩查询、Rating 计算、Best 50 图生成、牌子进度追踪。',
      'applicationCategory': 'GameApplication',
      'operatingSystem': 'Any (LINE)',
      'inLanguage': ['zh-CN', 'ja', 'en'],
      'offers': {
        '@type': 'Offer',
        'price': '0',
        'priceCurrency': 'JPY'
      },
      'author': {
        '@type': 'Person',
        'name': 'Matsuki',
        'url': 'https://github.com/Matsuk1'
      }
    }) ]
  ],

  // Mermaid 配置
  mermaid: {
    // 参考 https://mermaid.js.org/config/setup/modules/mermaidAPI.html#mermaidapi-configuration-defaults
  }
}))
