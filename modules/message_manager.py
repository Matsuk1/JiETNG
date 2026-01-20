from modules.config_loader import SUPPORT_PAGE, USERS, LINE_ACCOUNT_ID
from modules.user_manager import get_notice_interaction, get_user_timezone
from modules.tip_ad_manager import get_random_tip, get_random_ad
from linebot.v3.messaging import (
    TextMessage,
    QuickReply,
    QuickReplyItem,
    MessageAction,
    PostbackAction,
    URIAction,
    FlexMessage,
    FlexContainer
)

from linebot.v3.messaging.models import (
    FlexBubble,
    FlexBox,
    FlexText,
    FlexButton,
    FlexSeparator
)

# ============================================================
# 多语言辅助函数 / Multilingual Helper Functions
# ============================================================

def get_user_language(user_id):
    """
    获取用户语言设置

    Args:
        user_id: 用户ID

    Returns:
        str: 语言代码 ('ja', 'en', 'zh')，默认为 'ja'
    """
    if user_id and user_id in USERS:
        return USERS[user_id].get('language', 'ja')
    return 'ja'

def format_timezone_string(user_id):
    """
    格式化用户时区字符串

    Args:
        user_id: 用户ID

    Returns:
        str: 格式化的时区字符串，如 "(UTC+9)"
    """
    tz_offset = get_user_timezone(user_id)
    tz_sign = '+' if tz_offset >= 0 else ''
    return f"(UTC{tz_sign}{tz_offset})"

def get_multilingual_text(message_dict, user_id=None, language=None):
    """
    根据用户语言获取对应的文本

    Args:
        message_dict: 多语言消息字典 {'ja': '...', 'en': '...', 'zh': '...'}
        user_id: 用户ID（可选）
        language: 直接指定语言（可选，优先级高于user_id）

    Returns:
        str: 对应语言的文本，如果不存在则返回日语文本
    """
    if not isinstance(message_dict, dict):
        return message_dict

    if language is None:
        language = get_user_language(user_id) if user_id else 'ja'

    return message_dict.get(language, message_dict.get('ja', ''))

# ============================================================
# アカウント連携関連 / Account Binding
# ============================================================

bind_msg_text = {
    "ja": "✅ SEGA IDの連携できたよ！",
    "en": "✅ SEGA ID linked successfully!",
    "zh": "✅ SEGA ID 绑定成功！"
}

unbind_msg_text = {
    "ja": "✅ SEGA IDの連携を解除したよ！",
    "en": "✅ SEGA ID unlinked successfully!",
    "zh": "✅ SEGA ID 解绑成功！"
}

# ============================================================
# データ更新関連 / Data Update
# ============================================================

update_over_text = {
    "ja": "✅ アップデート完了！",
    "en": "✅ Update completed!",
    "zh": "✅ 更新完成！"
}

update_error_text = {
    "ja": "❗️あれ？アップデート中にエラーが出ちゃった！",
    "en": "❗️Oops! An error occurred during the update!",
    "zh": "❗️哎呀？更新过程中出现错误了！"
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
    "ja": "maimaiレコードまだアップデートしてないみたい！",
    "en": "Looks like you haven't updated your maimai records yet!",
    "zh": "看起来你还没有更新 maimai 记录！"
}

info_error_text = {
    "ja": "ごめん！maimai個人情報まだメモしてないわ！",
    "en": "Sorry! Your maimai profile hasn't been saved yet!",
    "zh": "抱歉！你的 maimai 个人信息还没有保存！"
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
    "ja": "全然わかんないなー",
    "en": "I don't understand what you mean...",
    "zh": "我完全不明白你的意思..."
}

picture_error_text = {
    "ja": "画像処理しっぱい〜〜",
    "en": "Image processing failed~~",
    "zh": "图片处理失败~~"
}

song_error_text = {
    "ja": "条件に合う楽曲がないかも...",
    "en": "No songs match the criteria...",
    "zh": "没有符合条件的歌曲..."
}

level_not_supported_text = {
    "ja": "このレベルの定数表はサポートされていません。\nレベル12以上のみ対応しています。",
    "en": "This level constant table is not supported.\nOnly levels 12 and above are available.",
    "zh": "不支持该等级的定数表。\n仅支持12级及以上。"
}


plate_error_text = {
    "ja": "そのプレートがわからないね...",
    "en": "I don't recognize that plate...",
    "zh": "我不认识那个牌子..."
}

version_error_text = {
    "ja": "そのバージョンがわからないね...",
    "en": "I don't recognize that version...",
    "zh": "我不认识那个版本..."
}

store_error_text = {
    "ja": "🥹 周辺の設置店舗がないね",
    "en": "🥹 No nearby arcades found",
    "zh": "🥹 附近没有找到游戏厅"
}

rate_limit_msg_text = {
    "ja": "⏳ ちょっと待ってー！今同じリクエスト処理中だから！\n終わるまでちょっと待っててね〜",
    "en": "⏳ Wait a moment! I'm still processing the same request!\nPlease wait until it's done~",
    "zh": "⏳ 稍等一下！我正在处理相同的请求！\n等我完成再试试吧~"
}

maintenance_error_text = {
    "ja": "🔧 あれ？公式サイトがメンテナンス中みたい！\n夜間とかメンテナンス時間はアクセスできないから、またあとで試してみてね〜",
    "en": "🔧 Oh? The official site seems to be under maintenance!\nIt's not accessible during maintenance hours, so please try again later~",
    "zh": "🔧 咦？官方网站好像在维护中！\n维护时间无法访问，请稍后再试~"
}

# ============================================================
# フレンド関連 / Friend Messages
# ============================================================

friend_error_text = {
    "ja": "お気に入りにフレンド登録してないみたいだよ？",
    "en": "Looks like you haven't registered any favorite friends?",
    "zh": "看起来你还没有收藏的好友？"
}

friend_rcd_error_text = {
    "ja": "この人フレンドじゃないかも！",
    "en": "This person might not be your friend!",
    "zh": "这个人可能不是你的好友！"
}

mention_error_text = {
    "ja": "メンションされたユーザーはまだ登録してないみたい！",
    "en": "The mentioned user hasn't registered yet!",
    "zh": "被提到的用户好像还没有注册！"
}

