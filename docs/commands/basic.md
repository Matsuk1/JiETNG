# 基础命令

## 账户管理

### 绑定

```
bind
```

发送后收到绑定链接（有效期 2 分钟）。仅限私聊。

### 解绑

```
unbind
```

发送后需确认：

```
unbind confirm
```

:::danger 警告
此操作不可逆，所有数据将被永久删除。
:::

### 修改账户设置

```
settings
rebind
```

发送设置链接，可修改密码、版本、时区、语言、Aime 等设置。SEGA ID 无法更改。仅限私聊。

### 更新成绩

```
maimai update
update
```

频率限制：30 秒内最多 2 次。

### 查看绑定信息

```
profile
getme
```

---

## 计算器

### 达成率计算器

```
calc <tap> <hold> <slide> [<touch>] <break>
```

4 个参数（无 touch）或 5 个参数（含 touch）：

```
calc 500 100 200 50        # 无 touch
calc 500 100 200 30 50     # 含 touch
```

### Rating 对照表

```
rc 14.7
RC 14.7
Rc 14.7
```

输入定数（1.0~15.0，最多一位小数），返回各达成率对应的 Rating 值。

---

## 排行榜

```
rank
ranking
ランキング
rank jp       # 日服排行榜
rank intl     # 国际服排行榜
```

---

## 随机歌曲

```
random
random 14        # 随机 Lv.14 歌曲（14.0~14.5）
random 14+       # 随机 Lv.14+ 歌曲（14.6~14.9）
random 14.7      # 随机定数 14.7 歌曲
```
