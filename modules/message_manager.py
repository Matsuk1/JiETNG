from urllib.parse import quote
from modules.config_loader import SUPPORT_PAGE, LINE_ACCOUNT_ID
from modules.i18n import get_user_language, select_text
from modules.user_db import get_user
from modules.user_manager import get_notice_interaction, get_user_timezone
from modules.tip_ad_manager import get_random_tip, get_random_ad
from modules.message_texts import *
from linebot.v3.messaging import (
    TextMessage,
    QuickReply,
    QuickReplyItem,
    MessageAction,
    URIAction,
    FlexMessage,
    FlexContainer,
    ImageMessage
)

from linebot.v3.messaging.models import (
    FlexBubble,
    FlexBox,
    FlexText,
    FlexButton,
    FlexSeparator
)

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

get_multilingual_text = select_text

COLOR_TEXT_PRIMARY = "#111111"
COLOR_TEXT_SECONDARY = "#666666"
COLOR_TEXT_MUTED = "#999999"
COLOR_TEXT_INVERSE = "#FFFFFF"
COLOR_SUCCESS = "#17B169"
COLOR_DANGER = "#FF3B30"
COLOR_WARNING = "#FF9500"
COLOR_BRAND = "#FF6B35"
COLOR_TIP = "#5856D6"
COLOR_TIP_BG = "#F0EFFF"
COLOR_AD_BG = "#FFF4E6"

HELP_UI_TEXT = {
    "help_title": {"zh": "命令帮助", "en": "Command Help", "ja": "コマンドヘルプ"},
    "usage": {"zh": "用法", "en": "Usage", "ja": "使い方"},
    "function": {"zh": "功能", "en": "Function", "ja": "機能"},
    "params": {"zh": "参数", "en": "Parameters", "ja": "引数"},
    "examples": {"zh": "示例", "en": "Examples", "ja": "例"},
    "notes": {"zh": "注意", "en": "Notes", "ja": "注意"},
    "command": {"zh": "命令", "en": "Command", "ja": "コマンド"},
    "purpose": {"zh": "用途", "en": "Purpose", "ja": "用途"},
    "none": {"zh": "无", "en": "None", "ja": "なし"},
    "default_purpose": {
        "zh": "查看该命令的说明。",
        "en": "Show help for this command.",
        "ja": "このコマンドの説明を表示します。",
    },
    "b_title": {"zh": "B 系列成绩图", "en": "B-Series Score Images", "ja": "B 系スコア画像"},
    "b_subtitle": {
        "zh": "Best / All Best / 特殊成绩图与筛选参数",
        "en": "Best / All Best / special score images and filters",
        "ja": "Best / All Best / 特殊成績画像とフィルター",
    },
    "modes": {"zh": "可用模式", "en": "Modes", "ja": "モード"},
    "catalog_title": {"zh": "命令目录", "en": "Command Directory", "ja": "コマンド一覧"},
    "catalog_subtitle": {
        "zh": "发送 命令-help 查看单项说明",
        "en": "Send command-help for detailed usage",
        "ja": "command-help で詳細を表示",
    },
    "categories": {"zh": "分类", "en": "Categories", "ja": "カテゴリ"},
    "detail_hint": {"zh": "详细说明", "en": "Detailed Help", "ja": "詳細ヘルプ"},
}


def _help_ui(key, user_id=None):
    return get_multilingual_text(HELP_UI_TEXT[key], user_id)


def _help_i18n(user_id, zh, en, ja):
    return get_multilingual_text({"zh": zh, "en": en, "ja": ja}, user_id)


def _help_flex_text(text, size="sm", color="#222222", weight=None, wrap=True, margin=None, align=None):
    node = {
        "type": "text",
        "text": text,
        "size": size,
        "color": color,
        "wrap": wrap,
    }
    if weight:
        node["weight"] = weight
    if margin:
        node["margin"] = margin
    if align:
        node["align"] = align
    return node


def _help_pill(text, color="#315B7D", bg_color="#EAF4FF"):
    return {
        "type": "box",
        "layout": "vertical",
        "backgroundColor": bg_color,
        "cornerRadius": "12px",
        "paddingTop": "3px",
        "paddingBottom": "3px",
        "paddingStart": "8px",
        "paddingEnd": "8px",
        "contents": [
            _help_flex_text(text, size="xxs", color=color, weight="bold", align="center", wrap=False)
        ],
    }


def _help_section_title(title, accent="#FF7A45"):
    return {
        "type": "box",
        "layout": "horizontal",
        "spacing": "sm",
        "alignItems": "center",
        "margin": "lg",
        "contents": [
            {
                "type": "box",
                "layout": "vertical",
                "width": "4px",
                "height": "18px",
                "cornerRadius": "2px",
                "backgroundColor": accent,
                "contents": [{"type": "filler"}],
            },
            _help_flex_text(title, size="sm", color="#111111", weight="bold"),
        ],
    }


def _help_mode_card(title, body, accent):
    return {
        "type": "box",
        "layout": "vertical",
        "spacing": "xs",
        "paddingAll": "10px",
        "cornerRadius": "8px",
        "borderWidth": "1px",
        "borderColor": "#E6E8EC",
        "contents": [
            _help_flex_text(title, size="xs", color=accent, weight="bold"),
            _help_flex_text(body, size="xxs", color="#555555"),
        ],
    }


def _help_filter_row(label, desc, example=None):
    contents = [
        {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                _help_pill(label, color="#C93D47", bg_color="#FFF0F1"),
            ],
        },
        _help_flex_text(desc, size="xxs", color="#555555", margin="xs"),
    ]
    if example:
        contents.append({
            "type": "box",
            "layout": "vertical",
            "margin": "xs",
            "paddingAll": "7px",
            "cornerRadius": "6px",
            "backgroundColor": "#F7F8FA",
            "contents": [
                _help_flex_text(example, size="xxs", color="#222222"),
            ],
        })
    return {
        "type": "box",
        "layout": "vertical",
        "paddingBottom": "8px",
        "contents": contents,
    }


def _help_note_row(label, desc):
    return {
        "type": "box",
        "layout": "vertical",
        "spacing": "xs",
        "paddingAll": "9px",
        "cornerRadius": "8px",
        "backgroundColor": "#F8FAFC",
        "contents": [
            _help_flex_text(label, size="xs", color="#315B7D", weight="bold"),
            _help_flex_text(desc, size="xxs", color="#555555"),
        ],
    }


