---
title: B50 成绩命令
description: JiETNG 舞萌DX 查分器的 B50、Best 50、Recent 50、DX Rating、レート内訳、等级进度和单曲成绩命令说明。
---

# 成绩命令

<img src="/b50_example.png" alt="Best 50 成绩示例" style="width: 22%; max-width: 400px; min-width: 200px; display: block; margin: 1.5rem auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);" />

## B 系列成绩图

```text
b50 / best50          # Best 35 + Best 15
b40 / best40          # 旧版 Rating 结构
b35 / best35          # 旧曲 Best 35
b15 / best15          # 新曲 Best 15
ab35 / allb35         # 不区分版本的 Best 35
ab50 / allb50         # 不区分版本的 Best 50
apb50 / ap50          # AP/AP+ 成绩 Best 50
fdxb50 / fdx50        # FDX/FDX+ 成绩 Best 50
rct50 / r50           # Recent 50
idealb50 / idlb50     # 理想分数 Best 50
寸50 / 寸止め / s50 / sun50  # 寸止め 50：100.4000%-100.4999%、99.9000%-99.9999%
```

这些命令可以直接发送，也可以带筛选参数。

`寸50` 会列出离 SSS+ / SSS 只差一点的成绩：`100.4000% - 100.4999%` 与 `99.9000% - 99.9999%`。

## 筛选参数

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

常用参数：

| 参数 | 说明 |
|------|------|
| `-lv` | 等级或定数，支持单值或范围 |
| `-ra` | 单谱 Rating 范围 |
| `-scr` | 达成率下限或范围 |
| `-dx` | DX 分数百分比范围 |
| `-star` | DX 星数 |
| `-diff` | 难度，如 `bas`、`adv`、`exp`、`mas`、`rem` |
| `-type` | 谱面类型，如 `std`、`dx` |
| `-ver` | 版本关键字 |
| `-next` / `-nxt` | 下版本预览 |
| `-page` | 页码 |
| `-times` | 放大默认展示数量 |

## 单曲成绩

```text
ヒバナ record
ヒバナ song-record
ヒバナのレコード
search-record 123456
```

- `record` / `song-record` / `のレコード` 按曲名或别名搜索。
- `search-record` 使用 6 位歌曲 ID 查询。
- 如果搜索结果不唯一，Bot 会返回候选列表。

## 等级与定数列表

```text
13のレコードリスト
13 records
13 record-list 2
13.6のレコードリスト
14.7 records 2
```

整数表示等级，小数表示定数。末尾数字表示页码。

## 等级达成进度

```text
13sss+ progress
14AP進捗
15fdx+ 进度
14ss+ progress -uc
14ss+ progress -up
14ss+ progress -c
```

支持的目标：`s`、`s+`、`ss`、`ss+`、`sss`、`sss+`、`fc`、`fc+`、`ap`、`ap+`、`fdx`、`fdx+`。

筛选后缀：

| 后缀 | 说明 |
|------|------|
| `-uc` | 只看未达成 |
| `-up` | 只看未游玩 |
| `-c` | 只看已达成 |

## 牌子与版本

```text
真極の達成状況
真極 achievement
真極の達成状況 -uc
PRiSM PLUSのバージョンリスト
PRiSM PLUS version-list
13.6のレベルリスト
13.6の定数リスト
13.6 level-list
```

牌子达成状况同样支持 `-uc`、`-up`、`-c`。

## @ 提及查询

群聊中可以 @ 已注册用户查询对方成绩：

```text
@好友 b50
@好友 13 records
@好友 14sss+ progress
```

仅成绩类命令支持 @ 查询。账号、设置、导出、更新等 self-only 命令始终只作用于发送者。
