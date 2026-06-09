from __future__ import annotations

from typing import Any

import discord
from discord import app_commands


MESSAGES: dict[str, dict[str, str]] = {
    "api_token_invalid": {
        "zh": "JiETNG API token 无效或已过期。",
        "ja": "JiETNG API token が無効、または期限切れです。",
        "en": "The JiETNG API token is invalid or expired.",
    },
    "permission_denied": {
        "zh": "当前 JiETNG API token 没有访问这个用户的权限。",
        "ja": "現在の JiETNG API token には、このユーザーへのアクセス権がありません。",
        "en": "The current JiETNG API token cannot access this user.",
    },
    "not_found": {
        "zh": "没有找到数据：{message}",
        "ja": "データが見つかりません：{message}",
        "en": "Data not found: {message}",
    },
    "bad_params": {
        "zh": "参数不正确：{message}",
        "ja": "パラメータが正しくありません：{message}",
        "en": "Invalid parameters: {message}",
    },
    "rate_limited": {
        "zh": "请求太频繁了，稍后再试。",
        "ja": "リクエストが多すぎます。しばらくしてから再試行してください。",
        "en": "Too many requests. Please try again later.",
    },
    "queue_full": {
        "zh": "JiETNG 服务端队列已满，稍后再试。",
        "ja": "JiETNG サーバーのキューがいっぱいです。しばらくしてから再試行してください。",
        "en": "The JiETNG server queue is full. Please try again later.",
    },
    "already_bound": {
        "zh": "这个 JiETNG 用户已经绑定过 SEGA 账号。请使用 `/rebind` 获取换绑链接。",
        "ja": "この JiETNG ユーザーは既に SEGA アカウントと連携済みです。`/rebind` を使って再連携リンクを取得してください。",
        "en": "This JiETNG user is already bound to a SEGA account. Use `/rebind` for a rebind link.",
    },
    "api_error": {
        "zh": "JiETNG API 错误：{message}",
        "ja": "JiETNG API エラー：{message}",
        "en": "JiETNG API error: {message}",
    },
    "self_only": {
        "zh": "这个命令只能访问你自己绑定的 JiETNG user_id。要切换账号，请先 `/unlink` 再 `/link`。",
        "ja": "このコマンドは、自分に紐づいた JiETNG user_id のみ利用できます。切り替える場合は先に `/unlink` してから `/link` してください。",
        "en": "This command can only access your linked JiETNG user_id. To switch accounts, use `/unlink` then `/link`.",
    },
    "need_link": {
        "zh": "请先使用 `/link user_id` 或 `/bind`。",
        "ja": "先に `/link user_id` または `/bind` を使ってください。",
        "en": "Use `/link user_id` or `/bind` first.",
    },
    "profile_user_id": {"zh": "user_id", "ja": "user_id", "en": "user_id"},
    "profile_name": {"zh": "用户", "ja": "ユーザー", "en": "User"},
    "profile_rating": {"zh": "Rating", "ja": "Rating", "en": "Rating"},
    "profile_version": {"zh": "服务器", "ja": "サーバー", "en": "Server"},
    "profile_updated": {"zh": "更新时间", "ja": "更新日時", "en": "Updated"},
    "no_song": {
        "zh": "没有找到歌曲。",
        "ja": "楽曲が見つかりませんでした。",
        "en": "No songs found.",
    },
    "button_not_for_you": {
        "zh": "这个选择按钮不是给你的。",
        "ja": "この選択ボタンはあなた向けではありません。",
        "en": "This selection button is not for you.",
    },
    "missing_song_id": {
        "zh": "搜索结果缺少歌曲 ID，无法生成图片。",
        "ja": "検索結果に楽曲 ID がないため、画像を生成できません。",
        "en": "The search result has no song ID, so an image cannot be generated.",
    },
    "missing_user_id": {
        "zh": "缺少 JiETNG user_id，无法生成成绩图。",
        "ja": "JiETNG user_id がないため、成績画像を生成できません。",
        "en": "Missing JiETNG user_id, so the record image cannot be generated.",
    },
    "linked_ready": {
        "zh": "`{user_id}` 已经绑定到当前 Discord 账号，并且权限已可用。",
        "ja": "`{user_id}` はこの Discord アカウントに紐づいており、権限も利用可能です。",
        "en": "`{user_id}` is already linked to this Discord account and permission is ready.",
    },
    "global_permission_not_linked": {
        "zh": "这个 JiETNG user_id 已经授权过当前 bot 的全局 API token，但无法确认是你本人授权。\n为了避免 Discord 用户之间串号，我没有创建本地绑定。请使用 `/bind` 创建 Discord 专用账号，或让该用户先在 JiETNG 侧撤销这个 token 后重新 `/link`。",
        "ja": "この JiETNG user_id は既にこの bot の共有 API token に権限を付与していますが、あなた本人の許可か確認できません。\nDiscord ユーザー間の取り違えを防ぐため、ローカル紐づけは作成していません。`/bind` で Discord 専用アカウントを作成するか、JiETNG 側でこの token を取り消してから再度 `/link` してください。",
        "en": "This JiETNG user_id has already granted access to this bot's shared API token, but I cannot verify that it was granted by you.\nTo avoid cross-account leaks between Discord users, I did not create a local link. Use `/bind` to create a Discord-specific account, or revoke this token on JiETNG and run `/link` again.",
    },
    "request_pending_linked": {
        "zh": "`{user_id}` 已经绑定到当前 Discord 账号，权限申请仍在等待 JiETNG 用户确认。",
        "ja": "`{user_id}` はこの Discord アカウントに紐づいていますが、権限リクエストはまだ承認待ちです。",
        "en": "`{user_id}` is linked to this Discord account, but the permission request is still pending.",
    },
    "request_pending_not_linked": {
        "zh": "这个 JiETNG user_id 已经有一条等待处理的 bot 权限申请。\n为了避免把别人的待处理申请绑定到你这里，我没有创建本地绑定。请等待原申请处理，或让该用户拒绝后再由你重新 `/link`。",
        "ja": "この JiETNG user_id には既に未処理の bot 権限リクエストがあります。\n他人の未処理リクエストをあなたに紐づけないため、ローカル紐づけは作成していません。元のリクエストが処理されるのを待つか、拒否後に改めて `/link` してください。",
        "en": "This JiETNG user_id already has a pending bot permission request.\nTo avoid linking someone else's pending request to you, I did not create a local link. Wait for the existing request to be handled, or ask the user to reject it and run `/link` again.",
    },
    "permission_requested": {
        "zh": "已向 `{user_id}` 发起访问权限申请，request_id: `{request_id}`。\n用户同意后即可使用 `/b50`、`/profile`、`/export` 等命令。",
        "ja": "`{user_id}` にアクセス権リクエストを送信しました。request_id: `{request_id}`。\n承認後、`/b50`、`/profile`、`/export` などが使えます。",
        "en": "Permission request sent to `{user_id}`. request_id: `{request_id}`.\nAfter approval, you can use `/b50`, `/profile`, `/export`, and more.",
    },
    "unlinked": {
        "zh": "已取消绑定，并已向 JiETNG 服务器请求放弃访问权限。",
        "ja": "連携を解除し、JiETNG サーバーへアクセス権の放棄をリクエストしました。",
        "en": "Unlinked and requested JiETNG server-side permission revocation.",
    },
    "unlinked_local_only": {
        "zh": "已取消本地绑定。服务器端权限没有撤销：{message}",
        "ja": "ローカル連携を解除しました。サーバー側の権限は取り消されませんでした：{message}",
        "en": "Local link removed. Server-side permission was not revoked: {message}",
    },
    "not_linked": {"zh": "你还没有绑定 JiETNG user_id。", "ja": "まだ JiETNG user_id を連携していません。", "en": "You have not linked a JiETNG user_id yet."},
    "already_has_link": {
        "zh": "你已经绑定到 `{linked}`。要切换账号，请先 `/unlink`，再重新 `/link` 或 `/bind`。",
        "ja": "既に `{linked}` に紐づいています。切り替える場合は先に `/unlink` してから `/link` または `/bind` してください。",
        "en": "You are already linked to `{linked}`. To switch accounts, use `/unlink` then `/link` or `/bind`.",
    },
    "has_local_link": {
        "zh": "你已经有本地绑定：`{user_id}`。\n如需绑定或换绑 SEGA 账号，请点击按钮。",
        "ja": "既にローカル連携があります：`{user_id}`。\nSEGA アカウントの連携・再連携はボタンから行ってください。",
        "en": "You already have a local link: `{user_id}`.\nUse the button to bind or rebind your SEGA account.",
    },
    "created_bind": {
        "zh": "已创建 JiETNG user_id：`{user_id}`。\n点击按钮完成绑定。",
        "ja": "JiETNG user_id を作成しました：`{user_id}`。\nボタンから連携を完了してください。",
        "en": "Created JiETNG user_id: `{user_id}`.\nUse the button to complete binding.",
    },
    "default_user_conflict": {
        "zh": "默认 Discord user_id 已存在，但当前 Discord 账号没有本地绑定。为避免串号，我没有继续操作。请联系 JiETNG 管理员处理这个冲突。",
        "ja": "既定の Discord user_id は既に存在しますが、この Discord アカウントにはローカル連携がありません。取り違え防止のため処理を中止しました。JiETNG 管理者に連絡してください。",
        "en": "The default Discord user_id already exists, but this Discord account has no local link. I stopped to avoid cross-account leaks. Contact a JiETNG admin to resolve this conflict.",
    },
    "open_bind": {"zh": "打开绑定页面", "ja": "連携ページを開く", "en": "Open Binding Page"},
    "open_settings": {"zh": "打开设置页面", "ja": "設定ページを開く", "en": "Open Settings"},
    "open_rebind": {"zh": "打开重新绑定页面", "ja": "再連携ページを開く", "en": "Open Rebind Page"},
    "binding_done": {
        "zh": "绑定完成。JiETNG user_id: `{user_id}`\n可以使用 `/sync` 更新成绩，或直接试 `/profile`。",
        "ja": "連携が完了しました。JiETNG user_id: `{user_id}`\n`/sync` で成績を更新するか、`/profile` を試してください。",
        "en": "Binding complete. JiETNG user_id: `{user_id}`\nUse `/sync` to update scores, or try `/profile`.",
    },
    "sync_timeout": {
        "zh": "同步任务已经提交，但 5 分钟内还没有完成。请稍后用 `/profile` 或 `/b50` 查看数据是否更新。",
        "ja": "同期タスクは送信されましたが、5 分以内に完了しませんでした。後で `/profile` または `/b50` で更新を確認してください。",
        "en": "Sync was submitted, but did not finish within 5 minutes. Check later with `/profile` or `/b50`.",
    },
    "sync_done": {"zh": "同步完成。", "ja": "同期が完了しました。", "en": "Sync complete."},
    "sync_result": {"zh": " 结果：`{result}`", "ja": " 結果：`{result}`", "en": " Result: `{result}`"},
    "sync_status": {"zh": "同步任务结束，状态：`{status}`", "ja": "同期タスクが終了しました。状態：`{status}`", "en": "Sync task ended with status: `{status}`"},
    "export_done": {"zh": "导出完成。", "ja": "エクスポートが完了しました。", "en": "Export complete."},
    "open_settings_prompt": {"zh": "点击按钮打开设置页面。", "ja": "ボタンから設定ページを開いてください。", "en": "Use the button to open settings."},
    "open_rebind_prompt": {"zh": "点击按钮打开重新绑定页面。", "ja": "ボタンから再連携ページを開いてください。", "en": "Use the button to open the rebind page."},
}


