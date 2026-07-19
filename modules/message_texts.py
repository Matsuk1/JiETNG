"""
多语言消息文本定义 / Multilingual Message Text Definitions

此模块包含所有的多语言消息文本定义，供 message_manager.py 使用。
This module contains all multilingual message text definitions for use by message_manager.py.
"""

from linebot.v3.messaging import (
    FlexMessage,
    URIAction
)

from linebot.v3.messaging.models import (
    FlexBubble,
    FlexBox,
    FlexText,
    FlexSeparator
)


welcome_msg_text = "『JiETNG・カヰテー』で有りんす。\nお願ひ申し候。"
group_welcome_msg_text = "『JiETNG・カヰテー』で有りんす。\nお出迎え有りんす。"

rebind_msg_text = {
    "ja": "✅ SEGA アカウント情報を更新しました。",
    "en": "✅ SEGA account settings updated.",
    "zh": "✅ SEGA 账号信息已更新。"
}

unbind_msg_text = {
    "ja": "✅ SEGA アカウント連携を解除しました。",
    "en": "✅ SEGA account unlinked.",
    "zh": "✅ SEGA 账号已解绑。"
}


# ============================================================
# エラーメッセージ / Error Messages
# ============================================================

segaid_error_text = {
    "ja": "SEGAアカウントまだ連携してないよね？",
    "en": "You haven't linked your SEGA account yet, right?",
    "zh": "你还没有绑定 SEGA 账号吧？"
}

record_error_text = {
    "ja": "まだ maimai 成績データがありません。『maimai update』で更新してから試してください。",
    "en": "No maimai records found yet. Run `maimai update` first, then try again.",
    "zh": "还没有 maimai 成绩数据。请先使用『maimai update』更新后再试。"
}

info_error_text = {
    "ja": "maimai プロフィールがまだ保存されていません。『maimai update』で更新してから試してください。",
    "en": "Your maimai profile has not been saved yet. Run `maimai update` first, then try again.",
    "zh": "你的 maimai 玩家资料尚未保存。请先使用『maimai update』更新后再试。"
}

access_error_text = {
    "ja": "🙇 今めっちゃアクセス多いんだよね…ちょっと後でもう一回試してみて！",
    "en": "🙇 There's a lot of traffic right now... Please try again later!",
    "zh": "🙇 现在访问量很大…请稍后再试！"
}

system_error_text = {
    "ja": "😵 システムエラーが発生しました…管理者に通知済みです。しばらくしてから再度お試しください。",
    "en": "😵 A system error occurred... The administrator has been notified. Please try again later.",
    "zh": "😵 发生系统错误…已通知管理员。请稍后再试。"
}

input_error_text = {
    "ja": "コマンドを認識できませんでした。入力内容を確認してください。",
    "en": "Command not recognized. Please check your input.",
    "zh": "无法识别该命令，请检查输入内容。"
}

song_error_text = {
    "ja": "条件に合う楽曲が見つかりませんでした。",
    "en": "No songs matched the criteria.",
    "zh": "没有找到符合条件的歌曲。"
}

level_not_supported_text = {
    "ja": "このレベルの定数表はサポートされていません。\nレベル12以上のみ対応しています。",
    "en": "This level constant table is not supported.\nOnly levels 12 and above are available.",
    "zh": "不支持该等级的定数表。\n仅支持12级及以上。"
}


plate_error_text = {
    "ja": "指定されたプレートが見つかりませんでした。",
    "en": "Plate not found.",
    "zh": "没有找到指定的牌子。"
}

version_error_text = {
    "ja": "指定されたバージョンが見つかりませんでした。",
    "en": "Version not found.",
    "zh": "没有找到指定的版本。"
}

store_error_text = {
    "ja": "🥹 周辺の設置店舗がないね",
    "en": "🥹 No nearby arcades found",
    "zh": "🥹 附近没有找到游戏厅"
}

rate_limit_msg_text = {
    "ja": "🔄 現在システムが混み合っています。\nしばらくしてからもう一度お試しください。",
    "en": "🔄 The system is currently busy.\nPlease try again in a moment.",
    "zh": "🔄 系统当前较为繁忙，请稍后再试。"
}