multiple_mention_error_text = {
    "ja": "ごめん！一度に複数のユーザーをメンションできないよ〜",
    "en": "Sorry! You can't mention multiple users at once~",
    "zh": "抱歉！不能一次提到多个用户哦~"
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


# ============================================================
# 管理者通知 / Admin Notifications
# ============================================================

notice_upload_text = {
    "ja": "✅ Notice uploaded",
    "en": "✅ Notice uploaded",
    "zh": "✅ 公告已上传"
}

dxdata_update_text = {
    "ja": "✅ Dxdata Updated!",
    "en": "✅ Dxdata Updated!",
    "zh": "✅ Dxdata 已更新！"
}

# ============================================================
# その他 / Others
# ============================================================

# 临时使用好友账号
friend_use_once_text = {
    "ja": "これからは一回だけ「{name}」さんとしてレコードをチェックしていきますよ！\n色んなコマンドを使ってみてね！",
    "en": "Checking records as '{name}' just once!\nTry various commands!",
    "zh": "这次将作为「{name}」查看记录！\n试试各种命令吧！"
}

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
sega_bind_title_text = {
    "ja": "SEGA アカウント連携",
    "en": "SEGA Account Link",
    "zh": "SEGA 账号绑定"
}

sega_bind_description_text = {
    "ja": "SEGA アカウントと連携されます\n有効期限は発行から2分間です",
    "en": "Link your SEGA account\nValid for 2 minutes from issuance",
    "zh": "将绑定你的 SEGA 账号\n有效期为发行后2分钟"
}

sega_bind_button_text = {
    "ja": "押しで連携",
    "en": "Tap to Link",
    "zh": "点击绑定"
}

sega_bind_alt_text = {
    "ja": "SEGA アカウント連携",
    "en": "SEGA Account Link",
    "zh": "SEGA 账号绑定"
}

# 语言选择消息（用于首次绑定时）
# 这些文本在用户未选择语言时显示，所以直接显示三语
language_select_title = "言語選択 / Language Selection / 语言选择"

language_select_description = """言語を選択 / Select language / 选择语言"""

language_button_ja = "🇯🇵 日本語"
language_button_en = "🇺🇸 English"
language_button_zh = "🇨🇳 中文"

language_select_alt = "Language Selection / 言語選択 / 语言选择"

language_set_success_text = {
    "ja": "✅ 言語を日本語に設定しました！",
    "en": "✅ Language set to English!",
    "zh": "✅ 语言已设置为中文！"
}

# 已绑定账号的提示
already_bound_text = {
    "ja": "⚠️ すでに SEGA アカウントが連携されています。\n再度連携する場合は、先に unbind コマンドで連携を解除してください。\n\n💡 パスワード、バージョン、タイムゾーン、言語のみを変更したい場合は、profile コマンドまたは rebind コマンドを使用してください。",
    "en": "⚠️ A SEGA account is already linked.\nTo rebind, please use the unbind command first to unlink your account.\n\n💡 If you only want to change password, version, timezone, or language, please use the profile or rebind command.",
    "zh": "⚠️ 已绑定 SEGA 账号。\n如需重新绑定，请先使用 unbind 命令解除绑定。\n\n💡 如果只想修改密码、版本、时区或语言，请使用 profile 或 rebind 命令。"
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

# Rebind/Profile 命令群聊警告
rebind_group_warning_text = {
    "ja": "⚠️ セキュリティのため、rebind / profile コマンドは個人チャットでのみ使用できます。ボットに直接メッセージを送信してください。",
    "en": "⚠️ For security reasons, the rebind / profile command can only be used in private chat. Please message the bot directly.",
    "zh": "⚠️ 出于安全考虑，rebind / profile 命令只能在私聊中使用。请直接向机器人发送消息。"
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
    "ja": "パスワード、バージョン、タイムゾーン、言語を変更できます。",
    "en": "You can change password, version, timezone, and language.",
    "zh": "您可以更改密码、版本、时区和语言。"
}

# Rebind 按钮模板 - 按钮标签
rebind_button_text = {
    "ja": "設定を編集",
    "en": "Edit Settings",
    "zh": "编辑设置"
}

# 公告标题
notice_header_text = {
    "ja": "📢 お知らせ",
    "en": "📢 Notice",
    "zh": "📢 公告"
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
view_friend_b50_text = {
    "ja": "{name} の B50 を表示",
    "en": "View {name}'s B50",
    "zh": "查看 {name} 的 B50"
}

# Note 分数计算按钮文本
calc_button_text = {
    "ja": "ノーツ計算",
    "en": "Note Calc",
    "zh": "Note 计算"
}

# Note 分数计算 alt_text
calc_button_alt_text = {
    "ja": "ノーツ計算",
    "en": "Note Calculation",
    "zh": "Note 分数计算"
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
# 消息生成辅助函数 / Message Generation Helper Functions
# ============================================================

def get_quick_reply_label(key, user_id=None):
    """获取 QuickReply 按钮的多语言标签"""
    if key not in quick_reply_labels:
        return key
    return get_multilingual_text(quick_reply_labels[key], user_id)

def create_text_message(msg_text_dict, user_id=None, quick_reply=None):
    """
    生成多语言 TextMessage

    Args:
        msg_text_dict: 多语言消息字典
        user_id: 用户ID（可选）
        quick_reply: QuickReply 对象（可选）

    Returns:
        TextMessage: 多语言文本消息
    """
    text = get_multilingual_text(msg_text_dict, user_id)
    return TextMessage(text=text, quick_reply=quick_reply)

def get_support_quick_reply(user_id=None):
    """获取「サポート」按钮的 QuickReply"""
    return QuickReply(
        items=[
            QuickReplyItem(action=URIAction(
                label=get_quick_reply_label("support", user_id),
                uri=SUPPORT_PAGE
            ))
        ]
    )

def get_update_quick_reply(user_id=None):
    """获取更新相关的 QuickReply"""
    label = get_quick_reply_label("maimai_update", user_id)
    return QuickReply(
        items=[
            QuickReplyItem(action=MessageAction(
                label=label,
                text="maimai update",
                display_text=label
            )),
            QuickReplyItem(action=URIAction(
                label=get_quick_reply_label("support", user_id),
                uri=SUPPORT_PAGE
            ))
        ]
    )

def get_update_over_quick_reply(user_id=None):
    """获取更新完成后的 QuickReply"""
    label_rct50 = get_quick_reply_label("recent_50", user_id)
    label_ab50 = get_quick_reply_label("all_best_50", user_id)
    return QuickReply(
        items=[
            QuickReplyItem(action=MessageAction(
                label=label_rct50,
                text="rct50",
                display_text=label_rct50
            )),
            QuickReplyItem(action=MessageAction(
                label=label_ab50,
                text="ab50",
                display_text=label_ab50
            )),
            QuickReplyItem(action=URIAction(
                label=get_quick_reply_label("support", user_id),
                uri=SUPPORT_PAGE
            ))
        ]
    )

def get_update_error_quick_reply(user_id=None):
    """获取更新错误后的 QuickReply"""
    label = get_quick_reply_label("retry", user_id)
    return QuickReply(
        items=[
            QuickReplyItem(action=MessageAction(
                label=label,
                text="maimai update",
                display_text=label
            )),
            QuickReplyItem(action=URIAction(
                label=get_quick_reply_label("support", user_id),
                uri=SUPPORT_PAGE
            ))
        ]
    )

def get_segaid_error_quick_reply(user_id=None):
    """获取 SEGA ID 错误的 QuickReply"""
    label = get_quick_reply_label("account_bind", user_id)
    return QuickReply(
        items=[
            QuickReplyItem(action=MessageAction(
                label=label,
                text="bind",
                display_text=label
            )),
            QuickReplyItem(action=URIAction(
                label=get_quick_reply_label("support", user_id),
                uri=SUPPORT_PAGE
            ))
        ]
    )

def get_record_error_quick_reply(user_id=None):
    """获取记录错误的 QuickReply"""
    label = get_quick_reply_label("maimai_update", user_id)
    return QuickReply(
        items=[
            QuickReplyItem(action=MessageAction(
                label=label,
                text="maimai update",
                display_text=label
            )),
            QuickReplyItem(action=URIAction(
                label=get_quick_reply_label("support", user_id),
                uri=SUPPORT_PAGE
            ))
        ]
    )

# ============================================================
# 向后兼容的消息生成函数 / Backward Compatible Message Functions
# ============================================================

def bind_msg(user_id=None):
    """生成 SEGA ID 绑定成功消息"""
    return create_text_message(bind_msg_text, user_id, get_update_quick_reply(user_id))

def unbind_msg(user_id=None):
    """生成 SEGA ID 解绑成功消息"""
    return create_text_message(unbind_msg_text, user_id)

def update_over(user_id=None):
    """生成更新完成消息"""
    return create_text_message(update_over_text, user_id, get_update_over_quick_reply(user_id))

def update_error(user_id=None):
    """生成更新错误消息"""
    return create_text_message(update_error_text, user_id, get_update_error_quick_reply(user_id))

def segaid_error(user_id=None):
    """生成 SEGA ID 错误消息"""
    return create_text_message(segaid_error_text, user_id, get_segaid_error_quick_reply(user_id))

def record_error(user_id=None):
    """生成记录错误消息"""
    return create_text_message(record_error_text, user_id, get_record_error_quick_reply(user_id))

def info_error(user_id=None):
    """生成个人信息错误消息"""
    return create_text_message(info_error_text, user_id, get_record_error_quick_reply(user_id))

def access_error(user_id=None):
    """生成访问错误消息"""
    return create_text_message(access_error_text, user_id)

def system_error(user_id=None):
    """生成系统错误消息"""
    return create_text_message(system_error_text, user_id, get_support_quick_reply(user_id))

def input_error(user_id=None):
    """生成输入错误消息"""
    return create_text_message(input_error_text, user_id, get_support_quick_reply(user_id))

def picture_error(user_id=None):
    """生成图片错误消息"""
    return create_text_message(picture_error_text, user_id, get_support_quick_reply(user_id))

def song_error(user_id=None):
    """生成歌曲错误消息"""
    return create_text_message(song_error_text, user_id, get_support_quick_reply(user_id))

def level_not_supported(user_id=None):
    """生成等级不支持消息"""
    return create_text_message(level_not_supported_text, user_id, get_support_quick_reply(user_id))

def plate_error(user_id=None):
    """生成牌子错误消息"""
    return create_text_message(plate_error_text, user_id, get_support_quick_reply(user_id))

def version_error(user_id=None):
    """生成版本错误消息"""
    return create_text_message(version_error_text, user_id, get_support_quick_reply(user_id))

def store_error(user_id=None):
    """生成店铺错误消息"""
    return create_text_message(store_error_text, user_id)

def rate_limit_msg(user_id=None):
    """生成频率限制消息"""
    return create_text_message(rate_limit_msg_text, user_id, get_support_quick_reply(user_id))

def maintenance_error(user_id=None):
    """生成维护错误消息"""
    return create_text_message(maintenance_error_text, user_id, get_support_quick_reply(user_id))

def friend_error(user_id=None):
    """生成好友错误消息"""
    return create_text_message(friend_error_text, user_id)

def friend_rcd_error(user_id=None):
    """生成好友记录错误消息"""
    return create_text_message(friend_rcd_error_text, user_id)

def mention_error(user_id=None):
    """生成提到用户不存在错误消息"""
    return create_text_message(mention_error_text, user_id)

def multiple_mention_error(user_id=None):
    """生成多个用户提到错误消息"""
    return create_text_message(multiple_mention_error_text, user_id)

def get_perm_request_notification_alt_text(count, user_id=None):
    """获取权限请求通知的 alt text"""
    return get_multilingual_text(perm_request_notification_alt_text, user_id).format(count=count)

def notice_upload(user_id=None):
    """生成公告上传消息"""
    return create_text_message(notice_upload_text, user_id)

def friend_use_once(name, user_id=None):
    """生成临时使用好友账号消息"""
    text = get_multilingual_text(friend_use_once_text, user_id).format(name=name)
    return TextMessage(text=text)

def level_record_not_found(level, page, user_id=None):
    """生成指定等级记录未找到消息"""
    text = get_multilingual_text(level_record_not_found_text, user_id).format(level=level, page=page)
    return TextMessage(text=text)

def level_record_page_hint(page, user_id=None):
    """生成等级记录页面提示消息"""
    text = get_multilingual_text(level_record_page_hint_text, user_id).format(page=page)
    return TextMessage(text=text)

def dxdata_update_notification(message, user_id=None):
    """生成 Dxdata 更新通知消息（管理员）"""
    text = get_multilingual_text(dxdata_update_notification_text, user_id).format(message=message)
    return TextMessage(text=text)

def get_notice_header(user_id=None):
    """获取公告标题（多语言）"""
    return get_multilingual_text(notice_header_text, user_id)

def generate_notice_flex(notice_json, user_id=None):
    """
    生成公告 FlexMessage (支持多语言和投票)

    Args:
        notice_json: 公告数据 {"id": "...", "content": {...}, "date": "...", "voting_enabled": bool}
        user_id: 用户ID（用于多语言和投票状态）

    Returns:
        FlexMessage
    """
    # 获取用户语言
    lang = get_user_language(user_id) if user_id else 'ja'

    # 标题（多语言）
    title = get_notice_header(user_id)

    # 内容（根据用户语言）
    content_dict = notice_json.get('content', {})
    if isinstance(content_dict, str):
        # 向后兼容旧格式
        content = content_dict
    else:
        content = content_dict.get(lang, content_dict.get('ja', ''))

    date = notice_json.get('date', '')
    notice_id = notice_json.get('id', '')
    voting_enabled = notice_json.get('voting_enabled', False)

    # 基础body内容
    body_contents = [
        {
            "type": "text",
            "text": content,
            "wrap": True,
            "size": "sm",
            "color": "#333333",
            "margin": "none"
        }
    ]

    # 如果有自定义按钮，添加按钮卡片到body
    if 'button' in notice_json:
        button_info = notice_json['button']
        button_type = button_info.get('type', 'uri')
        button_label_dict = button_info.get('label', {})
        button_label = button_label_dict.get(lang, button_label_dict.get('ja', ''))
        button_value = button_info.get('value', '')

        # 如果label为空，使用默认值
        if not button_label:
            default_labels = {
                'uri': {'ja': '詳細を見る', 'en': 'View Details', 'zh': '查看详情'},
                'message': {'ja': '試してみる', 'en': 'Try it', 'zh': '尝试一下'}
            }
            button_label = default_labels.get(button_type, {}).get(lang, 'Go')

        # 添加箭头到按钮标签
        button_label_with_arrow = f"{button_label} →"

        # 根据按钮类型创建action
        if button_type == 'uri':
            action = {
                "type": "uri",
                "label": button_label_with_arrow,
                "uri": button_value
            }
        else:  # message
            action = {
                "type": "uri",
                "label": button_label_with_arrow,
                "uri": f"https://line.me/R/oaMessage/{LINE_ACCOUNT_ID}/?{button_value}"
            }

        # 添加按钮卡片
        button_box = {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": action,
                    "style": "link",
                    "height": "sm",
                    "color": "#FF6B35"
                }
            ],
            "backgroundColor": "#FFF5F0",
            "cornerRadius": "md",
            "paddingAll": "12px",
            "margin": "md"
        }
        body_contents.append(button_box)

    # 基础bubble结构
    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": title,
                    "weight": "bold",
                    "size": "md",
                    "color": "#FFFFFF"
                }
            ],
            "backgroundColor": "#FF6B35",
            "paddingAll": "16px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": body_contents,
            "paddingAll": "20px",
            "backgroundColor": "#FFFFFF"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [],
            "paddingAll": "12px",
            "backgroundColor": "#F5F5F5"
        }
    }

    # 如果启用投票，添加投票按钮
    if voting_enabled and user_id:
        # 获取用户当前投票状态
        interaction = get_notice_interaction(user_id, notice_id)
        current_vote = interaction.get('vote') if interaction else None

        # 投票按钮文本（多语言）
        vote_labels = {
            'support': {'ja': '支持', 'en': 'Support', 'zh': '支持'},
            'oppose': {'ja': '反対', 'en': 'Oppose', 'zh': '反对'}
        }

        support_label = vote_labels['support'].get(lang, '支持')
        oppose_label = vote_labels['oppose'].get(lang, '反対')

        # 如果已投票，标记选中状态
        support_style = "primary"
        oppose_style = "primary"
        support_color = "#17B169"
        oppose_color = "#FF3B30"

        # 添加投票按钮
        vote_buttons = {
            "type": "box",
            "layout": "horizontal",
            "spacing": "sm",
            "margin": "md",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": support_label,
                        "data": f"action=vote_notice&notice_id={notice_id}&vote=support"
                    },
                    "style": support_style,
                    "color": support_color,
                    "height": "sm"
                },
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": oppose_label,
                        "data": f"action=vote_notice&notice_id={notice_id}&vote=oppose"
                    },
                    "style": oppose_style,
                    "color": oppose_color,
                    "height": "sm"
                }
            ]
        }

        bubble['footer']['contents'].append(vote_buttons)
        bubble['footer']['contents'].append({
            "type": "separator",
            "margin": "md"
        })

    # 添加日期
    bubble['footer']['contents'].append({
        "type": "text",
        "text": date,
        "size": "xs",
        "color": "#999999",
        "align": "end"
    })

    return FlexMessage(
        alt_text=title,
        contents=FlexContainer.from_dict(bubble)
    )

