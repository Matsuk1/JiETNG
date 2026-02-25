# 快速开始

## 前提条件

- LINE 账号
- SEGA ID 账号（用于 maimai NET）
- 访问 maimai NET 的权限

## 第一步：添加机器人

在 LINE 中搜索 **@299bylay** 或使用链接：[@299bylay](https://line.me/R/ti/p/@299bylay)

## 第二步：绑定 SEGA ID

在私聊中发送绑定命令：

```
bind
```

点击机器人发送的按钮打开绑定页面，输入 SEGA ID、密码、服务器版本（JP 或国际版）和语言。

:::warning
绑定令牌 2 分钟后过期，重新发送 `bind` 可获取新链接。
:::

验证是否绑定成功：

```
profile
```

## 第三步：同步成绩

```
maimai update
```

## 第四步：生成 Best 50

```
b50
```

其他图表类型请参阅[成绩命令](/commands/record)。
