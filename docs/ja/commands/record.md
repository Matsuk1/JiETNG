# スコアシステム

<img src="/b50_example.png" alt="Best 50 スコア例" style="width: 22%; max-width: 400px; min-width: 200px; display: block; margin: 1.5rem auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);" />

## コマンド

### 基本 Best チャート

```
b50          # Best 50（旧曲 35 + 新曲 15）
b40          # Best 40（旧 Rating 計算方式、旧曲 25 + 新曲 15）
best50 / best40   # 上記の代替コマンド
```

### バリエーション

```
b35 / best35              # 旧曲 Best 35 のみ
b15 / best15              # 新曲 Best 15 のみ
ab35 / allb35             # All Best 35（バージョン無視）
ab50 / allb50             # All Best 50（バージョン無視）
apb50 / ap50              # All Perfect Best 50（AP/AP+ のみ）
fdxb50 / fdx50            # Full DX Best 50（FDX/FDX+ のみ）
idealb50 / idlb50         # Ideal Best 50（上位梯度スコアをシミュレート）
rct50 / r50               # Recent 50（最近 50 回のプレイ）
```

## フィルター

すべての B 系コマンドは以下のフィルターパラメーターをサポートします：

| パラメーター | 説明 | 例 |
|------------|------|-----|
| `-lv [値] [最大値]` | 定数でフィルター。単値は精確一致、双値は範囲 | `-lv 14.7` または `-lv 14 14.9` |
| `-ra [値] [最大値]` | Rating でフィルター。単値は精確一致、双値は範囲 | `-ra 301` または `-ra 301 312` |
| `-star [値] [最大値]` | DX 星数でフィルター。単値は精確一致、双値は範囲 | `-star 3` または `-star 3 5` |
| `-scr [最小値] [最大値]` | 達成率でフィルター（最大値省略可） | `-scr 100.3` または `-scr 99 100` |
| `-dx [最小値] [最大値]` | DX score % でフィルター（最大値省略可） | `-dx 92` または `-dx 90 95` |
| `-ver [バージョン...]` | バージョンでフィルター、複数指定可 | `-ver buddies` または `-ver splash splash+` (plus → +) |
| `-diff [難易度...]` | 難易度でフィルター、複数指定可 | `-diff mas` または `-diff mas rem` |
| `-type [dx\|std]` | 譜面タイプでフィルター | `-type dx` |
| `-page [n]` | ページ送り | `-page 2` |

::: tip 難易度略語
`bas` = BASIC、`adv` = ADVANCED、`exp` = EXPERT、`mas` = MASTER、`rem` = Re:MASTER
:::

::: tip バージョン名
大文字小文字を区別しません。PLUS バージョンは `+` を使用（例：`splash+`）。複数指定はスペース区切り。
:::

### 例

```
b50 -lv 14.7                             # 定数 14.7（精確一致）
b50 -lv 14 14.9                          # 定数 14.0~14.9
b50 -ra 301 312                          # Rating 301~312
b50 -scr 100.3                           # 達成率 ≥100.3%
b50 -dx 92 95                            # DX score 92%~95%
b50 -ver buddies -lv 14 14.9             # Buddies バージョンのレベル 14 楽曲
b50 -diff mas rem -scr 100.5             # MASTER/Re:MASTER かつ達成率 ≥100.5%
b50 -type dx -diff mas                   # DX 譜面の MASTER 難易度
b50 -diff mas -lv 14 14.9 -page 2        # 2 ページ目へ
```

---

## 定数クエリ

指定難易度のすべての楽曲を内部定数でグループ表示します。

### コマンド形式

```
13の定数リスト    # 日本語コマンド
13のレベルリスト  # 日本語コマンド
13 level-list   # 英語コマンド
```

定数クエリは連携時に設定されたサーバーバージョン（JP または INTL）を自動的に使用します。

---

## 難易度評価達成進捗

指定難易度と評価の譜面達成状況を確認します。

### コマンド形式

```
13sss+進捗        # 13 難易度 SSS+ 評価進捗
13+sss progress   # 13+ 難易度 SSS 評価進捗
15fdx+ progress   # 15 難易度 FDX+ 評価進捗
```

### サポートされている評価

- **評価ランク**：S、S+、SS、SS+、SSS、SSS+
- **Full Combo**：FC、FC+、AP、AP+
- **Full Sync**：FDX、FDX+

::: tip
- 評価は大文字小文字を区別しません
- 日本語（進捗）と英語（progress）のキーワードをサポート
- サポートされている難易度：11、11+、12、12+、13、13+、14、14+、15
:::