maintenance_error_text = {
    "ja": "🔧 あれ？公式サイトがメンテナンス中みたい！\n夜間とかメンテナンス時間はアクセスできないから、またあとで試してみてね〜",
    "en": "🔧 Oh? The official site seems to be under maintenance!\nIt's not accessible during maintenance hours, so please try again later~",
    "zh": "🔧 咦？官方网站好像在维护中！\n维护时间无法访问，请稍后再试~"
}

# ============================================================
# 成績エクスポート / Records Export
# ============================================================

# 通知预览栏 / Push notification alt text
export_alt_text = {
    "ja": "成績データを書き出しました",
    "en": "Records exported",
    "zh": "成绩数据已导出"
}

# Flex 卡片标题
export_flex_title_text = {
    "ja": "成績データを書き出しました",
    "en": "Records Exported",
    "zh": "成绩数据已导出"
}

# Flex 卡片内说明（{best} / {recent} / {size} / {ttl} 可格式化）
export_flex_summary_text = {
    "ja": "Best: {best} 件 ・ Recent: {recent} 件\nファイル形式: {fmt}（{size_kb} KB）",
    "en": "Best: {best}  ·  Recent: {recent}\nFormat: {fmt} ({size_kb} KB)",
    "zh": "Best: {best} 条  ·  Recent: {recent} 条\n格式: {fmt}（{size_kb} KB）"
}

# Flex 卡片底部小字
export_flex_footnote_text = {
    "ja": "リンクは {ttl} 分後に自動で失効します",
    "en": "Link expires in {ttl} minutes",
    "zh": "下载链接将在 {ttl} 分钟后失效"
}

# Flex 按钮
export_flex_button_text = {
    "ja": "ダウンロード",
    "en": "Download",
    "zh": "下载"
}

# Flex 副按钮：复制下载链接
export_flex_copy_button_text = {
    "ja": "リンクをコピー",
    "en": "Copy Link",
    "zh": "复制链接"
}

# 无成绩 / 失败时的纯文本回退
export_empty_text = {
    "ja": "まだ書き出せる成績データがありません。『maimai update』で更新してから試してください。",
    "en": "No records to export yet. Run `maimai update` first, then try again.",
    "zh": "还没有可导出的成绩数据。请先使用『maimai update』更新后再试。"
}

export_failed_text = {
    "ja": "成績データの書き出しに失敗しました。しばらくしてからもう一度お試しください。",
    "en": "Failed to export records. Please try again later.",
    "zh": "成绩数据导出失败，请稍后再试。"
}

# ============================================================
# フレンド関連 / Friend Messages
# ============================================================

friend_error_text = {
    "ja": "お気に入りフレンドがまだ登録されていません。",
    "en": "No favorite friends have been registered yet.",
    "zh": "还没有收藏的好友。"
}

friend_rcd_error_text = {
    "ja": "指定されたユーザーはフレンドに登録されていません。",
    "en": "The selected user is not in your friend list.",
    "zh": "指定用户不在你的好友列表中。"
}

mention_error_text = {
    "ja": "メンションされたユーザーはまだ JiETNG に登録されていません。",
    "en": "The mentioned user is not registered with JiETNG yet.",
    "zh": "被提到的用户尚未注册 JiETNG。"
}

mention_record_error_text = {
    "ja": "メンションされたユーザーには、まだ maimai 成績データがありません。",
    "en": "The mentioned user does not have maimai records yet.",
    "zh": "被提到的用户还没有 maimai 成绩数据。"
}

cannot_do_for_others_text = {
    "ja": "このコマンドは自分のアカウントにのみ使用できます。",
    "en": "This command can only be used for your own account.",
    "zh": "该命令只能用于你自己的账号。"
}

# 有成绩，但本次查询的过滤/条件没匹配到（与"没成绩"区分）
no_matching_data_text = {
    "ja": "条件に合う成績データが見つかりませんでした。",
    "en": "No records matched the criteria.",
    "zh": "没有找到符合条件的成绩数据。"
}

mention_no_matching_data_text = {
    "ja": "メンションされたユーザーには、条件に合う成績データがありません。",
    "en": "The mentioned user has no records matching the criteria.",
    "zh": "被提到的用户没有符合条件的成绩数据。"
}


# 权限请求通知相关文本
perm_request_notification_title_text = {
    "ja": "アクセス権限リクエスト • Permission Requests",
    "en": "Access Permission Requests",
    "zh": "访问权限请求"
}

