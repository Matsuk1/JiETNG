---
layout: home
title: JiETNG · maimai B50 / レート内訳 · JP / INTL スコア管理
titleTemplate: false

hero:
  name: "JiETNG"
  text: "maimai DX<br>スコア管理"
  tagline: 国内版 JP と海外版 INTL に対応 · B50 / Best 50 / Recent 50 / DX Rating / レート内訳 / ブックマークレット取り込み
  image:
    src: /hero-image.svg
    alt: JiETNG Logo
  actions:
    - theme: brand
      text: はじめる
      link: /guide/getting-started
    - theme: alt
      text: ブックマークレット
      link: /bookmarklet
    - theme: alt
      text: GitHub
      link: https://github.com/Matsuk1/JiETNG

features:
  - icon: 📊
    title: スコア画像
    details: B50、B40、Best 35/15、All Best、AP Best、FDX Best、Recent 50、Ideal Best に対応。
    link: /commands/record
    linkText: コマンドを見る

  - icon: 🔎
    title: 詳細フィルター
    details: レベル、定数、達成率、DX スコア、譜面種別、難易度、バージョン、ページで絞り込み。
    link: /features/search
    linkText: 検索機能

  - icon: 🧩
    title: 2つのデータ元
    details: SEGA アカウント連携による同期、または Import Token とブックマークレットによる取り込み。
    link: /bookmarklet
    linkText: ブックマークレット

  - icon: 🏆
    title: 進捗管理
    details: プレート進捗、レベル別目標、未達成・未プレイ・達成済みの絞り込みに対応。
    link: /commands/
    linkText: コマンド一覧

  - icon: 🌐
    title: JP / INTL
    details: 国内版と海外版の maimai NET に対応。中文、English、日本語のドキュメントを用意。
    link: /guide/getting-started
    linkText: クイックスタート

  - icon: 🔐
    title: エクスポートと API
    details: 設定ページ、JSON/XML エクスポート、Import Token、開発者 Token、権限 API を提供。
    link: /developer-api
    linkText: API
---

<style>
.VPFeature { cursor: pointer; }
.VPFeature:hover .icon {
  transform: scale(1.12) rotate(4deg);
  transition: transform 0.2s ease;
}
.vp-doc h2 {
  border-top: none;
  padding-top: 24px;
}
</style>

## JiETNG とは

JiETNG は **maimai でらっくす / maimai DX** 向けのスコア管理 Bot です。SEGA アカウント連携で maimai NET から同期することも、ブラウザのブックマークレットで取得した加工済みデータを Import Token でアップロードすることもできます。

主な機能は B50 / Best 50 画像、Recent 50、DX Rating とレート内訳、楽曲/譜面検索、レベル/定数リスト、プレート進捗、フレンド成績、近くの店舗検索、JSON/XML エクスポート、開発者 API、Import Token です。

`maimai b50`、`maimai レート内訳`、`maimai DX Rating`、`maimai スコア管理` のような検索から見つけやすいツールを目指しています。

## クイックスタート

1. JiETNG LINE Bot を追加します。
2. 個別チャットで `bind` を送信します。SEGA アカウント連携、または Import Token モードを選べます。
3. `maimai update` で公式データを同期するか、[ブックマークレット](/bookmarklet)で公式サイトから取り込みます。
4. `b50`、`record`、`13.6 records`、`真極 achievement` などを試します。

[ガイドを読む →](/guide/getting-started)

## サポート

- [コマンド一覧](/commands/)
- [開発者 API](/developer-api)
- [GitHub Issues](https://github.com/Matsuk1/JiETNG/issues)
- [Discord](https://discord.gg/NXxFn9T8Xz)