def _standard_help_bubble(title, subtitle, sections, alt_text):
    body_contents = [
        {
            "type": "box",
            "layout": "vertical",
            "spacing": "xs",
            "paddingAll": "14px",
            "cornerRadius": "8px",
            "backgroundColor": "#111827",
            "contents": [
                _help_flex_text(title, size="lg", color="#FFFFFF", weight="bold"),
                _help_flex_text(subtitle, size="xs", color="#D1D5DB", margin="xs"),
            ],
        },
    ]
    for title, rows in sections:
        body_contents.append(_help_section_title(title))
        body_contents.append({
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": rows,
        })
    bubble = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "paddingAll": "16px",
            "contents": body_contents,
        },
    }
    return FlexMessage(
        alt_text=alt_text,
        contents=FlexContainer.from_dict(bubble),
    )


def _flex_action_button(label, action, style="primary", color=COLOR_BRAND):
    button = {
        "type": "button",
        "height": "sm",
        "style": style,
        "action": action,
    }
    if style == "primary":
        button["color"] = color
    return button


def _standard_action_bubble(title, subtitle, body_text, alt_text, actions=None, note_text=None,
                            accent=COLOR_BRAND, user_id=None):
    sections = [
        (_help_ui("function", user_id), [
            _help_note_row(_help_ui("purpose", user_id), body_text)
        ])
    ]
    if note_text:
        sections.append((_help_ui("notes", user_id), [
            _help_note_row(_help_ui("notes", user_id), note_text)
        ]))

    body_contents = [
        {
            "type": "box",
            "layout": "vertical",
            "spacing": "xs",
            "paddingAll": "14px",
            "cornerRadius": "8px",
            "backgroundColor": "#111827",
            "contents": [
                _help_flex_text(title, size="lg", color="#FFFFFF", weight="bold"),
                _help_flex_text(subtitle, size="xs", color="#D1D5DB", margin="xs"),
            ],
        },
    ]
    for section_title, rows in sections:
        body_contents.append(_help_section_title(section_title, accent=accent))
        body_contents.append({
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": rows,
        })

    bubble = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "paddingAll": "16px",
            "contents": body_contents,
        },
    }
    if actions:
        bubble["footer"] = {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "paddingAll": "12px",
            "contents": actions,
        }
    return FlexMessage(alt_text=alt_text, contents=FlexContainer.from_dict(bubble))


def generate_status_flex(title_text, body_text, user_id=None, alt_text=None, tone="info"):
    accent_by_tone = {
        "info": "#315B7D",
        "warning": COLOR_WARNING,
        "danger": COLOR_DANGER,
        "success": COLOR_SUCCESS,
    }
    title = get_multilingual_text(title_text, user_id)
    body = get_multilingual_text(body_text, user_id)
    alt = get_multilingual_text(alt_text, user_id) if alt_text is not None else title
    return _standard_action_bubble(
        title=title,
        subtitle="JiETNG",
        body_text=body,
        alt_text=alt,
        accent=accent_by_tone.get(tone, "#315B7D"),
        user_id=user_id,
    )


def generate_account_action_flex(action_type, url, user_id=None):
    configs = {
        "bind": {
            "title": sega_bind_title_text,
            "body": sega_bind_description_text,
            "button": sega_bind_button_text,
            "alt": sega_bind_alt_text,
            "accent": COLOR_BRAND,
        },
        "rebind": {
            "title": rebind_title_alt_text,
            "body": rebind_description_text,
            "button": rebind_button_text,
            "alt": rebind_title_alt_text,
            "accent": "#8A63D2",
        },
        "settings": {
            "title": settings_title_alt_text,
            "body": settings_description_text,
            "button": settings_button_text,
            "alt": settings_title_alt_text,
            "accent": "#315B7D",
        },
    }
    config = configs[action_type]
    title = get_multilingual_text(config["title"], user_id)
    body = get_multilingual_text(config["body"], user_id)
    button = get_multilingual_text(config["button"], user_id)
    alt = get_multilingual_text(config["alt"], user_id)
    return _standard_action_bubble(
        title=title,
        subtitle="JiETNG",
        body_text=body,
        alt_text=alt,
        actions=[
            _flex_action_button(button, {"type": "uri", "label": button, "uri": url}, color=config["accent"])
        ],
        accent=config["accent"],
        user_id=user_id,
    )


def generate_welcome_flex(user_id=None, bind_url=None, group=False):
    title = "JiETNG"
    body = group_welcome_msg_text if group else welcome_msg_text
    actions = None
    if bind_url:
        label = get_multilingual_text(sega_bind_button_text, user_id)
        actions = [
            _flex_action_button(label, {"type": "uri", "label": label, "uri": bind_url}, color=COLOR_BRAND)
        ]
    return _standard_action_bubble(
        title=title,
        subtitle="Maimai DX LINE Bot",
        body_text=body,
        alt_text=title,
        actions=actions,
        accent=COLOR_BRAND,
        user_id=user_id,
    )


def generate_export_flex(user_id, meta):
    size_kb = max(1, round(meta["size"] / 1024))
    fmt_label = meta["fmt"].upper()
    title = get_multilingual_text(export_flex_title_text, user_id)
    body = get_multilingual_text(export_flex_summary_text, user_id).format(
        best=meta["best_count"],
        recent=meta["recent_count"],
        fmt=fmt_label,
        size_kb=size_kb,
    )
    foot = get_multilingual_text(export_flex_footnote_text, user_id).format(ttl=meta["ttl_minutes"])
    btn = get_multilingual_text(export_flex_button_text, user_id)
    copy_btn = get_multilingual_text(export_flex_copy_button_text, user_id)
    alt = get_multilingual_text(export_alt_text, user_id)
    return _standard_action_bubble(
        title=title,
        subtitle=fmt_label,
        body_text=body,
        note_text=foot,
        alt_text=alt,
        actions=[
            _flex_action_button(btn, {"type": "uri", "label": btn, "uri": f"{meta['url']}?openExternalBrowser=1"}),
            _flex_action_button(
                copy_btn,
                {"type": "clipboard", "label": copy_btn, "clipboardText": meta["url"]},
                style="secondary",
            ),
        ],
        accent=COLOR_SUCCESS,
        user_id=user_id,
    )


