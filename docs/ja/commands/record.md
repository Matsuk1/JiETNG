---
title: B50 レコードコマンド
description: JiETNG の maimai B50、Best 50、Recent 50、DX Rating、レート内訳、レベル目標、単曲レコードコマンド一覧。
---

# レコードコマンド

<img src="/b50_example.png" alt="Best 50 Example" style="width: 22%; max-width: 400px; min-width: 200px; display: block; margin: 1.5rem auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);" />

## B 系スコア画像

```text
b50 / best50
b40 / best40
b35 / best35
b15 / best15
ab35 / allb35
ab50 / allb50
apb50 / ap50
fdxb50 / fdx50
rct50 / r50
idealb50 / idlb50
s50 / sun50 / 寸50 / 寸止め
```

同じメッセージにフィルターを追加できます。

`寸50` / `寸止め` は SSS+ / SSS 寸止めの成績（`100.4000% - 100.4999%`、`99.9000% - 99.9999%`）を表示します。

## フィルター

```text
b50 -lv 14.7
b50 -lv 14 14.9
b50 -ra 301 312
b50 -scr 100.3
b50 -dx 92 95
b50 -ver buddies -lv 14 14.9
b50 -diff mas rem -scr 100.5
b50 -type dx -diff mas
b50 -times 2
b50 -page 2
```

レベル/定数、単曲 Rating、達成率、DX スコア、DX 星、難易度、譜面種別、バージョン、次バージョンプレビュー、ページ、表示倍率に対応しています。

## 楽曲レコード

```text
ヒバナ record
```

`record` は曲名または別名で検索します。候補が複数ある場合はリストを返します。

## レベル / 定数リスト

```text
13 records
13.6 records
14.7 records 2
13.6 levels
```

整数はレベル、小数は定数です。末尾の数字はページとして扱われます。

## 目標

```text
13sss+ prog
14ss+ prog -uc
14ss+ prog -up
14ss+ prog -c
```

目標：`s`、`s+`、`ss`、`ss+`、`sss`、`sss+`、`fc`、`fc+`、`ap`、`ap+`、`fdx`、`fdx+`。

| 接尾辞 | 意味 |
|--------|------|
| `-uc` | 未達成 |
| `-up` | 未プレイ |
| `-c` | 達成済み |

## プレートとバージョン

```text
真極 plate
真極 plate -uc
PRiSM PLUS ver
13.6 levels
```

プレートコマンドも `-uc`、`-up`、`-c` に対応しています。

## メンション

グループでは JiETNG 登録済みユーザーをメンションして成績を参照できます。

```text
@friend b50
@friend 13 records
@friend 14sss+ prog
```

アカウント、設定、エクスポート、更新コマンドは常に送信者本人にのみ作用します。