def get_friend_list_alt_text(user_id=None):
    """获取好友列表 alt_text（多语言）"""
    return get_multilingual_text(friend_list_alt_text, user_id)

def get_nearby_stores_alt_text(user_id=None):
    """获取附近机厅列表 alt_text（多语言）"""
    return get_multilingual_text(nearby_stores_alt_text, user_id)

def get_calc_button_label(user_id=None):
    """获取定数计算按钮标签（多语言）"""
    return get_multilingual_text(calc_button_text, user_id)

def get_calc_button_alt_text(user_id=None):
    """获取定数计算按钮 alt_text（多语言）"""
    return get_multilingual_text(calc_button_alt_text, user_id)

def generate_calc_button(song_id, user_id=None):
    """
    生成 Note 计算按钮（FlexMessage）

    Args:
        song_id: 歌曲ID
        user_id: 用户ID（用于多语言）

    Returns:
        FlexMessage
    """
    return FlexMessage(
        alt_text=get_calc_button_alt_text(user_id),
        contents=FlexContainer.from_dict({
            "type": "bubble",
            "size": "micro",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "style": "secondary",
                        "height": "sm",
                        "action": {
                            "type": "postback",
                            "label": get_calc_button_label(user_id),
                            "data": f"calc-song {song_id}"
                        }
                    }
                ],
                "paddingAll": "8px"
            }
        })
    )