def generate_donate_flex(user_id=None):
    title = "カヰテーを支援 · Support JiETNG"
    body = (
        "一起为 JiETNG 的开发与未来加油！\n"
        "JiETNG の開発と未来を応援しよう！\n"
        "Support JiETNG's journey ahead!"
    )
    return _standard_action_bubble(
        title=title,
        subtitle="JiETNG",
        body_text=body,
        note_text="Thank you for supporting JiETNG",
        alt_text="JiETNGを支援 · Support JiETNG",
        actions=[
            _flex_action_button("Liberapay", {
                "type": "uri",
                "label": "Liberapay",
                "uri": "https://ja.liberapay.com/_matsuk1/donate?currency=JPY",
            }),
            _flex_action_button("爱发电", {
                "type": "uri",
                "label": "爱发电",
                "uri": "https://afdian.com/a/matsuki",
            }, style="secondary"),
        ],
        accent=COLOR_TIP,
        user_id=user_id,
    )

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


def _clean_help_text(text):
    return str(text or "").replace("`", "").strip()


def _parse_plain_help(text):
    fields = {"命令": "", "用途": "", "参数": "", "示例": "", "注意": ""}
    current_key = None
    for raw_line in _clean_help_text(text).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        matched = False
        for key in fields:
            prefix = f"{key}:"
            if line.startswith(prefix):
                fields[key] = line[len(prefix):].strip() or fields[key]
                current_key = key
                matched = True
                break
        if not matched and current_key:
            fields[current_key] = f"{fields[current_key]}\n{line}".strip()
    return fields


def generate_standard_help_flex(help_data, user_id=None):
    fields = get_multilingual_text(help_data, user_id) if isinstance(help_data, dict) else help_data
    if not isinstance(fields, dict):
        fields = _parse_plain_help(fields)
    command = fields.get("command") or fields.get("命令") or _help_ui("help_title", user_id)
    purpose = fields.get("purpose") or fields.get("用途")
    params = fields.get("params") or fields.get("参数")
    examples = fields.get("examples") or fields.get("示例")
    notes = fields.get("notes") or fields.get("注意")
    none_text = _help_ui("none", user_id)
    sections = [
        (_help_ui("usage", user_id), [_help_filter_row(_help_ui("command", user_id), command)]),
        (_help_ui("function", user_id), [
            _help_note_row(_help_ui("purpose", user_id), purpose or _help_ui("default_purpose", user_id))
        ]),
        (_help_ui("params", user_id), [_help_filter_row(_help_ui("params", user_id), params or none_text)]),
        (_help_ui("examples", user_id), [_help_filter_row(_help_ui("examples", user_id), examples or none_text)]),
    ]
    if notes:
        sections.append((_help_ui("notes", user_id), [_help_note_row(_help_ui("notes", user_id), notes)]))
    return _standard_help_bubble(
        title=_help_ui("help_title", user_id),
        subtitle=command,
        sections=sections,
        alt_text=f"{command} {_help_ui('help_title', user_id)}",
    )