perm_request_notification_subtitle_text = {
    "ja": "{count} 件の新しいリクエスト",
    "en": "{count} new requests",  # 简化处理，统一使用复数
    "zh": "{count} 个新请求"
}

perm_request_accept_button_text = {
    "ja": "承認",
    "en": "Accept",
    "zh": "接受"
}

perm_request_reject_button_text = {
    "ja": "拒否",
    "en": "Reject",
    "zh": "拒绝"
}

perm_request_notification_alt_text = {
    "ja": "{count} 件のアクセス権限リクエストがあります",
    "en": "You have {count} access permission request(s)",
    "zh": "你有 {count} 个访问权限请求"
}

perm_request_accept_success_text = {
    "ja": "✅ アクセス権限リクエストを承認しました！\n\nToken ID: {token_id}\n申請者: {requester_name}\n\nこのトークンはあなたのアカウント情報にアクセスできるようになりました。",
    "en": "✅ Access permission request accepted!\n\nToken ID: {token_id}\nRequester: {requester_name}\n\nThis token can now access your account information.",
    "zh": "✅ 已接受访问权限请求！\n\nToken ID: {token_id}\n申请者: {requester_name}\n\n该 token 现在可以访问你的账户信息了。"
}

perm_request_reject_success_text = {
    "ja": "✅ アクセス権限リクエストを拒否しました。\n\nToken ID: {token_id}\n申請者: {requester_name}",
    "en": "✅ Access permission request rejected.\n\nToken ID: {token_id}\nRequester: {requester_name}",
    "zh": "✅ 已拒绝访问权限请求。\n\nToken ID: {token_id}\n申请者: {requester_name}"
}

perm_request_already_processed_text = {
    "ja": "このリクエストはすでに処理されています。",
    "en": "This request has already been processed.",
    "zh": "该请求已经处理过了。",
}


# ============================================================
# 管理者通知 / Admin Notifications
# ============================================================

dxdata_update_text = {
    "ja": "✅ Dxdata Updated!",
    "en": "✅ Dxdata Updated!",
    "zh": "✅ Dxdata 已更新！"
}

# ============================================================
# その他 / Others
# ============================================================

# 指定レベルのレコードなし
level_record_not_found_text = {
    "ja": "指定されたレベル「{level}」の{page}ページ目の譜面記録は存在しないかも...",
    "en": "No records found for level '{level}' page {page}...",
    "zh": "指定等级「{level}」的第 {page} 页记录可能不存在..."
}

# レベルレコード追加ページの説明
level_record_page_hint_text = {
    "ja": "これは{page}ページ目のデータだよ！",
    "en": "This is page {page} data!",
    "zh": "这是第 {page} 页的数据！"
}

# Dxdata 更新通知（管理员）
dxdata_update_notification_text = {
    "ja": "📢 Dxdata 更新通知\n\n{message}",
    "en": "📢 Dxdata Update Notification\n\n{message}",
    "zh": "📢 Dxdata 更新通知\n\n{message}"
}

# Dxdata 更新成功消息组件
dxdata_update_success_text = {
    "ja": "✅ Dxdata Updated!",
    "en": "✅ Dxdata Updated!",
    "zh": "✅ Dxdata 更新成功！"
}

dxdata_new_songs_text = {
    "ja": "🎵 新曲: +{count}首",
    "en": "🎵 New Songs: +{count}",
    "zh": "🎵 新增歌曲: +{count}首"
}

dxdata_songs_decreased_text = {
    "ja": "🎵 楽曲: {count}首",
    "en": "🎵 Songs: {count}",
    "zh": "🎵 歌曲: {count}首"
}

dxdata_no_new_songs_text = {
    "ja": "🎵 新曲: なし",
    "en": "🎵 New Songs: None",
    "zh": "🎵 新增歌曲: 无"
}

dxdata_new_sheets_text = {
    "ja": "📊 新譜面: +{count}個",
    "en": "📊 New Charts: +{count}",
    "zh": "📊 新增谱面: +{count}个"
}

dxdata_sheets_decreased_text = {
    "ja": "📊 譜面: {count}個",
    "en": "📊 Charts: {count}",
    "zh": "📊 谱面: {count}个"
}