def build_dxdata_update_message(result, user_id=None):
    """
    构建 Dxdata 更新消息（多语言）

    Args:
        result: update_dxdata_with_comparison 返回的结果字典
        user_id: 用户ID（用于确定语言）

    Returns:
        str: 多语言更新消息
    """
    if not result.get('success'):
        # 更新失败
        if 'message' in result:
            # 如果已经有消息，判断是什么类型的错误
            if 'データ取得失敗' in result['message'] or 'fetch' in result['message'].lower():
                return get_multilingual_text(dxdata_fetch_failed_text, user_id)
            else:
                return get_multilingual_text(dxdata_parse_failed_text, user_id)
        return get_multilingual_text(dxdata_fetch_failed_text, user_id)

    message_parts = []

    # 标题
    message_parts.append(get_multilingual_text(dxdata_update_success_text, user_id))
    message_parts.append('')

    if result.get('old_stats'):
        # 有历史数据，显示对比
        diff = result.get('diff', {})
        songs_diff = diff.get('songs_added', 0)
        sheets_diff = diff.get('sheets_added', 0)

        # 新曲变化
        if songs_diff > 0:
            message_parts.append(get_multilingual_text(dxdata_new_songs_text, user_id).format(count=songs_diff))
        elif songs_diff < 0:
            message_parts.append(get_multilingual_text(dxdata_songs_decreased_text, user_id).format(count=songs_diff))
        else:
            message_parts.append(get_multilingual_text(dxdata_no_new_songs_text, user_id))

        # 新谱面变化
        if sheets_diff > 0:
            message_parts.append(get_multilingual_text(dxdata_new_sheets_text, user_id).format(count=sheets_diff))
        elif sheets_diff < 0:
            message_parts.append(get_multilingual_text(dxdata_sheets_decreased_text, user_id).format(count=sheets_diff))
        else:
            message_parts.append(get_multilingual_text(dxdata_no_new_sheets_text, user_id))

        # 上次更新时间
        message_parts.append('')
        message_parts.append(get_multilingual_text(dxdata_last_update_text, user_id).format(
            timestamp=result['old_stats']['timestamp']
        ))

        # 当前统计
        new_stats = result['new_stats']
        message_parts.append(get_multilingual_text(dxdata_current_stats_text, user_id).format(
            songs=new_stats['total_songs'],
            sheets=new_stats['total_sheets']
        ))
    else:
        # 首次更新
        new_stats = result['new_stats']
        message_parts.append(get_multilingual_text(dxdata_initial_stats_songs_text, user_id).format(
            count=new_stats['total_songs']
        ))
        message_parts.append(get_multilingual_text(dxdata_initial_stats_sheets_text, user_id).format(
            count=new_stats['total_sheets']
        ))
        message_parts.append('')
        message_parts.append(get_multilingual_text(dxdata_first_update_text, user_id))

    return '\n'.join(message_parts)

# ============================================================
# 用户信息 Flex Message / User Info Flex Message
# ============================================================

user_info_flex_text = {
    'title': {
        'ja': '👤 ユーザー情報',
        'en': '👤 User Information',
        'zh': '👤 用户信息'
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

def generate_user_info_flex(user_id):
    """
    生成用户信息 Flex Message

    Args:
        user_id: 用户ID

    Returns:
        FlexMessage: 用户信息 Flex Message
    """
    lang = get_user_language(user_id)
    texts = user_info_flex_text

    # 构建内容行
    content_rows = []

    if user_id in USERS:
        user_data = USERS[user_id]

        # LINE ID 行（带复制按钮）
        content_rows.append({
            "type": "box",
            "layout": "horizontal",
            "spacing": "md",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "flex": 3,
                    "contents": [
                        {
                            "type": "text",
                            "text": get_multilingual_text(texts['user_id_label'], language=lang),
                            "size": "xs",
                            "color": "#999999"
                        },
                        {
                            "type": "text",
                            "text": user_id,
                            "size": "sm",
                            "weight": "bold",
                            "wrap": True,
                            "margin": "xs"
                        }
                    ]
                },
                {
                    "type": "button",
                    "flex": 0,
                    "style": "secondary",
                    "height": "sm",
                    "action": {
                        "type": "message",
                        "label": "📋",
                        "text": user_id
                    }
                }
            ]
        })

        # 分隔线
        content_rows.append({
            "type": "separator",
            "margin": "md"
        })

        # SEGA ID
        sega_id_value = user_data.get('sega_id', get_multilingual_text(texts['not_bound'], language=lang))

        content_rows.append({
            "type": "box",
            "layout": "vertical",
            "margin": "md",
            "contents": [
                {
                    "type": "text",
                    "text": get_multilingual_text(texts['sega_id_label'], language=lang),
                    "size": "xs",
                    "color": "#999999"
                },
                {
                    "type": "text",
                    "text": sega_id_value,
                    "size": "sm",
                    "weight": "bold",
                    "margin": "xs"
                }
            ]
        })

        # 分隔线
        content_rows.append({
            "type": "separator",
            "margin": "md"
        })

        # 玩家名称
        if "personal_info" in user_data:
            personal_info = user_data['personal_info']
            if 'name' in personal_info:
                content_rows.append({
                    "type": "box",
                    "layout": "vertical",
                    "margin": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": get_multilingual_text(texts['name_label'], language=lang),
                            "size": "xs",
                            "color": "#999999"
                        },
                        {
                            "type": "text",
                            "text": personal_info['name'],
                            "size": "sm",
                            "weight": "bold",
                            "margin": "xs"
                        }
                    ]
                })

                # 分隔线
                content_rows.append({
                    "type": "separator",
                    "margin": "md"
                })

            # Rating
            if 'rating' in personal_info:
                rating_contents = [
                    {
                        "type": "text",
                        "text": get_multilingual_text(texts['rating_label'], language=lang),
                        "size": "xs",
                        "color": "#999999"
                    },
                    {
                        "type": "text",
                        "text": str(personal_info['rating']),
                        "size": "sm",
                        "weight": "bold",
                        "margin": "xs"
                    }
                ]

                # 添加最后更新时间（如果存在）
                if 'last_update' in user_data:
                    tz_str = format_timezone_string(user_id)
                    rating_contents.append({
                        "type": "text",
                        "text": f"・{get_multilingual_text(texts['last_update_label'], language=lang)} {tz_str}: {user_data['last_update']}",
                        "size": "xs",
                        "color": "#666666",
                        "margin": "sm"
                    })

                content_rows.append({
                    "type": "box",
                    "layout": "vertical",
                    "margin": "md",
                    "contents": rating_contents
                })

                # 分隔线
                content_rows.append({
                    "type": "separator",
                    "margin": "md"
                })

        # 服务器
        if "version" in user_data:
            server_text = texts['jp_server'] if user_data['version'] == 'jp' else texts['intl_server']
            content_rows.append({
                "type": "box",
                "layout": "vertical",
                "margin": "md",
                "contents": [
                    {
                        "type": "text",
                        "text": get_multilingual_text(texts['server_label'], language=lang),
                        "size": "xs",
                        "color": "#999999"
                    },
                    {
                        "type": "text",
                        "text": get_multilingual_text(server_text, language=lang),
                        "size": "sm",
                        "weight": "bold",
                        "margin": "xs"
                    }
                ]
            })

            # 分隔线
            content_rows.append({
                "type": "separator",
                "margin": "md"
            })

        # 语言
        lang_display = {
            'ja': texts['lang_ja'],
            'en': texts['lang_en'],
            'zh': texts['lang_zh']
        }.get(lang, texts['lang_ja'])

        content_rows.append({
            "type": "box",
            "layout": "vertical",
            "margin": "md",
            "contents": [
                {
                    "type": "text",
                    "text": get_multilingual_text(texts['language_label'], language=lang),
                    "size": "xs",
                    "color": "#999999"
                },
                {
                    "type": "text",
                    "text": get_multilingual_text(lang_display, language=lang),
                    "size": "sm",
                    "weight": "bold",
                    "margin": "xs"
                }
            ]
        })

    else:
        # 用户未绑定
        content_rows.append({
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": get_multilingual_text(texts['user_id_label'], language=lang),
                    "size": "xs",
                    "color": "#999999"
                },
                {
                    "type": "text",
                    "text": user_id,
                    "size": "sm",
                    "weight": "bold",
                    "wrap": True,
                    "margin": "xs"
                }
            ]
        })

        content_rows.append({
            "type": "separator",
            "margin": "md"
        })

        content_rows.append({
            "type": "box",
            "layout": "vertical",
            "margin": "md",
            "contents": [
                {
                    "type": "text",
                    "text": f"❌ {get_multilingual_text(texts['not_bound'], language=lang)}",
                    "size": "sm",
                    "color": "#FF0000"
                }
            ]
        })

    # 创建 bubble
    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": get_multilingual_text(texts['title'], language=lang),
                    "weight": "bold",
                    "size": "lg",
                    "color": "#FFFFFF"
                }
            ],
            "paddingAll": "16px",
            "backgroundColor": "#000000"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": content_rows,
            "paddingAll": "16px"
        }
    }

    return FlexMessage(
        alt_text=get_multilingual_text(texts['alt_text'], language=lang),
        contents=FlexContainer.from_dict(bubble)
    )