def generate_b_records_help_flex(user_id=None):
    modes = [
        ("Best", _help_i18n(
            user_id,
            "b50 / best50, b40 / best40, b35 / best35, b15 / best15",
            "b50 / best50, b40 / best40, b35 / best35, b15 / best15",
            "b50 / best50, b40 / best40, b35 / best35, b15 / best15",
        ), "#E85D75"),
        ("All Best", _help_i18n(
            user_id,
            "ab50 / allb50, ab35 / allb35",
            "ab50 / allb50, ab35 / allb35",
            "ab50 / allb50, ab35 / allb35",
        ), "#8A63D2"),
        ("Special", _help_i18n(
            user_id,
            "ap50, fdx50, r50 / rct50, idlb50, s50 / sun50",
            "ap50, fdx50, r50 / rct50, idlb50, s50 / sun50",
            "ap50, fdx50, r50 / rct50, idlb50, s50 / sun50",
        ), "#267D8B"),
    ]
    filters = [
        ("-lv / -level", _help_i18n(user_id, "等级或定数。1 个值精确匹配，2 个值范围。", "Level or constant. One value is exact; two values are a range.", "レベルまたは定数。1 つは完全一致、2 つは範囲です。"), "-lv 13.6   /   -lv 14 14.9"),
        ("-diff / -difficulty", _help_i18n(user_id, "难度。支持 bas、adv、exp、mas、rem 或完整名，可多个。", "Difficulty. Supports bas, adv, exp, mas, rem, or full names; multiple values are allowed.", "難易度。bas、adv、exp、mas、rem または正式名を複数指定できます。"), "-diff mas rem"),
        ("-ra / -rating", _help_i18n(user_id, "单谱 Rating。1 个值精确匹配，2 个值范围。", "Chart rating. One value is exact; two values are a range.", "単曲 Rating。1 つは完全一致、2 つは範囲です。"), "-ra 320 360"),
        ("-scr / -score", _help_i18n(user_id, "达成率。1 个值为下限，2 个值为范围。", "Achievement. One value is a lower bound; two values are a range.", "達成率。1 つは下限、2 つは範囲です。"), "-scr 100.5   /   -scr 100 100.5"),
        ("-dx / -dxscore", _help_i18n(user_id, "无参数时按 DX 分排序；带值时筛 DX Score 百分比。", "Without values, sort by DX score; with values, filter DX score percentage.", "値なしでは DX スコア順、値ありでは DX スコア割合で絞り込みます。"), "-dx   /   -dx 95 100"),
        ("-star / -dxstar", _help_i18n(user_id, "DX 星数。1 个值精确匹配，2 个值范围。", "DX stars. One value is exact; two values are a range.", "DX 星数。1 つは完全一致、2 つは範囲です。"), "-star 5"),
        ("-ver / -version", _help_i18n(user_id, "版本名，可多个。+ 会识别为 PLUS，dx / deluxe 会归一。", "Version names. Multiple values are allowed; + is treated as PLUS, and dx/deluxe are normalized.", "バージョン名。複数指定可。+ は PLUS、dx / deluxe は正規化されます。"), "-ver buddies prism+"),
        ("-type / -tp", _help_i18n(user_id, "谱面类型。支持 dx、std，可多个。", "Chart type. Supports dx and std; multiple values are allowed.", "譜面種別。dx、std を複数指定できます。"), "-type dx"),
        ("-next / -nxt", _help_i18n(user_id, "下版本预览。按下一版本 Rating 结构预览成绩图。", "Next-version preview using the next rating structure.", "次バージョンプレビュー。次の Rating 構成で成績画像を表示します。"), "-nxt"),
        ("-page / -pg", _help_i18n(user_id, "页码，从 1 开始。", "Page number, starting from 1.", "ページ番号。1 から始まります。"), "-page 2"),
        ("-times / -tm", _help_i18n(user_id, "扩大输出数量倍率，最大 2.5。", "Display multiplier, capped at 2.5.", "表示件数の倍率。最大 2.5 です。"), "-times 2"),
    ]
    sections = [
        (_help_ui("usage", user_id), [
            _help_filter_row(_help_ui("command", user_id), "b50 / b40 / b35 / b15 / ab50 / ap50 / fdx50 / r50 / idlb50 / s50"),
        ]),
        (_help_ui("function", user_id), [
            _help_note_row(_help_ui("purpose", user_id), _help_i18n(
                user_id,
                "生成 Best / All Best / 特殊成绩图，可追加筛选参数。",
                "Generate Best / All Best / special score images with optional filters.",
                "Best / All Best / 特殊成績画像を生成し、フィルターを追加できます。",
            )),
        ]),
        (_help_ui("modes", user_id), [
            _help_mode_card(title, body, color)
            for title, body, color in modes
        ]),
        (_help_ui("params", user_id), [
            _help_filter_row(label, desc, example)
            for label, desc, example in filters
        ]),
        (_help_ui("examples", user_id), [
            {
                "type": "box",
                "layout": "vertical",
                "spacing": "xs",
                "paddingAll": "10px",
                "cornerRadius": "8px",
                "backgroundColor": "#F7F8FA",
                "contents": [
                    _help_flex_text("b50 -lv 14 14.9 -diff mas rem -scr 100.5", size="xxs", color="#111111"),
                    _help_flex_text("ab50 -ver buddies -type dx", size="xxs", color="#111111"),
                    _help_flex_text("r50 -page 2", size="xxs", color="#111111"),
                ],
            },
        ]),
        (_help_ui("notes", user_id), [
            _help_note_row(_help_i18n(user_id, "数据要求", "Data required", "データ要件"), _help_i18n(
                user_id,
                "需要已绑定账号并完成 maimai update，或已有 Import Token / 开发者 API 导入的数据。",
                "Requires a linked account with maimai update completed, or data imported through Import Token / Developer API.",
                "maimai update 済みの連携アカウント、または Import Token / Developer API で取り込んだデータが必要です。",
            )),
            _help_note_row(_help_i18n(user_id, "查询他人", "Querying others", "他ユーザー検索"), _help_i18n(
                user_id,
                "支持 LINE mention 查询已注册用户；仅限本人命令不会接受 mention。",
                "LINE mentions can query registered users; self-only commands do not accept mentions.",
                "LINE メンションで登録済みユーザーを検索できます。本人専用コマンドはメンション不可です。",
            )),
        ]),
    ]
    return _standard_help_bubble(
        title=_help_ui("b_title", user_id),
        subtitle=_help_ui("b_subtitle", user_id),
        sections=sections,
        alt_text=f"{_help_ui('b_title', user_id)} {_help_ui('help_title', user_id)}",
    )


def generate_help_index_flex(user_id=None):
    groups = [
        (
            _help_i18n(user_id, "账号与系统", "Account and System", "アカウントとシステム"),
            "bind / rebind / settings / profile / update / export / status",
            _help_i18n(user_id, "绑定、设置、资料、同步、导出与状态。", "Binding, settings, profile, sync, export, and status.", "連携、設定、プロフィール、同期、エクスポート、状態確認。"),
            "#E85D75",
        ),
        (
            _help_i18n(user_id, "成绩图", "Score Images", "成績画像"),
            "b50 / b40 / ab50 / ap50 / fdx50 / r50 / idlb50 / s50",
            _help_i18n(user_id, "Best、All Best、Recent 与特殊成绩图。", "Best, All Best, Recent, and special score images.", "Best、All Best、Recent、特殊成績画像。"),
            "#8A63D2",
        ),
        (
            _help_i18n(user_id, "歌曲与成绩", "Songs and Records", "楽曲と成績"),
            "info / record / search / search-record / calc-song",
            _help_i18n(user_id, "查歌曲信息、单曲成绩和歌曲 ID。", "Song details, single-song records, and song IDs.", "楽曲情報、単曲成績、楽曲 ID 検索。"),
            "#267D8B",
        ),
        (
            _help_i18n(user_id, "搜索", "Search", "検索"),
            "artist / designer / bpm / random",
            _help_i18n(user_id, "按艺术家、谱师、BPM 或条件随机选曲。", "Search by artist, designer, BPM, or random conditions.", "アーティスト、譜面制作者、BPM、ランダム条件で検索。"),
            "#2F7D51",
        ),
        (
            _help_i18n(user_id, "列表与进度", "Lists and Progress", "リストと進捗"),
            "records / record-list / level-list / achievement / progress",
            _help_i18n(user_id, "等级列表、定数列表、牌子完成度和目标进度。", "Level lists, constant lists, plate completion, and target progress.", "レベルリスト、定数リスト、プレート達成状況、目標進捗。"),
            "#B86E19",
        ),
        (
            _help_i18n(user_id, "社交与权限", "Social and Permissions", "フレンドと権限"),
            "friends / friend-rcd / accept-perm-request / reject-perm-request",
            _help_i18n(user_id, "好友成绩和第三方访问权限管理。", "Friend records and third-party access permission management.", "フレンド成績と外部アクセス権限管理。"),
            "#315B7D",
        ),
        (
            _help_i18n(user_id, "工具", "Tools", "ツール"),
            "rank / rc / calc / donate / refreshmenu",
            _help_i18n(user_id, "排行榜、Rating 内訳、分值计算和辅助功能。", "Ranking, rating breakdown, note scoring, and utility commands.", "ランキング、レート内訳、ノーツ点数計算、補助機能。"),
            "#6B7280",
        ),
    ]
    sections = [
        (_help_ui("categories", user_id), [
            _help_mode_card(title, commands, color)
            for title, commands, _desc, color in groups
        ]),
        (_help_ui("function", user_id), [
            _help_note_row(title, desc)
            for title, _commands, desc, _color in groups
        ]),
        (_help_ui("detail_hint", user_id), [
            _help_filter_row(_help_i18n(user_id, "单项说明", "Single command", "単体説明"), _help_i18n(
                user_id,
                "发送 b50-help、artist-help、bpm-help 这类格式查看完整用法。",
                "Send b50-help, artist-help, bpm-help, and similar forms for full usage.",
                "b50-help、artist-help、bpm-help のように送信すると詳しい使い方を表示します。",
            )),
            _help_filter_row(_help_i18n(user_id, "参数缺失", "Missing arguments", "引数不足"), _help_i18n(
                user_id,
                "需要参数的命令只发送命令名时，也会显示对应说明。",
                "Commands that need arguments also show help when sent without arguments.",
                "引数が必要なコマンドを引数なしで送ると説明を表示します。",
            )),
        ]),
    ]
    return _standard_help_bubble(
        title=_help_ui("catalog_title", user_id),
        subtitle=_help_ui("catalog_subtitle", user_id),
        sections=sections,
        alt_text=f"{_help_ui('catalog_title', user_id)}",
    )


