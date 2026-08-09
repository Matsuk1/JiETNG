---
title: maimai DX 検索とフィルター
description: JiETNG は maimai B50、定数、レベル、DX Rating、達成率、レート内訳、単曲レコード検索に対応しています。
---

# 検索とフィルター

JiETNG の検索は、スコア画像フィルター、楽曲検索、楽曲 ID 検索に分かれます。

## スコア画像フィルター

```text
b50 -lv 14 14.9 -diff mas rem -scr 100.5
ab50 -ver buddies -type dx
rct50 -page 2
ap50 -lv 13.6
```

レベル/定数、単曲 Rating、達成率、DX スコア、DX 星、難易度、譜面種別、バージョン、ページで絞り込めます。

結果はスコア画像として描画されるため、定数帯 B50、MASTER/Re:MASTER のみ、特定バージョンのみなどの確認に使えます。

## 楽曲検索

```text
artist Nanahira
designer Jack
bpm 180
bpm 0-120
bpm 120-180
ヒバナ info
```

- `artist` はアーティスト名検索。
- `designer` は譜面制作者検索。
- `bpm` は BPM の完全一致または範囲検索。`0` から始まる範囲、`120-180`、`120~180`、`120 180` に対応。
- `info` は楽曲情報。
- キーワードは大文字小文字を区別しません。

## 楽曲レコード

```text
ヒバナ record
```

`record` は曲名または別名で個人成績を検索します。

## データ元

検索結果は JiETNG に保存済みの加工済み成績データを使います。データ元は `maimai update`、ブックマークレットの Import Token アップロード、または開発者 API インポートです。

検索コマンドだけでは公式データを再同期しません。