# ============================================================
# 更新结果 Flex Message / Update Result Flex Message
# ============================================================

update_result_flex_text = {
    'title_success': {
        'ja': '✅ アップデート完了',
        'en': '✅ Update Completed',
        'zh': '✅ 更新完成'
    },
    'title_error': {
        'ja': '⚠️ アップデートエラー',
        'en': '⚠️ Update Error',
        'zh': '⚠️ 更新错误'
    },
    'username_label': {
        'ja': 'プレイヤー名',
        'en': 'Player Name',
        'zh': '玩家名称'
    },
    'rating_label': {
        'ja': 'レーティング',
        'en': 'Rating',
        'zh': 'Rating'
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
        'ja': 'ステータス',
        'en': 'Status',
        'zh': '状态'
    },
    'success': {
        'ja': '成功',
        'en': 'Success',
        'zh': '成功'
    },
    'failed': {
        'ja': '失敗',
        'en': 'Failed',
        'zh': '失败'
    },
    'alt_text_success': {
        'ja': 'アップデート完了',
        'en': 'Update Completed',
        'zh': '更新完成'
    },
    'alt_text_error': {
        'ja': 'アップデートエラー',
        'en': 'Update Error',
        'zh': '更新错误'
    }
}

def generate_update_result_flex(user_id, username, rating, update_time, elapsed_time, func_status, success=True):
    """
    生成更新结果 Flex Message

    Args:
        user_id: 用户ID
        username: 用户名
        rating: Rating 值
        update_time: 更新时间
        elapsed_time: 耗时（秒）
        func_status: 各功能状态字典
        friends_count: 好友列表数量
        success: 是否成功

    Returns:
        FlexMessage: 更新结果 Flex Message
    """
    lang = get_user_language(user_id)
    texts = update_result_flex_text

    # 格式化耗时
    if elapsed_time < 60:
        elapsed_str = f"{elapsed_time:.2f}s"
    else:
        minutes = int(elapsed_time // 60)
        seconds = elapsed_time % 60
        elapsed_str = f"{minutes}m {seconds:.1f}s"

    # 构建内容行
    content_rows = []

    # UserName
    content_rows.append({
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "text": get_multilingual_text(texts['username_label'], language=lang),
                "size": "xs",
                "color": "#999999"
            },
            {
                "type": "text",
                "text": username,
                "size": "sm",
                "weight": "bold",
                "margin": "xs"
            }
        ]
    })

    # 分隔线
    content_rows.append({
        "type": "separator",
        "margin": "md"
    })

    # Rating
    content_rows.append({
        "type": "box",
        "layout": "vertical",
        "margin": "md",
        "contents": [
            {
                "type": "text",
                "text": get_multilingual_text(texts['rating_label'], language=lang),
                "size": "xs",
                "color": "#999999"
            },
            {
                "type": "text",
                "text": str(rating),
                "size": "sm",
                "weight": "bold",
                "margin": "xs"
            }
        ]
    })

    # 分隔线
    content_rows.append({
        "type": "separator",
        "margin": "md"
    })

    # 更新时间
    tz_str = format_timezone_string(user_id)
    content_rows.append({
        "type": "box",
        "layout": "vertical",
        "margin": "md",
        "contents": [
            {
                "type": "text",
                "text": f"{get_multilingual_text(texts['update_time_label'], language=lang)} {tz_str}",
                "size": "xs",
                "color": "#999999"
            },
            {
                "type": "text",
                "text": update_time,
                "size": "sm",
                "weight": "bold",
                "margin": "xs"
            }
        ]
    })

    # 分隔线
    content_rows.append({
        "type": "separator",
        "margin": "md"
    })

    # 耗时
    content_rows.append({
        "type": "box",
        "layout": "vertical",
        "margin": "md",
        "contents": [
            {
                "type": "text",
                "text": get_multilingual_text(texts['elapsed_time_label'], language=lang),
                "size": "xs",
                "color": "#999999"
            },
            {
                "type": "text",
                "text": elapsed_str,
                "size": "sm",
                "weight": "bold",
                "margin": "xs",
                "color": "#17B169" if success else "#FF3B30"
            }
        ]
    })

    # 分隔线
    content_rows.append({
        "type": "separator",
        "margin": "md"
    })

    # 状态详情
    status_contents = [
        {
            "type": "text",
            "text": get_multilingual_text(texts['status_label'], language=lang),
            "size": "xs",
            "color": "#999999"
        }
    ]

    for func_name, status in func_status.items():
        # Favorite Friends 特殊处理：显示数量
        if func_name == "Favorite Friends":
            status_text = f"{status}"
        else:
            status_text = get_multilingual_text(texts['success'], language=lang) if status else get_multilingual_text(texts['failed'], language=lang)

        status_color = "#17B169" if status else "#FF3B30"
        status_contents.append({
            "type": "text",
            "text": f"・{func_name}: {status_text}",
            "size": "xs",
            "color": status_color,
            "margin": "sm"
        })

    content_rows.append({
        "type": "box",
        "layout": "vertical",
        "margin": "md",
        "contents": status_contents
    })

    # 获取随机tip和ad并添加到内容中
    random_tip = get_random_tip()
    random_ad = get_random_ad()

    # 分割线
    if random_tip or random_ad:
        content_rows.append({
            "type": "separator",
            "margin": "md"
        })

    # 添加tip
    if random_tip:
        tip_box = generate_tip_ad_box(random_tip, lang)
        content_rows.append(tip_box)

    # 添加ad
    if random_ad:
        ad_box = generate_tip_ad_box(random_ad, lang)
        content_rows.append(ad_box)

    # 创建 bubble
    title_text = texts['title_success'] if success else texts['title_error']
    header_color = "#17B169" if success else "#FF3B30"

    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": get_multilingual_text(title_text, language=lang),
                    "weight": "bold",
                    "size": "lg",
                    "color": "#FFFFFF"
                }
            ],
            "paddingAll": "16px",
            "backgroundColor": header_color
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": content_rows,
            "paddingAll": "16px"
        }
    }

    alt_text = texts['alt_text_success'] if success else texts['alt_text_error']
    return FlexMessage(
        alt_text=get_multilingual_text(alt_text, language=lang),
        contents=FlexContainer.from_dict(bubble)
    )

