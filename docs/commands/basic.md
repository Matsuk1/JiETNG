# 基础命令

基础命令主要用于账号、设置、状态、导出与支持信息。除特别说明外，命令大小写不敏感。

## 账号与设置

### bind

```text
bind
```

发送绑定链接。仅限私聊。

绑定页支持两种模式：

- 绑定 SEGA 账号，用于 `maimai update` 自动同步。
- 不绑定 SEGA 账号，仅创建 Import Token 用户，用网页书签上传成绩。

### rebind

```text
rebind
```

发送换绑链接，可修改 SEGA 密码、服务器版本与 Aime。仅限已绑定完整 SEGA 账号的用户；SEGA ID 不可更换。仅限私聊。

### settings

```text
settings
```

发送设置页链接。可修改语言、时区、背景、显示设置，并管理 Import Token。完整绑定用户与 Import Token 用户均可使用。仅限私聊。

### profile / getme

```text
profile
getme
```

查看当前账号资料、绑定状态与服务器版本。

### unbind

```text
unbind
unbind confirm
```

先发送 `unbind` 获取确认提示，再发送 `unbind confirm` 删除保存的数据。此操作不可恢复。

## 数据更新

```text
maimai update
update
```

从 maimai NET 同步最新成绩。该命令需要完整 SEGA 账号绑定，并且只能用于自己的账号。

Import Token 用户请使用网页书签上传成绩。

## 数据导出

```text
export json
export xml
成绩导出 json
成績エクスポート xml
```

导出的是 JiETNG 加工后的成绩数据，不是数据库原始记录。内容包括用户资料、服务器版本、Best 记录、Recent 记录以及用于复现成绩图所需的标准化字段。

## 其他

```text
donate
status
rank
rank jp
rank intl
```

- `donate`：显示支持开发信息。
- `status`：显示机器人运行状态。
- `rank` / `ranking`：查看 DX Rating 排行榜，可指定 `jp` 或 `intl`。

## 限制

- `bind`、`rebind`、`settings`、`update`、`export`、`unbind` 为 self-only 命令，不会查询被 @ 提及的用户。
- 群聊中如果 @ 不存在或没有 JiETNG 数据的用户，成绩查询不会回退成你的数据。
