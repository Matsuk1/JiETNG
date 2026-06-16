# 隐私政策

## 概述

JiETNG 是个人维护的 maimai DX 成绩管理工具。本文说明当前项目会收集、保存和处理哪些数据。

## 数据来源

JiETNG 支持两种用户数据来源：

- **SEGA 账号同步**：用户在绑定页面填写 SEGA ID、密码、版本与 Aime，JiETNG 使用这些信息登录 maimai NET 并同步成绩。
- **Import Token 导入**：用户在设置页生成 Import Token，网页书签或第三方工具上传加工后的 `profile`、`best`、`recent` 数据。

## 保存的数据

可能保存的数据包括：

- LINE 用户 ID
- 语言、时区、背景等用户设置
- SEGA ID、加密后的 SEGA 密码、服务器版本、Aime
- maimai 用户资料、Rating、称号、头像/姓名框等显示信息
- Best、Recent 与单谱成绩数据
- Import Token 的哈希、状态与创建时间
- 开发者 Token、权限请求和授权关系
- 命令使用记录、错误日志与运行状态日志

Import Token 明文只在生成时显示一次，服务器保存哈希。

## 数据用途

数据用于：

- 同步与导入 maimai 成绩
- 生成成绩图、牌子进度、等级列表与排行榜
- 提供设置页、导出、权限管理和开发者 API
- 防止滥用、排查错误和维护服务稳定

## 第三方服务

JiETNG 会与以下服务交互：

- LINE Platform：接收和发送 Bot 消息
- SEGA maimai NET：同步官方成绩数据

网页书签运行在官方 maimai 移动站页面中，但上传到 JiETNG 的是加工后的成绩数据，不包含 SEGA 密码。

## 删除与导出

删除数据：

```text
unbind
unbind confirm
```

导出数据：

```text
export json
export xml
```

导出内容是加工后的成绩数据，不是数据库内部原始结构。

## 安全说明

- Web 页面通过 HTTPS 访问。
- SEGA 密码会加密保存。
- Import Token 与开发者 Token 应像密码一样保管。
- 撤销 Token 后，该 Token 不能继续上传或访问对应资源。

## 联系

- GitHub Issues：[github.com/Matsuk1/JiETNG/issues](https://github.com/Matsuk1/JiETNG/issues)
- Discord：[加入服务器](https://discord.gg/NXxFn9T8Xz)

**生效日期**：2026 年 6 月 16 日