def generate_tip_ad_box(tip_ad, lang):
    """
    生成 Tip/Ad 小容器

    Args:
        tip_ad: tip/ad 数据字典
        lang: 语言代码

    Returns:
        dict: Flex Box 字典
    """
    # 获取对应语言的文本
    text_dict = tip_ad.get('text', {})
    text = text_dict.get(lang, text_dict.get('ja', ''))

    # 确定颜色和图标
    is_ad = tip_ad.get('type') == 'ad'
    bg_color = "#FFF4E6" if is_ad else "#F0EFFF"  # 浅橙色 or 浅紫色背景
    text_color = "#FF9500" if is_ad else "#5856D6"
    icon = "📢" if is_ad else "💡"

    # 构建内容
    box_contents = [
        {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": icon,
                    "size": "md",
                    "flex": 0
                },
                {
                    "type": "text",
                    "text": text,
                    "size": "xs",
                    "wrap": True,
                    "color": "#666666",
                    "flex": 1,
                    "margin": "sm"
                }
            ]
        }
    ]

    # 如果有按钮，添加按钮
    if 'button' in tip_ad:
        button_info = tip_ad['button']
        button_type = button_info.get('type', 'uri')
        button_label_dict = button_info.get('label', {})
        button_label = button_label_dict.get(lang, button_label_dict.get('ja', ''))
        button_value = button_info.get('value', '')

        # 如果label为空，使用默认值
        if not button_label:
            default_labels = {
                'uri': {'ja': '詳細を見る', 'en': 'View Details', 'zh': '查看详情'},
                'message': {'ja': '試してみる', 'en': 'Try it', 'zh': '尝试一下'}
            }
            button_label = default_labels.get(button_type, {}).get(lang, 'Go')

        # 添加箭头到按钮标签
        button_label_with_arrow = f"{button_label} →"

        # 根据按钮类型创建action
        if button_type == 'uri':
            action = {
                "type": "uri",
                "label": button_label_with_arrow,
                "uri": button_value
            }
        else:  # message
            action = {
                "type": "uri",
                "label": button_label_with_arrow,
                "uri": f"https://line.me/R/oaMessage/{LINE_ACCOUNT_ID}/?{button_value}"
            }

        # 添加按钮
        box_contents.append({
            "type": "button",
            "action": action,
            "style": "link",
            "height": "sm",
            "color": text_color,
            "margin": "sm"
        })

    # 构建最终的box
    tip_ad_box = {
        "type": "box",
        "layout": "vertical",
        "contents": box_contents,
        "backgroundColor": bg_color,
        "cornerRadius": "md",
        "paddingAll": "12px",
        "margin": "md"
    }

    return tip_ad_box

# ============================================================
# 系统错误警报 Flex Message / System Error Alert Flex Message
# ============================================================

def generate_error_alert_flex(error_title, error_details, context, timestamp):
    """
    生成系统错误警报 Flex Message

    Args:
        error_title: 错误标题
        error_details: 错误详情（已截断到合理长度）
        context: 上下文信息字典
        timestamp: 时间戳

    Returns:
        FlexMessage: 系统错误警报 Flex Message
    """
    # 构建内容行
    content_rows = []

    # 时间
    content_rows.append({
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "text": "Time",
                "size": "xs",
                "color": "#999999"
            },
            {
                "type": "text",
                "text": timestamp,
                "size": "sm",
                "weight": "bold",
                "margin": "xs"
            }
        ]
    })

    # 分隔线
    content_rows.append({
        "type": "separator",
        "margin": "md"
    })

    # 错误标题
    content_rows.append({
        "type": "box",
        "layout": "vertical",
        "margin": "md",
        "contents": [
            {
                "type": "text",
                "text": "Error",
                "size": "xs",
                "color": "#999999"
            },
            {
                "type": "text",
                "text": error_title,
                "size": "sm",
                "weight": "bold",
                "margin": "xs",
                "wrap": True,
                "color": "#FF6B6B"
            }
        ]
    })

    # 分隔线
    content_rows.append({
        "type": "separator",
        "margin": "md"
    })

    # 错误详情
    # 限制长度避免 flex message 过大
    detail_text = error_details[:800] + "..." if len(error_details) > 800 else error_details

    content_rows.append({
        "type": "box",
        "layout": "vertical",
        "margin": "md",
        "contents": [
            {
                "type": "text",
                "text": "Details",
                "size": "xs",
                "color": "#999999"
            },
            {
                "type": "text",
                "text": detail_text,
                "size": "xs",
                "margin": "xs",
                "wrap": True,
                "color": "#666666"
            }
        ]
    })

    # 如果有上下文信息
    if context:
        # 分隔线
        content_rows.append({
            "type": "separator",
            "margin": "md"
        })

        # 上下文标题
        context_contents = [
            {
                "type": "text",
                "text": "Context",
                "size": "xs",
                "color": "#999999"
            }
        ]

        # 添加上下文项
        for key, value in list(context.items())[:5]:  # 最多显示5项
            context_contents.append({
                "type": "text",
                "text": f"・{key}: {value}",
                "size": "xs",
                "color": "#666666",
                "margin": "sm",
                "wrap": True
            })

        content_rows.append({
            "type": "box",
            "layout": "vertical",
            "margin": "md",
            "contents": context_contents
        })

    # 创建 bubble
    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🚨 System Error Alert",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#FFFFFF"
                }
            ],
            "paddingAll": "16px",
            "backgroundColor": "#FF3B30"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": content_rows,
            "paddingAll": "16px"
        }
    }

    return FlexMessage(
        alt_text="🚨 System Error Alert",
        contents=FlexContainer.from_dict(bubble)
    )


def generate_calc_result_flex(notes, scores, difficulty=None, level=None):
    """
    生成计算结果 Flex Message

    Args:
        notes: dict with keys ['tap', 'hold', 'slide', 'touch', 'break']
        scores: dict with score calculations
        difficulty: 可选，难度名称 (如 'master', 'remaster')
        level: 可选，难度等级 (如 14.5)

    Returns:
        FlexMessage: 计算结果 Flex Message
    """
    bubble = _build_calc_bubble(notes, scores, difficulty, level)
    return FlexMessage(
        alt_text="Calc Result",
        contents=FlexContainer.from_dict(bubble)
    )


def generate_calc_carousel(calc_bubbles_data):
    """
    生成calc结果的carousel Flex Message

    Args:
        calc_bubbles_data: list of tuples (notes, scores, difficulty, level)

    Returns:
        FlexMessage: Carousel格式的calc结果
    """
    if len(calc_bubbles_data) == 1:
        # 只有一个bubble，直接返回单个flex message
        notes, scores, difficulty, level = calc_bubbles_data[0]
        return generate_calc_result_flex(notes, scores, difficulty, level)

    # 多个bubble，构建carousel
    bubbles = []
    for notes, scores, difficulty, level in calc_bubbles_data:
        # 直接构建bubble字典，复制generate_calc_result_flex的逻辑
        bubble = _build_calc_bubble(notes, scores, difficulty, level)
        bubbles.append(bubble)

    carousel = {
        "type": "carousel",
        "contents": bubbles
    }
    return FlexMessage(
        alt_text="Calc Results",
        contents=FlexContainer.from_dict(carousel)
    )


