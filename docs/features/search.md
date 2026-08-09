---
title: 舞萌DX 成绩查询与筛选
description: JiETNG 支持 maimai B50、定数、等级、DX Rating、达成率、レート内訳和歌曲成绩查询筛选。
---

# 成绩查询与搜索

JiETNG 的查询能力分为三类：成绩图筛选、歌曲搜索、歌曲 ID 查询。

## 成绩图筛选

B 系列命令支持在同一条消息里追加筛选参数：

```text
b50 -lv 14 14.9 -diff mas rem -scr 100.5
ab50 -ver buddies -type dx
rct50 -page 2
ap50 -lv 13.6
```

可筛选字段包括等级/定数、单谱 Rating、达成率、DX 分数、DX 星数、难度、谱面类型、版本和页码。

筛选结果会继续使用成绩图模板渲染，因此适合用来做“某个定数段的 B50”“只看 MAS/Re:MAS”“只看某版本”等图。

## 歌曲搜索

```text
artist Nanahira
designer Jack
bpm 180
bpm 0-120
bpm 120-180
ヒバナ info
ヒバナ info
```

- `artist` 按艺术家名搜索。
- `designer` 按谱面设计师搜索。
- `bpm` 按 BPM 精确值或范围搜索，支持从 `0` 开始的范围，以及 `120-180`、`120~180`、`120 180`。
- `info` 查询歌曲信息。
- 关键词大小写不敏感。

## 歌曲成绩

```text
ヒバナ record
```

`record` 按歌曲名或别名搜索个人成绩。

## 等级列表

```text
13 records
13.6 levels
```

- `records` 输出你的成绩列表。
- `levels` 输出定数/等级相关的歌曲列表与目标达成视图。

## 数据来源

查询结果来自 JiETNG 当前保存的加工后成绩数据。数据可能来自：

- `maimai update` 从 maimai NET 同步
- 网页书签通过 Import Token 上传
- 开发者 API 上传的加工后成绩 JSON

如果数据没有更新，查询结果也不会自动重新爬取。需要同步时请手动 `maimai update`，或重新使用网页书签上传。
