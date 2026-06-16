# 支持与反馈

## 先确认问题类型

### 成绩没有更新

- SEGA 绑定用户：先发送 `maimai update`。
- 导入模式用户：重新打开网页书签并上传成绩。
- 查询命令不会自动重新爬取官方数据。

### 无法绑定

- 确认在私聊中发送 `bind`。
- 确认选择了正确服务器：`jp` 或 `intl`。
- 如果只想使用网页书签，绑定页可选择 Import Token 导入模式。

### 网页书签失败

- 确认当前页面是官方 maimai 移动站：
  - `https://maimaidx.jp/maimai-mobile/home/`
  - `https://maimaidx-eng.com/maimai-mobile/home/`
- 确认浏览器已经登录。
- 图片生成超过 15 秒会提示超时，可以刷新后重试。
- 如果要上传成绩，请确认 Import Token 未撤销。

### @ 提及查不到用户

被提及用户必须已经注册 JiETNG 且有成绩数据。目标不存在时不会回退到你的数据。

## 提交反馈时请提供

- 使用的命令
- JP 还是 INTL
- 是否使用 SEGA 绑定或 Import Token
- 错误截图或 Bot 返回文本
- 大致发生时间

不要公开发送 SEGA 密码、Import Token、开发者 Token。

## 反馈渠道

- GitHub Issues：[github.com/Matsuk1/JiETNG/issues](https://github.com/Matsuk1/JiETNG/issues)
- Discord：[加入服务器](https://discord.gg/NXxFn9T8Xz)

## 支持开发

如果 JiETNG 对你有帮助，可以在 Bot 中发送：

```text
donate
```