dxdata_no_new_sheets_text = {
    "ja": "📊 新譜面: なし",
    "en": "📊 New Charts: None",
    "zh": "📊 新增谱面: 无"
}

dxdata_last_update_text = {
    "ja": "📅 前回更新: {timestamp}",
    "en": "📅 Last Update: {timestamp}",
    "zh": "📅 上次更新: {timestamp}"
}

dxdata_current_stats_text = {
    "ja": "📈 現在: 楽曲{songs}首 / 譜面{sheets}個",
    "en": "📈 Current: {songs} Songs / {sheets} Charts",
    "zh": "📈 当前: {songs}首歌曲 / {sheets}个谱面"
}

dxdata_first_update_text = {
    "ja": "(初回更新完了！)",
    "en": "(Initial update complete!)",
    "zh": "(首次更新完成！)"
}

dxdata_fetch_failed_text = {
    "ja": "❌ データ取得失敗！",
    "en": "❌ Failed to fetch data!",
    "zh": "❌ 数据获取失败！"
}

dxdata_parse_failed_text = {
    "ja": "❌ データ解析失敗！",
    "en": "❌ Failed to parse data!",
    "zh": "❌ 数据解析失败！"
}

dxdata_initial_stats_songs_text = {
    "ja": "📈 楽曲: {count}首",
    "en": "📈 Songs: {count}",
    "zh": "📈 歌曲: {count}首"
}

dxdata_initial_stats_sheets_text = {
    "ja": "📊 譜面: {count}個",
    "en": "📊 Charts: {count}",
    "zh": "📊 谱面: {count}个"
}

# SEGA 账号绑定消息
sega_bind_title_text = "SEGA Account Link"
sega_bind_description_text = "绑定你的 SEGA 账号\n綁定你的 SEGA 帳號\nSEGA アカウントを連携"
sega_bind_button_text = "Tap Here"
sega_bind_alt_text = "SEGA Account Link / SEGA 账号绑定 / SEGA 帳號綁定 / SEGA アカウント連携"

# 语言选择消息（用于首次绑定时）
# 这些文本在用户未选择语言时显示，所以直接显示多语言
language_select_title = "言語選択"

language_select_description = """Language Selection・语言选择・語言選擇"""

language_button_ja = "日本語"
language_button_en = "English"
language_button_zh = "简体中文"
language_button_zh_tw = "繁體中文"

language_select_alt = "Language Selection / 言語選択 / 语言选择 / 語言選擇"

language_set_success_text = {
    "ja": "✅ 言語を日本語に設定しました！",
    "en": "✅ Language set to English!",
    "zh": "✅ 语言已设置为中文！",
    "zh-tw": "✅ 語言已設定為繁體中文！"
}

# 已绑定账号的提示
already_bound_text = {
    "ja": "⚠️ すでに SEGA アカウントが連携されています。\n再度連携する場合は、先に unbind コマンドで連携を解除してください。\n\n💡 パスワードやバージョンを変更したい場合は rebind コマンド、タイムゾーンや言語などの設定は settings コマンドを使用してください。",
    "en": "⚠️ A SEGA account is already linked.\nTo rebind, please use the unbind command first to unlink your account.\n\n💡 Use rebind to change password or version, and settings for timezone, language, and other preferences.",
    "zh": "⚠️ 已绑定 SEGA 账号。\n如需重新绑定，请先使用 unbind 命令解除绑定。\n\n💡 修改密码或版本请使用 rebind 命令，修改时区、语言等设置请使用 settings 命令。"
}

# Unbind 确认消息
unbind_confirm_text = {
    "ja": "⚠️ アカウント連携を解除しようとしています。\n\nこの操作により、連携されている SEGA ID、パスワード、その他すべての設定が削除されます。\n\n🔴 この操作は取り消せません。\n\n続行するには、以下のコマンドを送信してください：\nunbind confirm",
    "en": "⚠️ You are about to unbind your account.\n\nThis will delete your linked SEGA ID, password, and all other settings.\n\n🔴 This action cannot be undone.\n\nTo proceed, please send the following command:\nunbind confirm",
    "zh": "⚠️ 您即将解除账号绑定。\n\n此操作将删除您绑定的 SEGA ID、密码以及所有其他设置。\n\n🔴 此操作无法撤销。\n\n若要继续，请发送以下命令：\nunbind confirm"
}

