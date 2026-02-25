# 快速开始

只需三个简单步骤即可开始使用 JiETNG 追踪您的 『maimai でらっくす』 成绩。

## 前提条件

在开始之前，请确保您有：

- ✅ LINE 账号
- ✅ SEGA ID 账号（用于 maimai NET）
- ✅ 访问 maimai NET 的权限
- ✅ 智能手机或电脑

## 步骤 1: 添加机器人

1. 在 LINE 中搜索 **@299bylay**
2. 或点击链接：[@299bylay](https://line.me/R/ti/p/@299bylay)
3. 点击"添加好友"
4. 开始对话

## 步骤 2: 绑定 SEGA ID

### 开始绑定

向机器人发送：

```
bind
```

### 完成绑定流程

1. 机器人会发送一个带有 **绑定URL** 的按钮
2. **点击按钮**打开绑定网页
3. **输入您的凭据**：
   - SEGA ID（用户名）
   - 密码
   - 选择版本（JP 或 International）
   - 选择语言
4. **提交表单**
5. 等待确认消息

:::warning ⚠️ 重要安全提示
- **不要在聊天中输入密码**
- 只使用机器人提供的官方链接
- 令牌在 2 分钟后过期
- 您的密码经过加密存储
:::

### 验证绑定

检查绑定是否成功：

```
profile
```

您应该看到您的 SEGA ID、版本和语言信息。

[需要帮助绑定？查看详细绑定指南 →](/guide/binding)

## 步骤 3: 更新您的成绩

现在从 maimai NET 同步您的成绩！

### 首次同步

```
maimai update
```

### 等待处理

- ⏱️ 更新时间：20-30 秒
- 📊 获取所有您的曲目和成绩

## 步骤 4: 生成 Best 50

### 基础命令

```
b50
```

### 其他变体

```
b100      # Best 100（前 70 旧曲 + 前 30 新曲）
b35       # 仅前 35 旧曲
b15       # 仅前 15 新曲
```

[了解更多关于 Best 50 →](/commands/record)

## 下一步做什么

### 探索功能

可用命令示例：

**搜索曲目**：
```
[曲名] info
```

**随机曲目**：
```
random
random 14
```

**好友列表**：
```
friend list
```

**查看版本成就**：
```
暁極 achievement
```

### 学习更多

- 🎮 [基础命令列表](/commands/basic)
- ❓ [常见问题](/more/faq)

## 常用命令速查

| 命令 | 用途 |
|----------|---------|
| `maimai update` | 从 maimai NET 同步成绩 |
| `b50` | 生成 Best 50 图表 |
| `[曲名] song-info` | 搜索曲目信息 |
| `[曲名] record` | 查看您在该曲目的成绩 |
| `14 record-list` | 查看所有 14 级成绩 |
| `friend list` | 查看您的好友 |
| `profile` | 查看账号信息 |
| `unbind` | 解除绑定 SEGA ID |

## 故障排除

### "您尚未绑定 SEGA ID"

**解决方案**：完成步骤 2 - 使用 `bind` 命令

### "更新失败"

**可能原因**：
- maimai NET 正在维护
- 网络连接问题
- SEGA 凭据错误

**解决方案**：
- 等待几分钟后重试
- 检查 maimai NET 能否直接访问
- 使用 `unbind` 然后重新 `bind`

### "命令不起作用"

**检查列表**：
- ✅ 是否已绑定？（`profile`）
- ✅ 是否已更新成绩？（`maimai update`）
- ✅ 拼写是否正确？
- ✅ 使用的是正确的命令吗？

[查看完整故障排除指南 →](/more/faq)

## 需要帮助？

- 📖 [阅读完整文档](/guide/introduction)
- ❓ [查看 FAQ](/more/faq)
- 💬 [加入 Discord](https://discord.gg/NXxFn9T8Xz)
- 🐛 [报告问题](https://github.com/Matsuk1/JiETNG/issues)
- 📧 [联系支持](/more/support)

