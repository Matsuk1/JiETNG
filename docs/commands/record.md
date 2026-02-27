# 成绩系统

<img src="/b50_example.png" alt="Best 50 成绩示例" style="width: 22%; max-width: 400px; min-width: 200px; display: block; margin: 1.5rem auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);" />

## 命令

### 基础 Best 图表

```
b50          # Best 50 图表（旧曲 35 + 新曲 15）
b40          # Best 40 图表（过去的 Rating 计算方案，旧曲 25 + 新曲 15）
best50 / best40   # 同上，替代命令
```

### 变体

```
b35 / best35              # 仅旧曲 Best 35
b15 / best15              # 仅新曲 Best 15
ab35 / allb35             # All Best 35（忽略版本）
ab50 / allb50             # All Best 50（忽略版本）
apb50 / ap50              # All Perfect Best 50（仅 AP/AP+ 成绩）
fdxb50 / fdx50            # Full DX Best 50（仅 FDX/FDX+ 成绩）
idealb50 / idlb50         # Ideal Best 50（模拟上一梯度成绩）
rct50 / r50               # Recent 50（最近 50 次游玩）
```

## 过滤参数

所有 B 系命令均支持以下过滤参数：

| 参数 | 说明 | 示例 |
|------|------|------|
| `-lv [值] [最大值]` | 按定数筛选。单值精确匹配，双值为范围 | `-lv 14.7` 或 `-lv 14 14.9` |
| `-ra [值] [最大值]` | 按 Rating 筛选。单值精确匹配，双值为范围 | `-ra 301` 或 `-ra 301 312` |
| `-star [值] [最大值]` | 按 DX 星数筛选。单值精确匹配，双值为范围 | `-star 3` 或 `-star 3 5` |
| `-scr [最小值] [最大值]` | 按达成率筛选（最大值可选） | `-scr 100.3` 或 `-scr 99 100` |
| `-dx [最小值] [最大值]` | 按 DX score 百分比筛选（最大值可选） | `-dx 92` 或 `-dx 90 95` |
| `-ver [版本...]` | 按版本筛选，可多选 | `-ver buddies` 或 `-ver splash splash+` |
| `-diff [难度...]` | 按难度筛选，可多选 | `-diff mas` 或 `-diff mas rem` |
| `-type [dx\|std]` | 按谱面类型筛选 | `-type dx` |
| `-page [页码]` | 翻页 | `-page 2` |

::: tip 难度简写
`bas` = BASIC，`adv` = ADVANCED，`exp` = EXPERT，`mas` = MASTER，`rem` = Re:MASTER
:::

::: tip 版本名称
不区分大小写，使用 `+` 表示 PLUS 版本（如 `splash+`），多个版本用空格分隔。
:::

### 示例

```
b50 -lv 14.7                             # 定数 14.7（精确匹配）
b50 -lv 14 14.9                          # 定数 14.0~14.9
b50 -ra 301 312                          # Rating 301~312
b50 -scr 100.3                           # 达成率 ≥100.3%
b50 -dx 92 95                            # DX score 92%~95%
b50 -ver buddies -lv 14 14.9             # Buddies 版本 14 级歌曲
b50 -diff mas rem -scr 100.5             # MASTER/Re:MASTER 且达成率 ≥100.5%
b50 -type dx -diff mas                   # DX 谱面 MASTER 难度
b50 -diff mas -lv 14 14.9 -page 2        # 翻到第 2 页
```

---

## 定数查询

查看指定难度等级的所有歌曲，按内部定数分组显示。

### 命令格式

```
13の定数リスト    # 日文命令
13のレベルリスト  # 日文命令
13 level-list   # 英文命令
```

定数查询自动使用绑定时设置的服务器版本（JP 或 INTL）。

---

## 难度评级达成进度

查看指定难度和评级的谱面达成情况。

### 命令格式

```
13sss+進捗        # 13 难度 SSS+ 评级进度
13+sss progress   # 13+ 难度 SSS 评级进度
15fdx+ progress   # 15 难度 FDX+ 评级进度
```

### 支持的评级

- **评分等级**：S、S+、SS、SS+、SSS、SSS+
- **Full Combo**：FC、FC+、AP、AP+
- **Full Sync**：FDX、FDX+

::: tip
- 评级不区分大小写
- 支持日文（進捗）、英文（progress）和中文（进度）关键字
- 支持的难度：11、11+、12、12+、13、13+、14、14+、15
:::