# Bind 命令群聊警告
bind_group_warning_text = {
    "ja": "⚠️ セキュリティのため、bind コマンドは個人チャットでのみ使用できます。ボットに直接メッセージを送信してください。",
    "en": "⚠️ For security reasons, the bind command can only be used in private chat. Please message the bot directly.",
    "zh": "⚠️ 出于安全考虑，bind 命令只能在私聊中使用。请直接向机器人发送消息。"
}

# Rebind 命令群聊警告
rebind_group_warning_text = {
    "ja": "⚠️ セキュリティのため、rebind コマンドは個人チャットでのみ使用できます。ボットに直接メッセージを送信してください。",
    "en": "⚠️ For security reasons, the rebind command can only be used in private chat. Please message the bot directly.",
    "zh": "⚠️ 出于安全考虑，rebind 命令只能在私聊中使用。请直接向机器人发送消息。"
}

# Settings 命令群聊警告
settings_group_warning_text = {
    "ja": "⚠️ セキュリティのため、settings コマンドは個人チャットでのみ使用できます。ボットに直接メッセージを送信してください。",
    "en": "⚠️ For security reasons, the settings command can only be used in private chat. Please message the bot directly.",
    "zh": "⚠️ 出于安全考虑，settings 命令只能在私聊中使用。请直接向机器人发送消息。"
}

private_info_group_warning_text = {
    "ja": "⚠️ セキュリティのため、個人情報コマンドは個人チャットでのみ使用できます。ボットに直接メッセージを送信してください。",
    "en": "⚠️ For security reasons, personal info commands can only be used in private chat. Please message the bot directly.",
    "zh": "⚠️ 出于安全考虑，个人信息命令只能在私聊中使用。请直接向机器人发送消息。"
}

friend_rcd_group_warning_text = {
    "ja": "⚠️ セキュリティのため、フレンドレコードコマンドは個人チャットでのみ使用できます。ボットに直接メッセージを送信してください。",
    "en": "⚠️ For security reasons, friend record commands can only be used in private chat. Please message the bot directly.",
    "zh": "⚠️ 出于安全考虑，好友记录命令只能在私聊中使用。请直接向机器人发送消息。"
}

# 搜索命令群聊警告
search_group_warning_text = {
    "ja": "⚠️ グループチャットでの荒らし防止のため、artist / designer / bpm 検索コマンドは個人チャットでのみ使用できます。",
    "en": "⚠️ To prevent spam, artist / designer / bpm search commands can only be used in private chat.",
    "zh": "⚠️ 为防止刷屏，artist / designer / bpm 搜索命令仅限私聊使用。"
}

# 排行榜
ranking_title_text = {
    "ja": "Rating ランキング",
    "en": "Rating Ranking",
    "zh": "Rating 排行榜"
}

ranking_alt_text = {
    "ja": "Rating ランキング",
    "en": "Rating Ranking",
    "zh": "Rating 排行榜"
}

ranking_no_data_text = {
    "ja": "ランキングデータがありません。",
    "en": "No ranking data available.",
    "zh": "暂无排行榜数据。"
}

# Rebind 未绑定提示
rebind_not_bound_text = {
    "ja": "まだ SEGA アカウントが連携されていません。bind コマンドで連携してください。",
    "en": "No SEGA account linked yet. Please use the bind command to link your account.",
    "zh": "尚未绑定 SEGA 账号。请使用 bind 命令进行绑定。"
}

# Rebind 按钮模板 - 标题 / Alt
rebind_title_alt_text = {
    "ja": "アカウント設定の編集",
    "en": "Edit Account Settings",
    "zh": "编辑账号设置"
}

# Rebind 按钮模板 - 描述
rebind_description_text = {
    "ja": "パスワード、バージョン、Aimeを変更できます。",
    "en": "You can change password, version, and Aime.",
    "zh": "您可以更改密码、版本和 Aime。"
}

# Rebind 按钮模板 - 按钮标签
rebind_button_text = {
    "ja": "アカウントを編集",
    "en": "Edit Account",
    "zh": "编辑账号"
}

# Settings 按钮模板 - 标题 / Alt
settings_title_alt_text = {
    "ja": "個人設定",
    "en": "Personal Settings",
    "zh": "个人设置"
}

