---
title: maimai DX コマンド一覧
description: JiETNG の maimai B50、スコア管理、レート内訳、プレート進捗、楽曲検索、エクスポート、Import Token コマンド一覧。
---

# JiETNG コマンド一覧

現在のコマンド登録に基づいた一覧です。特記がない限り大文字小文字は区別されません。

## アカウントとシステム

| コマンド | 説明 |
|----------|------|
| `bind` | SEGA 連携または Import Token モードのリンクを作成 |
| `rebind` | SEGA パスワード、サーバー、Aime を更新 |
| `settings` | 設定と Import Token 管理 |
| `profile` / `getme` | プロフィールと連携状態 |
| `unbind` / `unbind confirm` | 保存データを削除 |
| `maimai update` / `update` | maimai NET から同期 |
| `export json` / `export xml` | 加工済み成績を出力 |
| `donate` | 支援情報 |
| `status` | Bot 稼働状態 |

`bind`、`rebind`、`settings`、`update`、`export`、`unbind` は自分自身にのみ作用します。

## B 系スコア画像

| コマンド | 説明 |
|----------|------|
| `b50` / `best50` | Best 35 + Best 15 |
| `b40` / `best40` | 旧 Rating 構成 |
| `b35` / `best35` | 旧曲 Best 35 |
| `b15` / `best15` | 新曲 Best 15 |
| `ab35` / `allb35` | All Best 35 |
| `ab50` / `allb50` | All Best 50 |
| `apb50` / `ap50` | AP/AP+ Best 50 |
| `fdxb50` / `fdx50` | FDX/FDX+ Best 50 |
| `rct50` / `r50` | Recent 50 |
| `idealb50` / `idlb50` | Ideal Best 50 |
| `unknown` | バージョン不明楽曲 |

`-lv`、`-ra`、`-scr`、`-dx`、`-star`、`-diff`、`-ver`、`-type`、`-page`、`-times` を追加できます。

## 楽曲と成績

| 形式 | 説明 |
|------|------|
| `[曲名] record` / `[曲名] song-record` / `[曲名]のレコード` | 単曲個人成績 |
| `search-record <楽曲ID>` | 6 桁 ID で個人成績 |
| `[曲名] info` / `[曲名] song-info` / `[曲名]ってどんな曲` | 楽曲情報 |
| `search <楽曲ID>` | ID で楽曲情報 |
| `calc-song <楽曲ID>` | 達成率計算 |
| `artist <キーワード> [ページ]` | アーティスト検索 |
| `designer <キーワード> [ページ]` | 譜面制作者検索 |

## リストと進捗

| 形式 | 説明 |
|------|------|
| `[レベル/定数] records [ページ]` | 成績リスト |
| `[レベル/定数] record-list [ページ]` | 成績リスト |
| `[レベル/定数]のレコードリスト [ページ]` | 成績リスト |
| `[レベル/定数] level-list` | レベル/定数リスト |
| `[レベル][目標] progress` | レベル目標進捗 |
| `[レベル][目標] 進捗` / `[レベル][目標] 进度` | 同上 |

目標：`s`、`s+`、`ss`、`ss+`、`sss`、`sss+`、`fc`、`fc+`、`ap`、`ap+`、`fdx`、`fdx+`。

進捗とプレートは `-uc`、`-up`、`-c` に対応しています。

## その他

| コマンド | 説明 |
|----------|------|
| `[プレート]の達成状況` / `[プレート] achievement` | プレート進捗 |
| `[バージョン]のバージョンリスト` / `[バージョン] version-list` | バージョン楽曲一覧 |
| `friend list` / `friends` | maimai フレンド一覧 |
| `friend-rcd <コード> [コマンド] [フィルター]` | フレンド成績画像 |
| `rc <定数>` | Rating 表 |
| `calc <tap> <hold> <slide> [touch] <break>` | Note スコア計算 |
| `random [レベル/定数]` | ランダム選曲 |
| `rank` / `ranking` / `rank jp` / `rank intl` | ランキング |
| LINE 位置メッセージ | JP / INTL 店舗データを統合して近い店舗を表示 |

## 権限リクエスト

```text
accept-perm-request <request_id>
reject-perm-request <request_id>
```
