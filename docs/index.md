---
layout: home
title: 舞萌DX 查分器 · maimai B50 / レート内訳 · JiETNG
titleTemplate: false

hero:
  name: "JiETNG"
  text: "舞萌DX 查分器<br>maimai でらっくす"
  tagline: 支持日服 JP 与国际服 INTL · B50 / Best 50 / Recent 50 / DX Rating / レート内訳 / 网页书签导入
  image:
    src: /hero-image.svg
    alt: JiETNG Logo
  actions:
    - theme: brand
      text: 开始使用
      link: /zh/guide/getting-started
    - theme: alt
      text: 网页书签
      link: /zh/bookmarklet
    - theme: alt
      text: GitHub
      link: https://github.com/Matsuk1/JiETNG

features:
  - icon: 📊
    title: 成绩图生成
    details: 支持 B50、B40、Best 35/15、All Best、AP Best、FDX Best、Recent 50 和理想分数图。
    link: /zh/commands/record
    linkText: 查看成绩命令

  - icon: 🔎
    title: 精准查询
    details: 可按等级、定数、达成率、DX 分数、谱面类型、难度、版本与分页筛选成绩。
    link: /zh/features/search
    linkText: 查看筛选方式

  - icon: 🧩
    title: 两种数据来源
    details: 可绑定 SEGA 账号自动同步，也可使用 Import Token 与网页书签上传已加工成绩数据。
    link: /zh/bookmarklet
    linkText: 查看书签工具

  - icon: 🏆
    title: 牌子与进度
    details: 支持版本达成状况、等级达成进度、未游玩/未达成/已达成筛选。
    link: /zh/commands/
    linkText: 查看命令大全

  - icon: 🌐
    title: 多语言与双版本
    details: 文档与主要交互支持中文、英文、日文；数据侧支持 JP 与 INTL。
    link: /zh/guide/getting-started
    linkText: 快速开始

  - icon: 🔐
    title: 权限与导出
    details: 支持用户设置页、数据导出 JSON/XML、开发者 Token 和用户授权。
    link: /zh/developer-api
    linkText: 查看 API
---

<style>
.VPFeature {
  cursor: pointer;
}

.VPFeature:hover .icon {
  transform: scale(1.12) rotate(4deg);
  transition: transform 0.2s ease;
}

.vp-doc h2 {
  border-top: none;
  padding-top: 24px;
}
</style>

## JiETNG 是什么？

JiETNG 是面向 **maimai でらっくす / 舞萌DX** 的查分器和 LINE 成绩管理机器人。它可以从官方 maimai NET 同步成绩，也可以通过网页书签读取当前浏览器会话并上传加工后的成绩数据。

项目当前重点功能包括：B50 / Best 50 成绩图、Recent 50、DX Rating 与レート内訳查看、歌曲/谱面查询、等级与定数列表、版本达成状况、好友成绩查询、附近机厅查询、成绩导出、开发者 API 与 Import Token。

如果你在找“舞萌查分器”“maimai b50”“舞萌DX B50”“レート内訳”或“maimai DX Rating”工具，JiETNG 的目标就是把这些查询集中到一个可在 LINE 和网页书签中使用的服务里。

## 快速开始

1. 添加 JiETNG LINE Bot。
2. 私聊发送 `bind`，选择绑定 SEGA 账号，或选择 Import Token 导入模式。
3. 发送 `maimai update` 同步官方数据，或使用[网页书签工具](/zh/bookmarklet)从官方网页读取并上传成绩。
4. 发送 `b50`、`record`、`13.6のレコードリスト`、`真極の達成状況` 等命令查看结果。

[阅读快速开始 →](/zh/guide/getting-started)

## 社区与支持

- [命令参考](/zh/commands/)
- [开发者 API](/zh/developer-api)
- [GitHub Issues](https://github.com/Matsuk1/JiETNG/issues)
- [Discord](https://discord.gg/NXxFn9T8Xz)