# Settings 按钮模板 - 描述
settings_description_text = {
    "ja": "タイムゾーン、言語、背景画像を変更できます。",
    "en": "You can change timezone, language, and background image.",
    "zh": "您可以更改时区、语言和背景图片。"
}

# Settings 按钮模板 - 按钮标签
settings_button_text = {
    "ja": "設定を開く",
    "en": "Open Settings",
    "zh": "打开设置"
}

# 公告标题
notice_header_text = {
    "ja": "📢 お知らせ",
    "en": "📢 Notice",
    "zh": "📢 公告",
    "zh-tw": "📢 公告"
}

# 开发者 Token 相关消息
devtoken_create_success_text = {
    "ja": "✅ 開発者トークンを作成しました！\n\nToken ID: {token_id}\nToken: {token}\n備考: {note}\n作成日時: {created_at}\n\n⚠️ このトークンは一度しか表示されません。安全な場所に保管してください。",
    "en": "✅ Developer token created successfully!\n\nToken ID: {token_id}\nToken: {token}\nNote: {note}\nCreated: {created_at}\n\n⚠️ This token will only be shown once. Please store it securely.",
    "zh": "✅ 开发者 Token 创建成功！\n\nToken ID: {token_id}\nToken: {token}\n备注: {note}\n创建时间: {created_at}\n\n⚠️ 此 Token 仅显示一次，请妥善保管。"
}

devtoken_create_failed_text = {
    "ja": "❌ トークンの作成に失敗しました。",
    "en": "❌ Failed to create token.",
    "zh": "❌ Token 创建失败。"
}

devtoken_list_header_text = {
    "ja": "📋 開発者トークン一覧",
    "en": "📋 Developer Tokens List",
    "zh": "📋 开发者 Token 列表"
}

devtoken_list_empty_text = {
    "ja": "トークンはまだ作成されていません。",
    "en": "No tokens created yet.",
    "zh": "还没有创建任何 Token。"
}

devtoken_revoke_success_text = {
    "ja": "✅ トークン {token_id} を無効化しました。",
    "en": "✅ Token {token_id} has been revoked.",
    "zh": "✅ 已撤销 Token {token_id}。"
}

devtoken_revoke_failed_text = {
    "ja": "❌ トークン {token_id} が見つかりません。",
    "en": "❌ Token {token_id} not found.",
    "zh": "❌ 找不到 Token {token_id}。"
}

devtoken_info_text = {
    "ja": "📝 トークン詳細情報\n\nToken ID: {token_id}\nToken: {token}\n備考: {note}\n作成者: {created_by}\n作成日時: {created_at}\n最終使用: {last_used}\nステータス: {status}",
    "en": "📝 Token Details\n\nToken ID: {token_id}\nToken: {token}\nNote: {note}\nCreated by: {created_by}\nCreated: {created_at}\nLast used: {last_used}\nStatus: {status}",
    "zh": "📝 Token 详细信息\n\nToken ID: {token_id}\nToken: {token}\n备注: {note}\n创建者: {created_by}\n创建时间: {created_at}\n最后使用: {last_used}\n状态: {status}"
}

devtoken_info_not_found_text = {
    "ja": "❌ トークンが見つかりません。",
    "en": "❌ Token not found.",
    "zh": "❌ 找不到 Token。"
}

devtoken_usage_text = {
    "ja": "📚 開発者トークン管理\n\ndevtoken create <備考> - 新しいトークンを作成\ndevtoken list - トークン一覧を表示\ndevtoken revoke <token_id> - トークンを無効化\ndevtoken info <token_id> - トークンの詳細を表示",
    "en": "📚 Developer Token Management\n\ndevtoken create <note> - Create a new token\ndevtoken list - List all tokens\ndevtoken revoke <token_id> - Revoke a token\ndevtoken info <token_id> - Show token details",
    "zh": "📚 开发者 Token 管理\n\ndevtoken create <备注> - 创建新 Token\ndevtoken list - 显示所有 Token\ndevtoken revoke <token_id> - 撤销 Token\ndevtoken info <token_id> - 显示 Token 详情"
}

# 好友列表 alt_text
friend_list_alt_text = {
    "ja": "お気に入りフレンド",
    "en": "Favorite Friends",
    "zh": "收藏的好友"
}

