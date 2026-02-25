# 基础命令

本页面涵盖您在使用 JiETNG 时会经常用到的所有基本命令。

## 账户管理

### 绑定 SEGA 账户

链接您的 SEGA ID 以开始使用 JiETNG：

```
bind
```

这将提供一个用于安全绑定的网页链接。仅限私聊使用。

### 解绑账户

移除您的 SEGA ID 并删除所有存储的数据：

```
unbind
```

发送后，机器人会要求确认。发送以下命令以确认操作：

```
unbind confirm
```

:::danger 警告
此操作不可逆。您的所有数据将被永久删除。
:::

### 修改账户设置

在不解绑的情况下更新密码、时区、语言或 Aime 设置：

```
settings
rebind
```

发送链接，通过 Web 表单修改设置，SEGA ID 无法更改。仅限私聊使用。

### 更新成绩

从 SEGA 获取您的最新成绩：

```
maimai update
```

## 计算器

### 达成率计算器

计算达到目标达成率所需的百分比：

```
calc <tap> <hold> <slide> [<touch>] <break>
```

示例（100 个 tap、50 个 hold、30 个 slide、20 个 touch、10 个 break 的歌曲）：
```
calc 100 50 30 20 10
```

显示每种音符类型的达成率值。

## 用户资料

### 获取用户信息

```
profile
```

## 排行榜

### DX Rating 排行榜

查看当前版本用户的 DX Rating 排名：

```
rank
ranking
ランキング
```

也可以指定版本：

```
rank jp
rank intl
```

## 提示

### 命令快捷方式

许多命令有多个别名：

```
b50 = best50
b100 = best100
```

### 不区分大小写

命令不区分大小写：

```
B50 = b50 = Best50
RANDOM = random
```

### 空格

大多数命令忽略多余空格：

```
ヒバナ info       # 正常工作
b50              # 不需要空格
```

## 下一步

- 📖 [成绩命令](/commands/record) - 成绩查看命令

---

需要帮助？查看 [FAQ](/more/faq) 或[联系支持](/more/support)。