def _update_status_label(func_name, lang):
    status_text_keys = {
        "User Info": "status_user_info",
        "Best Records": "status_best_records",
        "Recent Records": "status_recent_records",
    }
    text_key = status_text_keys.get(func_name)
    if not text_key:
        return func_name
    return get_multilingual_text(update_result_flex_text[text_key], language=lang)

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

def rebind_msg(user_id=None):
    """生成 SEGA ID 更新成功消息"""
    return create_text_message(rebind_msg_text, user_id, get_update_quick_reply(user_id))

def unbind_msg(user_id=None):
    """生成 SEGA ID 解绑成功消息"""
    return create_text_message(unbind_msg_text, user_id)

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

def mention_record_error(user_id=None):
    """生成被提到用户无成绩数据错误消息（与 record_error 区分，避免主语错位）"""
    return create_text_message(mention_record_error_text, user_id)

def cannot_do_for_others(user_id=None):
    """@ 别人但用了仅限本人的命令（如 update / bind / unbind / export）时的拒绝消息"""
    return create_text_message(cannot_do_for_others_text, user_id)

def no_matching_data(user_id=None):
    """有成绩，但本次查询的过滤/条件无匹配时返回（与 record_error 区分语义）"""
    return create_text_message(no_matching_data_text, user_id)

def mention_no_matching_data(user_id=None):
    """被 @ 的用户有成绩但本次查询无匹配时返回"""
    return create_text_message(mention_no_matching_data_text, user_id)

def get_perm_request_notification_alt_text(count, user_id=None):
    """获取权限请求通知的 alt text"""
    return get_multilingual_text(perm_request_notification_alt_text, user_id).format(count=count)

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
    lang = get_user_language(user_id)

    # 标题（多语言）
    title = get_notice_header(user_id)

    # 内容（根据用户语言）
    content_dict = notice_json.get('content', {})
    if isinstance(content_dict, str):
        # 向后兼容旧格式
        content = content_dict
    else:
        content = select_text(content_dict, language=lang, default_language='ja')

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
        button_label = select_text(button_label_dict, language=lang, default_language='ja')
        button_value = button_info.get('value', '')

        # 如果label为空，使用默认值
        if not button_label:
            default_labels = {
                'uri': {'ja': '詳細を見る', 'en': 'View Details', 'zh': '查看详情'},
                'message': {'ja': '試してみる', 'en': 'Try it', 'zh': '尝试一下'}
            }
            button_label = select_text(default_labels.get(button_type, {}), language=lang, default_language='ja') or 'Go'

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
                "type": "message",
                "label": button_label_with_arrow,
                "text": button_value
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

        # 投票按钮文本
        vote_labels = {
            'support': {'ja': '支持', 'en': 'Support', 'zh': '支持'},
            'oppose': {'ja': '反対', 'en': 'Oppose', 'zh': '反对'}
        }

        support_label = select_text(vote_labels['support'], language=lang, default_language='ja')
        oppose_label = select_text(vote_labels['oppose'], language=lang, default_language='ja')

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


def generate_song_info_flex(song_id, image_url, image_width, image_height, user_id=None, mode='info'):
    """
    生成歌曲信息 Flex Message（图片 + 按钮合为一个 bubble）

    Args:
        song_id: 歌曲ID
        image_url: 歌曲信息图片 URL
        image_width: 图片宽度（px）
        image_height: 图片高度（px）
        user_id: 用户ID（用于多语言）
        mode: 'info'（歌曲信息模式，显示 calc + record 按钮）
              'record'（成绩模式，显示 info 按钮）

    Returns:
        FlexMessage
    """
    from math import gcd
    g = gcd(image_width, image_height)
    aspect_ratio = f"{image_width // g}:{image_height // g}"

    buttons = []

    if mode == 'info':
        buttons.append({
            "type": "button",
            "style": "secondary",
            "height": "sm",
            "action": {
                "type": "postback",
                "label": get_multilingual_text(calc_button_text, user_id),
                "data": f"calc-song {song_id}"
            }
        })
        buttons.append({
            "type": "button",
            "style": "secondary",
            "height": "sm",
            "margin": "sm",
            "action": {
                "type": "postback",
                "label": get_multilingual_text(view_record_button_text, user_id),
                "data": f"search-record {song_id}",
                "displayText": f"search-record {song_id}"
            }
        })
    else:
        buttons.append({
            "type": "button",
            "style": "secondary",
            "height": "sm",
            "action": {
                "type": "postback",
                "label": get_multilingual_text(view_info_button_text, user_id),
                "data": f"search {song_id}",
                "displayText": f"search {song_id}"
            }
        })

    alt_text = get_multilingual_text(song_info_alt_text, user_id) if mode == 'info' else get_multilingual_text(song_record_alt_text, user_id)

    bubble = {
        "type": "bubble",
        "size": "mega",
        "hero": {
            "type": "image",
            "url": image_url,
            "action": {
                "type": "uri",
                "uri": image_url
            },
            "size": "full",
            "aspectRatio": aspect_ratio,
            "aspectMode": "fit"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": buttons,
            "paddingAll": "12px"
        }
    }

    return FlexMessage(
        alt_text=alt_text,
        contents=FlexContainer.from_dict(bubble)
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

    user_data = get_user(user_id)
    if user_data:

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
                            "color": COLOR_TEXT_MUTED
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
                        "type": "clipboard",
                        "label": "📋",
                        "clipboardText": user_id
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
                    "color": COLOR_TEXT_MUTED
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
                            "color": COLOR_TEXT_MUTED
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
                        "color": COLOR_TEXT_MUTED
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
                        "color": COLOR_TEXT_SECONDARY,
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
                        "color": COLOR_TEXT_MUTED
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
            'zh': texts['lang_zh'],
            'zh-tw': {'zh-tw': '繁體中文'}
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
                    "color": COLOR_TEXT_MUTED
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
                    "color": COLOR_TEXT_MUTED
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
                    "color": COLOR_DANGER
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
                    "color": COLOR_TEXT_INVERSE
                }
            ],
            "paddingAll": "16px",
            "backgroundColor": COLOR_BRAND
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