# 查看好友 B50 按钮显示文本
friend_rcd_text = {
    "ja": "{name} のデータ",
    "en": "{name}'s record",
    "zh": "{name} 的数据"
}

# Note 分数计算按钮文本
calc_button_text = {
    "ja": "ノーツ計算",
    "en": "Note Calc",
    "zh": "Note 计算"
}

# 歌曲信息 alt_text
song_info_alt_text = {
    "ja": "楽曲情報",
    "en": "Song Info",
    "zh": "歌曲信息"
}

# 歌曲成绩 alt_text
song_record_alt_text = {
    "ja": "楽曲成績",
    "en": "Song Record",
    "zh": "歌曲成绩"
}

# 查看成绩按钮文本
view_record_button_text = {
    "ja": "スコアを見る",
    "en": "View Record",
    "zh": "查看成绩"
}

# 查看歌曲信息按钮文本
view_info_button_text = {
    "ja": "楽曲情報を見る",
    "en": "View Song Info",
    "zh": "查看歌曲信息"
}

# 保存图片按钮文本
save_image_button_text = {
    "ja": "画像を保存",
    "en": "Save Image",
    "zh": "保存图片"
}

# 附近机厅列表 alt_text
nearby_stores_alt_text = {
    "ja": "最寄りの maimai 設置店舗",
    "en": "Nearby maimai Arcade Stores",
    "zh": "附近的 maimai 机厅"
}

donate_message = FlexMessage(
    alt_text="JiETNGを支援 · Support JiETNG",
    contents=FlexBubble(
        body=FlexBox(
            layout="vertical",
            spacing="md",
            paddingAll="16px",
            backgroundColor="#FFFFFF",
            contents=[
                # 标题
                FlexText(
                    text="カヰテーを支援 · Support JiETNG",
                    weight="bold",
                    size="md",
                    wrap=True,
                    align="center",
                    color="#000000"
                ),
                # 多语言说明文本
                FlexText(
                    text=(
                        "一起为 JiETNG 的开发与未来加油！\n"
                        "JiETNG の開発と未来を応援しよう！\n"
                        "Support JiETNG's journey ahead!"
                    ),
                    size="sm",
                    wrap=True,
                    margin="md",
                    align="center",
                    color="#555555"
                ),
                # 按钮容器
                FlexBox(
                    layout="horizontal",
                    spacing="md",
                    margin="lg",
                    justifyContent="center",
                    contents=[
                        # Liberapay
                        FlexBox(
                            layout="vertical",
                            flex=0,
                            width="100px",
                            height="40px",
                            cornerRadius="6px",
                            borderColor="#000000",
                            borderWidth="1px",
                            backgroundColor="#FFFFFF",
                            justifyContent="center",
                            alignItems="center",
                            contents=[
                                FlexText(
                                    text="Liberapay",
                                    weight="bold",
                                    color="#000000",
                                    size="sm",
                                    align="center",
                                    action=URIAction(
                                        label="Liberapay",
                                        uri="https://ja.liberapay.com/_matsuk1/donate?currency=JPY"
                                    )
                                )
                            ]
                        ),
                        # 爱发电
                        FlexBox(
                            layout="vertical",
                            flex=0,
                            width="100px",
                            height="40px",
                            cornerRadius="6px",
                            borderColor="#000000",
                            borderWidth="1px",
                            backgroundColor="#FFFFFF",
                            justifyContent="center",
                            alignItems="center",
                            contents=[
                                FlexText(
                                    text="爱发电",
                                    weight="bold",
                                    color="#000000",
                                    size="sm",
                                    align="center",
                                    action=URIAction(
                                        label="爱发电",
                                        uri="https://afdian.com/a/matsuki"
                                    )
                                )
                            ]
                        ),
                    ],
                ),
                # 底部灰分割线
                FlexSeparator(
                    margin="lg",
                    color="#DDDDDD"
                ),
                # 底部说明
                FlexText(
                    text="Thank you for supporting JiETNG",
                    size="xs",
                    color="#666666",
                    align="center",
                    margin="md"
                ),
            ],
        )
    ),
)

# ============================================================
# QuickReply 按钮标签多语言
# ============================================================