COMMAND_TRANSLATIONS: dict[str, dict[str, str]] = {
    "cmd.link.desc": {
        "zh": "向 JiETNG 用户请求访问权限并绑定默认 user_id",
        "ja": "JiETNG ユーザーへのアクセス権を申請し、既定の user_id に紐づけます",
        "en": "Request JiETNG access and link a default user_id",
    },
    "cmd.unlink.desc": {
        "zh": "取消当前 Discord 账号的 JiETNG 绑定",
        "ja": "現在の Discord アカウントの JiETNG 連携を解除します",
        "en": "Unlink the JiETNG user_id from this Discord account",
    },
    "cmd.bind.desc": {
        "zh": "首次绑定 SEGA 账号到 JiETNG",
        "ja": "SEGA アカウントを JiETNG に初回連携します",
        "en": "Create a JiETNG user and bind a SEGA account",
    },
    "cmd.profile.desc": {
        "zh": "查看自己的 JiETNG 用户资料",
        "ja": "自分の JiETNG プロフィールを表示します",
        "en": "Show your JiETNG profile",
    },
    "cmd.sync.desc": {
        "zh": "触发一次自己的 JiETNG 成绩同步",
        "ja": "自分の JiETNG 成績同期を開始します",
        "en": "Sync your JiETNG scores and wait for completion",
    },
    "cmd.b50.desc": {"zh": "生成 Best 50 成绩图", "ja": "Best 50 成績画像を生成します", "en": "Generate a Best 50 image"},
    "cmd.b40.desc": {"zh": "生成 Best 40 成绩图", "ja": "Best 40 成績画像を生成します", "en": "Generate a Best 40 image"},
    "cmd.b35.desc": {"zh": "生成旧版本 Best 35 成绩图", "ja": "旧バージョン Best 35 成績画像を生成します", "en": "Generate an old-version Best 35 image"},
    "cmd.b15.desc": {"zh": "生成新版本 Best 15 成绩图", "ja": "新バージョン Best 15 成績画像を生成します", "en": "Generate a new-version Best 15 image"},
    "cmd.ab35.desc": {"zh": "生成 All Best 35 成绩图", "ja": "All Best 35 成績画像を生成します", "en": "Generate an All Best 35 image"},
    "cmd.ab50.desc": {"zh": "生成 All Best 50 成绩图", "ja": "All Best 50 成績画像を生成します", "en": "Generate an All Best 50 image"},
    "cmd.ap50.desc": {"zh": "生成 AP Best 50 成绩图", "ja": "AP Best 50 成績画像を生成します", "en": "Generate an AP Best 50 image"},
    "cmd.fdx50.desc": {"zh": "生成 FDX Best 50 成绩图", "ja": "FDX Best 50 成績画像を生成します", "en": "Generate an FDX Best 50 image"},
    "cmd.r50.desc": {"zh": "生成最近游玩 50 成绩图", "ja": "最近プレイ 50 成績画像を生成します", "en": "Generate a recent 50 image"},
    "cmd.idlb50.desc": {"zh": "生成理想 B50 成绩图", "ja": "理想 B50 成績画像を生成します", "en": "Generate an ideal B50 image"},
    "cmd.unknown.desc": {"zh": "生成版本未知歌曲成绩图", "ja": "バージョン不明楽曲の成績画像を生成します", "en": "Generate an unknown-version records image"},
    "cmd.achievement.desc": {
        "zh": "生成等级列表 / 达成状况图",
        "ja": "レベル一覧 / 達成状況画像を生成します",
        "en": "Generate a level list or achievement progress image",
    },
    "cmd.plate.desc": {"zh": "生成牌子进度图", "ja": "称号プレート進捗画像を生成します", "en": "Generate a plate progress image"},
    "cmd.song.desc": {"zh": "按歌曲名或别名搜索歌曲", "ja": "楽曲名または別名で検索します", "en": "Search by song title or alias"},
    "cmd.record.desc": {"zh": "按歌曲名或别名生成自己的单曲成绩图", "ja": "楽曲名または別名から自分の単曲成績画像を生成します", "en": "Generate your song record image by title or alias"},
    "cmd.export.desc": {"zh": "导出加工后的成绩数据", "ja": "整形済み成績データをエクスポートします", "en": "Export processed score data"},
    "cmd.settings.desc": {"zh": "创建自己的 JiETNG 设置页面链接", "ja": "自分の JiETNG 設定ページを作成します", "en": "Create your JiETNG settings link"},
    "cmd.rebind.desc": {"zh": "创建自己的 JiETNG 重新绑定链接", "ja": "自分の JiETNG 再連携リンクを作成します", "en": "Create your JiETNG rebind link"},
    "param.user_id": {"zh": "JiETNG user_id", "ja": "JiETNG user_id", "en": "JiETNG user_id"},
    "param.command": {
        "zh": "可选过滤参数，例如 -lv 14 或 -ver buddies",
        "ja": "任意のフィルター。例: -lv 14 または -ver buddies",
        "en": "Optional filters, e.g. -lv 14 or -ver buddies",
    },
    "param.level": {"zh": "等级，例如 13+", "ja": "レベル。例: 13+", "en": "Level, e.g. 13+"},
    "param.rank": {
        "zh": "目标，例如 sss+, ap, fdx+；不填则为该等级列表",
        "ja": "目標。例: sss+, ap, fdx+。未指定ならレベル一覧",
        "en": "Target, e.g. sss+, ap, fdx+. Leave empty for a level list",
    },
    "param.filter_mode": {"zh": "可选筛选条件", "ja": "任意のフィルター条件", "en": "Optional filter"},
    "param.title": {"zh": "牌子名，例如 真神", "ja": "称号名。例: 真神", "en": "Plate title, e.g. 真神"},
    "param.query": {"zh": "歌曲名 / 别名", "ja": "楽曲名 / 別名", "en": "Song title / alias"},
    "param.ver": {"zh": "jp 或 intl", "ja": "jp または intl", "en": "jp or intl"},
    "param.format": {"zh": "json 或 xml", "ja": "json または xml", "en": "json or xml"},
}


def locale_key(locale: Any) -> str:
    value = str(locale or "").lower()
    if value.startswith("ja"):
        return "ja"
    if value.startswith(("zh", "zh-cn", "zh-tw")):
        return "zh"
    return "en"


def interaction_lang(interaction: discord.Interaction) -> str:
    return locale_key(getattr(interaction, "locale", None))


def tr(lang: str, key: str, **kwargs: Any) -> str:
    text = MESSAGES.get(key, {}).get(lang) or MESSAGES.get(key, {}).get("en") or key
    return text.format(**kwargs)


class BotTranslator(app_commands.Translator):
    async def translate(
        self,
        string: app_commands.locale_str,
        locale: discord.Locale,
        context: app_commands.TranslationContext,
    ) -> str | None:
        key = string.extras.get("key", string.message)
        lang = locale_key(locale)
        return COMMAND_TRANSLATIONS.get(key, {}).get(lang)
