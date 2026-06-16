# 快速开始

本页按当前 JiETNG 的实际流程说明如何开始使用。JiETNG 支持两种数据来源：绑定 SEGA 账号自动同步，或使用 Import Token 上传网页书签读取到的加工后成绩。

## 准备

- 一个 LINE 账号
- 至少一种数据来源：
  - SEGA ID 与 maimai NET 账号，用于 `maimai update` 自动同步
  - 或 JiETNG Import Token，用于网页书签上传成绩

## 绑定方式

在与 Bot 的私聊中发送：

```text
bind
```

Bot 会发送一个网页按钮。打开后可以选择：

- **绑定 SEGA 账号**：填写 SEGA ID、密码、服务器版本（`jp` 或 `intl`）、语言与 Aime。
- **不绑定但使用 Import Token**：创建仅依赖导入数据的账号，适合只想通过网页书签上传成绩的用户。

绑定链接会过期；过期后重新发送 `bind` 即可获取新链接。

## 同步或导入成绩

### SEGA 账号用户

发送：

```text
maimai update
```

别名：

```text
update
```

Bot 会从对应版本的 maimai NET 同步资料、Best 记录、Recent 记录等数据。这个命令只能查询自己。

### Import Token 用户

发送：

```text
settings
```

在设置页生成 Import Token，然后到[网页书签工具](/bookmarklet)页面保存书签。登录 maimai 官方移动站后点击书签，即可在原页面生成成绩图，并可保存 token 后上传 best / recent / profile 数据。

Import Token 明文只显示一次。设置页可以查看所有 token、撤销 token，并删除已撤销 token。

## 常用命令

```text
b50
rct50
13.6のレコードリスト
13sss+ progress
真極の達成状況
ヒバナ record
settings
export json
```

更多命令见[命令大全](/commands/)和[成绩命令](/commands/record)。

## 修改设置

发送：

```text
settings
```

可修改语言、时区、背景、显示设置，并管理 Import Token。`settings` 仅限私聊使用。

如需修改 SEGA 账号密码、版本或 Aime，发送：

```text
rebind
```

`rebind` 只适用于已绑定完整 SEGA 账号的用户，且 SEGA ID 本身不可更换。

## 解除绑定

发送：

```text
unbind
```

再发送：

```text
unbind confirm
```

会删除 JiETNG 中保存的用户数据。此操作不可恢复。

## JP 与 INTL

绑定 SEGA 账号时选择 `jp` 或 `intl`。网页书签会根据当前打开的官方域名自动识别：

- JP：`https://maimaidx.jp/maimai-mobile/home/`
- INTL：`https://maimaidx-eng.com/maimai-mobile/home/`