quick_reply_labels = {
    "maimai_update": {"ja": "maimai update", "en": "maimai update", "zh": "更新数据"},
    "support": {"ja": "サポート", "en": "Support", "zh": "帮助"},
    "account_bind": {"ja": "アカウント連携", "en": "Link Account", "zh": "绑定账号"},
    "retry": {"ja": "もう一回", "en": "Try Again", "zh": "再试一次"},
    "recent_50": {"ja": "Recent 50", "en": "Recent 50", "zh": "Recent 50"},
    "all_best_50": {"ja": "All Best 50", "en": "All Best 50", "zh": "All Best 50"},
}


# ============================================================
# 用户信息 Flex Message / User Info Flex Message
# ============================================================

user_info_flex_text = {
    'title': {
        'ja': 'ユーザー情報',
        'en': 'User Information',
        'zh': '用户信息'
    },
    'user_id_label': {
        'ja': 'LINE ID',
        'en': 'LINE ID',
        'zh': 'LINE ID'
    },
    'name_label': {
        'ja': 'プレイヤー名',
        'en': 'Player Name',
        'zh': '玩家名称'
    },
    'rating_label': {
        'ja': 'レーティング',
        'en': 'Rating',
        'zh': 'Rating'
    },
    'sega_id_label': {
        'ja': 'SEGA ID',
        'en': 'SEGA ID',
        'zh': 'SEGA ID'
    },
    'password_label': {
        'ja': 'パスワード',
        'en': 'Password',
        'zh': '密码'
    },
    'server_label': {
        'ja': 'サーバー',
        'en': 'Server',
        'zh': '服务器'
    },
    'language_label': {
        'ja': '言語',
        'en': 'Language',
        'zh': '语言'
    },
    'jp_server': {
        'ja': '日本版',
        'en': 'Japanese Server',
        'zh': '日服'
    },
    'intl_server': {
        'ja': '海外版',
        'en': 'International Server',
        'zh': '国际服'
    },
    'lang_ja': {
        'ja': '日本語',
        'en': 'Japanese',
        'zh': '日语'
    },
    'lang_en': {
        'ja': '英語',
        'en': 'English',
        'zh': '英语'
    },
    'lang_zh': {
        'ja': '中国語',
        'en': 'Chinese',
        'zh': '中文'
    },
    'copy_id': {
        'ja': 'IDをコピー',
        'en': 'Copy ID',
        'zh': '复制ID'
    },
    'alt_text': {
        'ja': 'ユーザー情報',
        'en': 'User Information',
        'zh': '用户信息'
    },
    'last_update_label': {
        'ja': '最終更新',
        'en': 'Last Update',
        'zh': '最后更新'
    },
    'not_bound': {
        'ja': '未連携',
        'en': 'Not Bound',
        'zh': '未绑定'
    },
}

update_result_flex_text = {
    'title_success': {
        'ja': '成績更新完了',
        'en': 'Records Updated',
        'zh': '成绩更新完成'
    },
    'title_error': {
        'ja': '成績更新エラー',
        'en': 'Records Update Failed',
        'zh': '成绩更新失败'
    },
    'update_time_label': {
        'ja': '更新日時',
        'en': 'Update Time',
        'zh': '更新时间'
    },
    'elapsed_time_label': {
        'ja': '処理時間',
        'en': 'Elapsed Time',
        'zh': '耗时'
    },
    'status_label': {
        'ja': '取得できなかった項目',
        'en': 'Items Not Updated',
        'zh': '未更新项目'
    },
    'failed': {
        'ja': '失敗',
        'en': 'Failed',
        'zh': '失败'
    },
    'alt_text_success': {
        'ja': '成績更新完了',
        'en': 'Records Updated',
        'zh': '成绩更新完成'
    },
    'alt_text_error': {
        'ja': '成績更新エラー',
        'en': 'Records Update Failed',
        'zh': '成绩更新失败'
    },
    'status_user_info': {
        'ja': 'プロフィール',
        'en': 'Profile',
        'zh': '玩家资料'
    },
    'status_best_records': {
        'ja': 'Best 成績',
        'en': 'Best Records',
        'zh': 'Best 成绩'
    },
    'status_recent_records': {
        'ja': 'Recent 成績',
        'en': 'Recent Records',
        'zh': 'Recent 成绩'
    }
}