def _build_calc_bubble(notes, scores, difficulty=None, level=None):
    """
    构建calc结果的bubble字典（内部辅助函数）

    Args:
        notes: dict with keys ['tap', 'hold', 'slide', 'touch', 'break']
        scores: dict with score calculations
        difficulty: 可选，难度名称
        level: 可选，难度等级

    Returns:
        dict: bubble字典
    """
    # Note类型和数量
    note_contents = []
    note_labels = {
        'tap': 'TAP',
        'hold': 'HOLD',
        'slide': 'SLIDE',
        'touch': 'TOUCH',
        'break': 'BREAK'
    }

    for key in ['tap', 'hold', 'slide', 'touch', 'break']:
        # 跳过没有 touch 数据的情况
        if key == 'touch' and (not notes.get(key) or notes.get(key) == 0):
            continue

        note_contents.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": note_labels[key],
                    "size": "sm",
                    "color": "#666666",
                    "flex": 0,
                    "weight": "bold"
                },
                {
                    "type": "text",
                    "text": str(notes[key]),
                    "size": "sm",
                    "color": "#111111",
                    "align": "end"
                }
            ],
            "margin": "sm"
        })

    # 分隔线
    separator = {
        "type": "separator",
        "margin": "md"
    }

    # 判定分数
    score_contents = []
    note_groups = [
        ('tap', ['tap_great', 'tap_good', 'tap_miss']),
        ('hold', ['hold_great', 'hold_good', 'hold_miss']),
        ('slide', ['slide_great', 'slide_good', 'slide_miss']),
        ('touch', ['touch_great', 'touch_good', 'touch_miss']),
        ('break', ['break_high_perfect', 'break_low_perfect', 'break_high_great',
                   'break_middle_great', 'break_low_great', 'break_good', 'break_miss'])
    ]

    def get_judgement_color(score_name):
        if 'perfect' in score_name:
            return "#FF9500"
        elif 'great' in score_name:
            return "#FF69B4"
        elif 'good' in score_name:
            return "#34C759"
        elif 'miss' in score_name:
            return "#999999"
        return "#666666"

    first_group = True
    for note_type, judgements in note_groups:
        # 跳过没有 touch 数据的情况
        if note_type == 'touch' and (not notes.get('touch') or notes.get('touch') == 0):
            continue

        if not first_group:
            score_contents.append({
                "type": "separator",
                "margin": "md"
            })
        first_group = False

        for score_name in judgements:
            if score_name in scores:
                score_value = scores[score_name]
                score_contents.append({
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": score_name.replace('_', ' ').title(),
                            "size": "xs",
                            "color": "#666666",
                            "flex": 3
                        },
                        {
                            "type": "text",
                            "text": f"-{score_value:.5f}%",
                            "size": "xs",
                            "color": get_judgement_color(score_name),
                            "align": "end",
                            "flex": 2
                        }
                    ],
                    "margin": "sm"
                })

    # 难度映射和颜色
    difficulty_map = {
        'basic': {'name': 'BASIC', 'color': '#34C759'},
        'advanced': {'name': 'ADVANCED', 'color': '#FF9500'},
        'expert': {'name': 'EXPERT', 'color': '#FF3B30'},
        'master': {'name': 'MASTER', 'color': '#AF52DE'},
        'remaster': {'name': 'Re:MASTER', 'color': '#D4A5F5'},
        'utage': {'name': 'UTAGE', 'color': '#000000'}
    }

    # 生成标题文本
    if difficulty:
        diff_info = difficulty_map.get(difficulty, {'name': difficulty.upper(), 'color': '#007AFF'})
        title_text = f"🗒️ {diff_info['name']}"
        if level:
            title_text += f" (Lv. {level:.1f})"
        header_color = diff_info['color']
    else:
        title_text = "🗒️ Note Distribution"
        header_color = "#007AFF"

    # 计算 tap_great 容错数
    tap_great_tolerance = []
    if 'tap_great' in scores and scores['tap_great'] > 0:
        # 从 101% 到 100.5000%
        max_tap_great_to_half = int(0.5 / scores['tap_great'])
        # 从 101% 到 100.0000%
        max_tap_great_to_full = int(1.0 / scores['tap_great'])

        tap_great_tolerance.append({
            "type": "separator",
            "margin": "lg"
        })

        tap_great_tolerance.append({
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "100.5000%",
                            "size": "xs",
                            "color": "#666666",
                            "flex": 3,
                            "weight": "bold"
                        },
                        {
                            "type": "text",
                            "text": f"Max {max_tap_great_to_half} TAP GREAT",
                            "size": "xs",
                            "color": "#FF69B4",
                            "align": "end",
                            "flex": 4,
                            "weight": "bold"
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "100.0000%",
                            "size": "xs",
                            "color": "#666666",
                            "flex": 3,
                            "weight": "bold"
                        },
                        {
                            "type": "text",
                            "text": f"Max {max_tap_great_to_full} TAP GREAT",
                            "size": "xs",
                            "color": "#FF69B4",
                            "align": "end",
                            "flex": 4,
                            "weight": "bold"
                        }
                    ],
                    "margin": "sm"
                }
            ],
            "backgroundColor": "#FFF5F0",
            "cornerRadius": "md",
            "paddingAll": "12px",
            "margin": "md"
        })

    # 构建body内容
    body_contents = score_contents if difficulty else (note_contents + [separator] + score_contents)
    body_contents.extend(tap_great_tolerance)

    # 构建bubble
    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": title_text,
                    "weight": "bold",
                    "size": "lg",
                    "color": "#FFFFFF"
                }
            ],
            "paddingAll": "16px",
            "backgroundColor": header_color
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": body_contents,
            "paddingAll": "16px"
        }
    }

    return bubble


def _generate_search_results_flex_internal(user_id, matching_songs, search_type='song', id_use=None):
    """
    生成搜索结果列表 Flex Message（内部通用函数）

    Args:
        user_id: 用户ID
        matching_songs: 匹配的歌曲列表
        search_type: 搜索类型 ('song' 或 'record')
        id_use: 使用的ID

    Returns:
        FlexMessage: 搜索结果列表
    """
    # 获取用户语言
    language = get_user_language(user_id)

    id_use_text = ""
    if id_use:
        id_use_text = f"&id_use={id_use}"

    # 构建歌曲行
    song_rows = []

    # 类型映射
    type_map = {
        'dx': 'DX',
        'std': 'STD',
        'utage': 'UTAGE'
    }

    # 搜索类型配置
    search_config = {
        'song': {
            'command': 'search',
            'title': {
                'ja': f'検索結果 ({len(matching_songs)}件)',
                'en': f'Search Results ({len(matching_songs)})',
                'zh': f'搜索结果 ({len(matching_songs)}条)'
            },
            'color': '#34C759'
        },
        'record': {
            'command': 'search-record',
            'title': {
                'ja': f'レコード検索結果 ({len(matching_songs)}件)',
                'en': f'Record Search Results ({len(matching_songs)})',
                'zh': f'成绩搜索结果 ({len(matching_songs)}条)'
            },
            'color': '#FF9500'
        }
    }

    config = search_config[search_type]

    for song in matching_songs[:20]:  # 最多显示20首
        song_id = song.get('id', '')
        song_type = type_map.get(song.get('type', ''), song.get('type', '').upper())

        song_rows.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": song.get('title', 'Unknown'),
                            "size": "sm",
                            "weight": "bold",
                            "wrap": True,
                            "maxLines": 2,
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": song_type,
                            "size": "xs",
                            "color": "#999999",
                            "margin": "xs"
                        }
                    ],
                    "flex": 3
                },
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "→",
                        "data": f"{config['command']} {song_id}{id_use_text}",
                        "displayText": f"{config['command']} {song_id}"
                    },
                    "style": "primary",
                    "height": "sm",
                    "flex": 1
                }
            ],
            "margin": "md",
            "spacing": "sm"
        })

        # 添加分隔线（最后一首除外）
        if song != matching_songs[-1] and len(song_rows) < 40:
            song_rows.append({
                "type": "separator",
                "margin": "md"
            })

    # 标题文本
    title_text = config['title'].get(language, config['title']['ja'])

    # 构建bubble
    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": title_text,
                    "weight": "bold",
                    "size": "lg",
                    "color": "#FFFFFF"
                }
            ],
            "paddingAll": "16px",
            "backgroundColor": config['color']
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": song_rows,
            "paddingAll": "16px"
        }
    }

    return FlexMessage(
        alt_text=title_text,
        contents=FlexContainer.from_dict(bubble)
    )


def generate_search_results_flex(user_id, matching_songs):
    """
    生成搜索结果列表 Flex Message

    Args:
        user_id: 用户ID
        matching_songs: 匹配的歌曲列表

    Returns:
        FlexMessage: 搜索结果列表
    """
    return _generate_search_results_flex_internal(user_id, matching_songs, 'song')


def generate_search_record_results_flex(user_id, id_use, matching_songs):
    """
    生成成绩搜索结果列表 Flex Message

    Args:
        user_id: 用户ID
        matching_songs: 匹配的歌曲列表（包含游玩记录）

    Returns:
        FlexMessage: 成绩搜索结果列表
    """
    return _generate_search_results_flex_internal(user_id, matching_songs, 'record', id_use)