def generate_update_result_flex(
    user_id,
    username,
    rating,
    update_time,
    elapsed_time,
    func_status,
    success=True,
):
    """
    生成更新结果 Flex Message

    Args:
        user_id: 用户ID
        username: 用户名
        rating: Rating 值
        update_time: 更新时间
        elapsed_time: 耗时（秒）
        func_status: 各功能状态字典
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
                "color": COLOR_TEXT_MUTED
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
                "color": COLOR_TEXT_MUTED
            },
            {
                "type": "text",
                "text": elapsed_str,
                "size": "sm",
                "weight": "bold",
                "margin": "xs",
                "color": COLOR_SUCCESS if success else COLOR_DANGER
            }
        ]
    })

    failed_statuses = {
        func_name: status
        for func_name, status in func_status.items()
        if not status
    }
    if failed_statuses:
        content_rows.append({
            "type": "separator",
            "margin": "md"
        })

        status_contents = [
            {
                "type": "text",
                "text": get_multilingual_text(texts['status_label'], language=lang),
                "size": "xs",
                "color": COLOR_TEXT_MUTED
            }
        ]

        for func_name, status in failed_statuses.items():
            status_text = get_multilingual_text(texts['failed'], language=lang)
            func_label = _update_status_label(func_name, lang)
            status_contents.append({
                "type": "text",
                "text": f"・{func_label}: {status_text}",
                "size": "xs",
                "color": COLOR_DANGER,
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
    header_color = COLOR_SUCCESS if success else COLOR_DANGER

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
                    "color": COLOR_TEXT_INVERSE
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
    text = select_text(text_dict, language=lang, default_language='ja')

    # 确定颜色和图标
    is_ad = tip_ad.get('type') == 'ad'
    bg_color = COLOR_AD_BG if is_ad else COLOR_TIP_BG
    text_color = COLOR_WARNING if is_ad else COLOR_TIP
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
        button_label = select_text(button_label_dict, language=lang, default_language='ja')
        button_value = button_info.get('value', '')

        # 如果label为空，使用默认值
        if not button_label:
            default_labels = {
                'uri': {'ja': '詳細を見る', 'en': 'View Details', 'zh': '查看详情'},
                'message': {'ja': '試してみる', 'en': 'Try it', 'zh': '尝试一下'}
            }
            button_label = select_text(default_labels.get(button_type, {}), language=lang, default_language='ja') or 'Go'

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
                "type": "message",
                "label": button_label_with_arrow,
                "text": button_value
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


def generate_search_results_flex(user_id, matching_songs, search_type='song', id_use=None):
    """
    生成搜索结果列表 Flex Message

    Args:
        user_id: 用户ID
        matching_songs: 匹配的歌曲列表
        search_type: 搜索类型 ('song' 或 'record')
        id_use: 使用的ID

    Returns:
        FlexMessage: 搜索结果列表
    """
    language = get_user_language(user_id)

    id_use_text = ""
    if id_use:
        id_use_text = f"&id_use={id_use}"

    type_map = {
        'dx': 'DX',
        'std': 'STD',
        'utage': 'UTAGE'
    }

    search_config = {
        'song': {
            'command': 'search',
            'title': {
                'ja': f'楽曲検索結果 ({len(matching_songs)}件)',
                'en': f'Song Search Results ({len(matching_songs)})',
                'zh': f'歌曲搜索结果 ({len(matching_songs)}条)'
            }
        },
        'record': {
            'command': 'search-record',
            'title': {
                'ja': f'レコード検索結果 ({len(matching_songs)}件)',
                'en': f'Record Search Results ({len(matching_songs)})',
                'zh': f'成绩搜索结果 ({len(matching_songs)}条)'
            }
        }
    }

    config = search_config[search_type]
    display_songs = matching_songs[:20]

    song_rows = []
    for idx, song in enumerate(display_songs):
        song_id = song.get('id', '')
        song_title = song.get('title', 'Unknown')
        song_type = type_map.get(song.get('type', ''), song.get('type', '').upper())
        artist = song.get('artist') or '-'

        row = {
            "type": "box",
            "layout": "horizontal",
            "spacing": "md",
            "margin": "md" if idx > 0 else "none",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "flex": 3,
                    "contents": [
                        {
                            "type": "text",
                            "text": song_title,
                            "size": "sm",
                            "weight": "bold",
                            "color": "#000000",
                            "wrap": True,
                            "maxLines": 2
                        },
                        {
                            "type": "text",
                            "text": artist,
                            "size": "xs",
                            "color": "#666666",
                            "margin": "xs",
                            "wrap": True,
                            "maxLines": 1
                        },
                        {
                            "type": "text",
                            "text": song_type,
                            "size": "xs",
                            "color": "#999999",
                            "margin": "xs"
                        }
                    ]
                },
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "→",
                        "data": f"{config['command']} {song_id}{id_use_text}",
                        "displayText": f"{config['command']} {song_id}"
                    },
                    "style": "secondary",
                    "height": "sm",
                    "flex": 0
                }
            ]
        }

        song_rows.append(row)
        if idx < len(display_songs) - 1:
            song_rows.append({"type": "separator", "margin": "sm"})

    title_text = select_text(config['title'], language=language, default_language='ja')

    header_box = {
        "type": "box",
        "layout": "vertical",
        "paddingAll": "16px",
        "contents": [
            {
                "type": "text",
                "text": title_text,
                "weight": "bold",
                "size": "lg",
                "color": "#000000"
            },
            {
                "type": "separator",
                "color": "#DDDDDD",
                "margin": "md"
            }
        ]
    }

    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": header_box,
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": song_rows,
            "paddingAll": "16px",
            "backgroundColor": "#FFFFFF"
        },
        "styles": {"body": {"backgroundColor": "#FFFFFF"}}
    }

    return FlexMessage(
        alt_text=title_text,
        contents=FlexContainer.from_dict(bubble)
    )


def generate_ranking_flex(user_id, top5, nearby_entries=None, ver="jp"):
    """
    生成 Rating 排行榜 Flex Message（5+7 布局）

    Args:
        user_id: 当前用户ID
        top5: 前5名列表 [{"rank": 1, "name": "xxx", "rating": "15000"}, ...]
        nearby_entries: 以用户为中心的附近名单（用户不在前5时提供），None 表示用户在前5或版本不一致
        ver: 版本 "jp" 或 "intl"

    Returns:
        FlexMessage
    """
    title_text = get_multilingual_text(ranking_title_text, user_id)
    ver_label = "JP" if ver == "jp" else "INTL"

    # Header
    header = {
        "type": "box",
        "layout": "horizontal",
        "contents": [
            {
                "type": "text",
                "text": title_text,
                "weight": "bold",
                "size": "lg",
                "color": "#000000",
                "flex": 1
            },
            {
                "type": "text",
                "text": ver_label,
                "size": "sm",
                "color": "#999999",
                "align": "end",
                "gravity": "center",
                "flex": 0
            }
        ],
        "paddingAll": "16px"
    }

    body_contents = [
        {"type": "separator", "color": "#000000"}
    ]

    def make_row(entry, highlight=False):
        rank = entry["rank"]
        name = entry["name"]
        rating = entry["rating"]

        row_contents = [
            {
                "type": "text",
                "text": f"#{rank}",
                "size": "sm",
                "weight": "bold",
                "color": "#000000",
                "flex": 0,
                "contents": []
            },
            {
                "type": "text",
                "text": name,
                "size": "sm",
                "color": "#000000",
                "flex": 3,
                "wrap": True,
                "maxLines": 1
            },
            {
                "type": "text",
                "text": str(rating),
                "size": "sm",
                "color": "#666666",
                "flex": 0,
                "align": "end"
            }
        ]

        row = {
            "type": "box",
            "layout": "horizontal",
            "spacing": "md",
            "contents": row_contents,
            "paddingAll": "8px"
        }

        if highlight:
            row["borderWidth"] = "2px"
            row["borderColor"] = "#000000"
            row["cornerRadius"] = "4px"

        return row

    # 渲染前5名
    for i, entry in enumerate(top5):
        body_contents.append(make_row(entry, highlight=entry.get("is_user", False)))
        if i < len(top5) - 1:
            body_contents.append({"type": "separator", "color": "#DDDDDD"})

    # 用户不在前5，显示虚线分割 + 以用户为中心的附近名单
    if nearby_entries:
        body_contents.append({
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "· · · · · · · · · · · · · · · · · · · · · · · · · · · · · ·",
                    "size": "xxs",
                    "color": "#999999",
                    "align": "center"
                }
            ],
            "margin": "sm"
        })
        for i, entry in enumerate(nearby_entries):
            body_contents.append(make_row(entry, highlight=entry.get("is_user", False)))
            if i < len(nearby_entries) - 1:
                body_contents.append({"type": "separator", "color": "#DDDDDD"})

    body = {
        "type": "box",
        "layout": "vertical",
        "contents": body_contents,
        "paddingStart": "12px",
        "paddingEnd": "12px",
        "paddingBottom": "12px",
        "paddingTop": "4px"
    }

    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": header,
        "body": body
    }

    alt_text = get_multilingual_text(ranking_alt_text, user_id)
    return FlexMessage(alt_text=alt_text, contents=FlexContainer.from_dict(bubble))


def generate_song_list_flex(user_id, title, matching_songs, page, command_prefix, query, matched_sheets_map=None):
    """
    生成歌曲列表 Flex Message（黑白简约风，歌曲搜索列表共用）

    Args:
        user_id: 用户ID
        title: 列表标题
        matching_songs: 匹配的歌曲列表
        page: 当前页码（从1开始）
        command_prefix: 翻页命令前缀（如 "artist"、"designer" 或 "bpm"）
        query: 搜索关键词
        matched_sheets_map: designer 模式下的匹配谱面映射 {song_id: [sheet, ...]}

    Returns:
        FlexMessage: 歌曲列表
    """
    type_map = {
        'dx': 'DX',
        'std': 'STD',
        'utage': 'UTAGE'
    }

    difficulty_label_map = {
        'basic': 'BAS',
        'advanced': 'ADV',
        'expert': 'EXP',
        'master': 'MAS',
        'remaster': 'ReMAS'
    }

    page_size = 15
    total = len(matching_songs)
    total_pages = (total + page_size - 1) // page_size
    page = max(1, min(page, total_pages))

    start = (page - 1) * page_size
    end = start + page_size
    has_next = end < total

    # 超过每页限制时，取前19条 + 翻页按钮
    if has_next:
        page_songs = matching_songs[start:start + page_size - 1]
    else:
        page_songs = matching_songs[start:end]

    song_rows = []
    for idx, song in enumerate(page_songs):
        song_id = song.get('id', '')
        song_title = song.get('title', 'Unknown')
        song_type = type_map.get(song.get('type', ''), song.get('type', '').upper())

        # 副信息
        if matched_sheets_map and song_id in matched_sheets_map:
            # designer 模式：谱师名 + 匹配的难度标签
            sheets = matched_sheets_map[song_id]
            designers = []
            for s in sheets:
                diff_label = difficulty_label_map.get(s.get('difficulty', ''), s.get('difficulty', ''))
                designer_name = s.get('noteDesigner', '')
                designers.append(f"{designer_name} [{diff_label}]")
            sub_text = ' / '.join(designers)
        elif command_prefix == "bpm":
            sub_text = f"BPM: {song.get('bpm', '-')}"
        else:
            # artist 模式：艺术家名
            sub_text = song.get('artist') or '-'

        left_contents = [
            {
                "type": "text",
                "text": song_title,
                "size": "sm",
                "weight": "bold",
                "color": "#000000",
                "wrap": True,
                "maxLines": 2
            },
            {
                "type": "text",
                "text": sub_text,
                "size": "xs",
                "color": "#666666",
                "margin": "xs",
                "wrap": True,
                "maxLines": 1
            },
            {
                "type": "text",
                "text": song_type,
                "size": "xs",
                "color": "#999999",
                "margin": "xs"
            }
        ]

        row = {
            "type": "box",
            "layout": "horizontal",
            "spacing": "md",
            "margin": "md" if idx > 0 else "none",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "flex": 3,
                    "contents": left_contents
                },
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "→",
                        "data": f"search {song_id}",
                        "displayText": f"search {song_id}"
                    },
                    "style": "secondary",
                    "height": "sm",
                    "flex": 0
                }
            ]
        }

        song_rows.append(row)
        if idx < len(page_songs) - 1 or has_next:
            song_rows.append({"type": "separator", "margin": "sm"})

    # 翻页按钮
    if has_next:
        next_page = page + 1
        song_rows.append({
            "type": "button",
            "action": {
                "type": "postback",
                "label": f"Next Page ({next_page}/{total_pages})",
                "data": f"{command_prefix} {query} {next_page}",
                "displayText": f"{command_prefix} {query} {next_page}"
            },
            "style": "secondary",
            "height": "sm",
            "margin": "md"
        })

    # 跳转按钮（多页时显示）
    if total_pages > 1:
        jump_text = f"{command_prefix} {query} "
        song_rows.append({
            "type": "button",
            "action": {
                "type": "uri",
                "label": f"Go to ... (1~{total_pages})",
                "uri": f"https://line.me/R/oaMessage/{LINE_ACCOUNT_ID}/?{quote(jump_text)}"
            },
            "style": "secondary",
            "height": "sm",
            "margin": "sm"
        })

    header_box = {
        "type": "box",
        "layout": "vertical",
        "paddingAll": "16px",
        "contents": [
            {
                "type": "text",
                "text": title,
                "weight": "bold",
                "size": "lg",
                "color": "#000000"
            },
            {
                "type": "text",
                "text": f"Page {page}/{total_pages} • {total} songs",
                "size": "xs",
                "color": "#666666",
                "margin": "sm"
            },
            {
                "type": "separator",
                "color": "#DDDDDD",
                "margin": "md"
            }
        ]
    }

    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": header_box,
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": song_rows,
            "paddingAll": "16px",
            "backgroundColor": "#FFFFFF"
        },
        "styles": {"body": {"backgroundColor": "#FFFFFF"}}
    }

    return FlexMessage(
        alt_text=title,
        contents=FlexContainer.from_dict(bubble)
    )


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
                            "type": "uri",
                            "label": "→",
                            "uri": f"https://line.me/R/oaMessage/{LINE_ACCOUNT_ID}/?friend-rcd%20{friend_id}%20"
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
    title_text = select_text(title_texts, language=language, default_language='ja')

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

def generate_bot_status_flex(uptime_str, image_queue_size, web_queue_size,
                              tasks_today, song_count, dxdata_date, user_id=None):
    """
    生成 Bot 状态信息 Flex Message

    Args:
        uptime_str: 运行时长字符串（如 "1d 4h 22m"）
        image_queue_size: 图片队列当前排队任务数
        web_queue_size: web 队列当前排队任务数
        tasks_today: 今日已处理 image_gen 任务数
        song_count: dxdata 中的歌曲总数
        dxdata_date: dxdata 文件 mtime 的日期字符串（YYYY-MM-DD）
        user_id: 用户ID（用于多语言）

    Returns:
        FlexMessage: Bot 状态信息
    """
    lang = get_user_language(user_id)

    texts = {
        'title':       {'ja': 'JiETNG 稼働状態', 'en': 'JiETNG Service Status', 'zh': 'JiETNG 运行状态'},
        'uptime':      {'ja': '稼働時間',      'en': 'Uptime',          'zh': '运行时长'},
        'queue':       {'ja': 'キュー状況',    'en': 'Queue Status',    'zh': '队列状态'},
        'tasks_today': {'ja': '本日のタスク',  'en': 'Tasks Today',     'zh': '今日任务'},
        'songs':       {'ja': '楽曲データ',    'en': 'Songs DB',        'zh': '歌曲数据'},
    }
    # "曲" / songs / 首
    song_unit = select_text({'ja': '曲', 'en': 'songs', 'zh': '首'}, language=lang)

    queue_busy = (image_queue_size + web_queue_size) > 0
    queue_text = f"Image {image_queue_size} · Web {web_queue_size}"
    queue_color = "#FF9500" if queue_busy else "#34C759"
    songs_text = f"{song_count} {song_unit} · {dxdata_date}"

    def _row(label, value, value_color="#111111", margin="md"):
        return {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": label, "size": "xs", "color": "#666666", "flex": 0},
                {"type": "text", "text": value, "size": "sm", "weight": "bold",
                 "color": value_color, "align": "end"},
            ],
            "margin": margin,
        }

    _sep = {"type": "separator", "margin": "md"}
    content_rows = [
        _row(select_text(texts['uptime'], language=lang),      uptime_str, margin="none"),
        _sep,
        _row(select_text(texts['queue'], language=lang),       queue_text, value_color=queue_color),
        _sep,
        _row(select_text(texts['tasks_today'], language=lang), str(tasks_today), value_color="#AF52DE"),
        _sep,
        _row(select_text(texts['songs'], language=lang),       songs_text),
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
                    "text": select_text(texts['title'], language=lang),
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