def generate_friend_buttons(user_id, alt_text, friend_list, group_size):
    """
    生成好友列表 Flex Message（极简黑白风格）

    Args:
        alt_text: 替代文本
        friend_list: 好友列表 [{"name": "text", "rating": "text", "friend_id": "text"}]
        group_size: 每页显示的好友数（默认6个）

    Returns:
        FlexMessage
    """
    if not friend_list:
        return friend_error(user_id)

    bubbles = []
    total_pages = (len(friend_list) + group_size - 1) // group_size

    for page_idx in range(0, len(friend_list), group_size):
        group = friend_list[page_idx:page_idx + group_size]
        page_num = page_idx // group_size + 1

        # 创建好友行
        friend_rows = []
        for idx, friend in enumerate(group):
            # 解析信息
            name = friend["name"]
            rating = friend["rating"]
            friend_id = friend["friend_id"]

            # 创建单行（第一个不需要上边距）
            row = {
                "type": "box",
                "layout": "horizontal",
                "spacing": "md",
                "margin": "md" if idx > 0 else "none",
                "contents": [
                    # 左侧：名字和Rating
                    {
                        "type": "box",
                        "layout": "vertical",
                        "flex": 3,
                        "contents": [
                            {
                                "type": "text",
                                "text": name,
                                "size": "sm",
                                "weight": "bold",
                                "wrap": True,
                                "maxLines": 2
                            },
                            {
                                "type": "text",
                                "text": f"Rating: {rating}",
                                "size": "xs",
                                "color": "#999999",
                                "margin": "xs"
                            }
                        ]
                    },
                    # 右侧：按钮（只显示符号）
                    {
                        "type": "button",
                        "flex": 0,
                        "style": "secondary",
                        "height": "sm",
                        "action": {
                            "type": "postback",
                            "label": "→",
                            "data": f"friend-b50 {friend_id}",
                            "displayText": get_multilingual_text(view_friend_b50_text, user_id).format(name=name)
                        }
                    }
                ]
            }

            # 添加分隔线（除了最后一个）
            if idx < len(group) - 1:
                friend_rows.append(row)
                friend_rows.append({
                    "type": "separator",
                    "margin": "sm"
                })
            else:
                friend_rows.append(row)

        # 创建 bubble
        bubble = {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": alt_text,
                        "weight": "bold",
                        "size": "lg"
                    },
                    {
                        "type": "text",
                        "text": f"Page {page_num}/{total_pages} • {len(group)} friends",
                        "size": "xs",
                        "color": "#999999",
                        "margin": "sm"
                    },
                    {
                        "type": "separator",
                        "color": "#DDDDDD",
                        "margin": "md"
                    }
                ],
                "paddingAll": "16px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": friend_rows,
                "paddingAll": "16px"
            }
        }

        bubbles.append(bubble)

    # 创建 carousel
    if len(bubbles) == 1:
        # 只有一页，直接返回 bubble
        flex_dict = bubbles[0]
    else:
        # 多页，使用 carousel
        flex_dict = {
            "type": "carousel",
            "contents": bubbles
        }

    return FlexMessage(
        alt_text=alt_text,
        contents=FlexContainer.from_dict(flex_dict)
    )


def generate_rc_flex(level: float, rc_data: list, user_id=None):
    """
    生成 Rating Constant 对照表 Flex Message

    Args:
        level: 谱面定数 (如 14.5)
        rc_data: Rating 对照数据列表 [(score, rating), ...]
        user_id: 用户ID（用于多语言）

    Returns:
        FlexMessage: Rating 对照表
    """
    language = get_user_language(user_id)

    # 标题文本
    title_texts = {
        'ja': f'定数 {level} のRating対照表',
        'en': f'Rating Chart for {level}',
        'zh': f'定数 {level} Rating 对照表'
    }
    title_text = title_texts.get(language, title_texts['ja'])

    # 按达成率整数部分分组（100.xxxx、99.xxxx、98.xxxx...）
    score_groups = {}
    for score, rating in rc_data:
        score_int = int(score)
        if score_int not in score_groups:
            score_groups[score_int] = []
        score_groups[score_int].append((score, rating))

    # 获取所有达成率整数值并倒序排列（从高到低）
    sorted_score_ints = sorted(score_groups.keys(), reverse=True)

    # 构建单列内容
    content_rows = []

    for i, score_int in enumerate(sorted_score_ints):
        entries = score_groups[score_int]

        # 当整数部分变化时，添加分隔线（第一组除外）
        if i > 0:
            content_rows.append({
                "type": "separator",
                "margin": "md",
                "color": "#DDDDDD"
            })

        # 按达成率倒序排列
        entries.sort(key=lambda x: x[0], reverse=True)

        # 达成率列表
        for score, rating in entries:
            score_text = f"{score:.4f}%"
            is_special = (score_text in ["100.5000%", "100.0000%", "99.5000%", "99.0000%", "98.0000%", "97.0000%"])

            content_rows.append({
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "text",
                        "text": score_text,
                        "size": "sm",
                        "color": "#000000" if is_special else "#666666",
                        "align": "start"
                    },
                    {
                        "type": "text",
                        "text": "→",
                        "size": "sm",
                        "color": "#222222" if is_special else "#999999",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": f"{rating}",
                        "size": "sm",
                        "color": "#000000" if is_special else "#666666",
                        "align": "end"
                    }
                ],
                "margin": "xs",
                "spacing": "md"
            })

    # 构建 bubble
    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": title_text,
                    "weight": "bold",
                    "size": "lg",
                    "color": "#FFFFFF"
                }
            ],
            "paddingAll": "16px",
            "backgroundColor": "#AF52DE"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": content_rows,
            "paddingAll": "16px"
        }
    }

    return FlexMessage(
        alt_text=title_text,
        contents=FlexContainer.from_dict(bubble)
    )

def generate_bot_status_flex(uptime_str, cpu_percent, memory_percent, memory_used_gb, total_memory, avg_response_time, user_id=None):
    """
    生成 Bot 状态信息 Flex Message

    Args:
        uptime_str: 运行时长字符串
        cpu_percent: CPU 使用率
        memory_percent: 内存使用率百分比（已弃用）
        memory_used_gb: 已使用内存（已弃用）
        total_memory: 总内存（已弃用）
        avg_response_time: 平均响应时间字符串
        user_id: 用户ID（用于多语言）

    Returns:
        FlexMessage: Bot 状态信息
    """
    lang = get_user_language(user_id)

    # 多语言文本
    texts = {
        'title': {
            'ja': 'JiETNG 稼働状態',
            'en': 'JiETNG Service Status',
            'zh': 'JiETNG 运行状态'
        },
        'uptime': {
            'ja': '稼働時間',
            'en': 'Uptime',
            'zh': '运行时长'
        },
        'cpu': {
            'ja': 'CPU 使用率',
            'en': 'CPU Usage',
            'zh': 'CPU 使用率'
        },
        'response': {
            'ja': '平均応答',
            'en': 'Avg Response',
            'zh': '平均响应'
        }
    }

    content_rows = [
        # Uptime
        {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": texts['uptime'][lang],
                    "size": "xs",
                    "color": "#666666",
                    "flex": 0
                },
                {
                    "type": "text",
                    "text": uptime_str,
                    "size": "sm",
                    "weight": "bold",
                    "color": "#111111",
                    "align": "end"
                }
            ],
            "margin": "none"
        },
        {
            "type": "separator",
            "margin": "md"
        },
        # CPU Usage
        {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": texts['cpu'][lang],
                    "size": "xs",
                    "color": "#666666",
                    "flex": 0
                },
                {
                    "type": "text",
                    "text": f"{cpu_percent}%",
                    "size": "sm",
                    "weight": "bold",
                    "color": "#FF9500" if cpu_percent > 70 else "#34C759",
                    "align": "end"
                }
            ],
            "margin": "md"
        },
        {
            "type": "separator",
            "margin": "md"
        },
        # Average Response Time
        {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": texts['response'][lang],
                    "size": "xs",
                    "color": "#666666",
                    "flex": 0
                },
                {
                    "type": "text",
                    "text": avg_response_time,
                    "size": "sm",
                    "weight": "bold",
                    "color": "#AF52DE",
                    "align": "end"
                }
            ],
            "margin": "md"
        }
    ]
    
    # 获取随机tip和ad并添加到内容中
    random_tip = get_random_tip()
    random_ad = get_random_ad()

    # 分割线
    if random_tip or random_ad:
        content_rows.append({
            "type": "separator",
            "margin": "md"
        })

    # 添加tip
    if random_tip:
        tip_box = generate_tip_ad_box(random_tip, lang)
        content_rows.append(tip_box)

    # 添加ad
    if random_ad:
        ad_box = generate_tip_ad_box(random_ad, lang)
        content_rows.append(ad_box)

    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": texts['title'][lang],
                    "weight": "bold",
                    "size": "lg",
                    "color": "#000000"
                }
            ],
        "paddingTop": "16px",
        "paddingBottom": "0px",
        "paddingStart": "16px",
        "paddingEnd": "16px",
        "backgroundColor": "#FFFFFF"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": content_rows,
            "paddingAll": "16px"
        }
    }

    return FlexMessage(
        alt_text="Service Status",
        contents=FlexContainer.from_dict(bubble)
    )
