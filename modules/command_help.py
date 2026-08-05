"""Command-help lookup and message generation."""

import re

from modules.i18n import localized_catalog
from modules.message_manager import (
    generate_b_records_help_flex,
    generate_help_index_flex,
    generate_standard_help_flex,
)

COMMAND_HELP = localized_catalog("command_help")

EXACT_HELP_ALIASES = {
    "maimai update": "maimai_update",
    "update": "maimai_update",
    "friend list": "friend_list",
    "friends": "friend_list",
    "unbind": "unbind_prompt",
    "bind": "bind",
    "rebind": "rebind",
    "settings": "settings",
    "profile": "profile",
    "getme": "profile",
    "status": "status",
    "refreshmenu": "refreshmenu",
    "rank": "ranking",
    "ranking": "ranking",
    "random": "random_song",
    "rec": "score_recognition",
    "rec-flex": "score_recognition",
    "crop": "score_recognition",
    "fix-rcd": "score_recognition",
}

FIRST_WORD_HELP_ALIASES = {
    "friend-rcd": "friend_rcd",
    "search-record": "search_record",
    "search": "search_by_id",
    "calc-song": "calc_song",
    "artist": "search_by_artist",
    "designer": "search_by_designer",
    "bpm": "search_by_bpm",
    "rc": "rc",
    "export": "export",
    "成績エクスポート": "export",
    "成绩导出": "export",
    "calc": "calc_notes",
}

SUFFIX_HELP_ALIASES = {
    "record": "song_record",
    "song-record": "song_record",
    "のレコード": "song_record",
    "info": "song_info",
    "song-info": "song_info",
    "ってどんな曲": "song_info",
    "version-list": "version_songs",
    "のバージョンリスト": "version_songs",
    "level-list": "level_rank_list",
    "の定数リスト": "level_rank_list",
    "のレベルリスト": "level_rank_list",
    "records": "level_records",
    "record-list": "level_records",
    "のレコードリスト": "level_records",
    "achievement": "plate",
    "の達成状況": "plate",
    "progress": "level_rank_progress",
    "進捗": "level_rank_progress",
    "进度": "level_rank_progress",
}

REQUIRED_PARAM_HELP_WORDS = set(FIRST_WORD_HELP_ALIASES) | set(SUFFIX_HELP_ALIASES)
HIDDEN_HELP_COMMAND_WORDS = {"unknown"}
HELP_INDEX_WORDS = {"help", "commands", "command", "帮助", "幫助", "ヘルプ", "コマンド"}


def command_help_message(help_key, user_id=None):
    if help_key == "help_index":
        return generate_help_index_flex(user_id)
    if help_key == "b_records":
        return generate_b_records_help_flex(user_id)
    help_data = COMMAND_HELP.get(help_key)
    return generate_standard_help_flex(help_data, user_id) if help_data else None


def detect_command_help_key(text, *, b_command_words=(), progress_rank_pattern=""):
    lowered = re.sub(r"\s+", " ", text.strip()).lower()
    if not lowered:
        return None

    direct_match = EXACT_HELP_ALIASES.get(lowered)
    if direct_match:
        return direct_match
    if lowered in HELP_INDEX_WORDS:
        return "help_index"
    if lowered in SUFFIX_HELP_ALIASES:
        return SUFFIX_HELP_ALIASES[lowered]

    first_word = lowered.split(maxsplit=1)[0]
    if first_word in {"rank", "ranking"}:
        return "ranking"
    if first_word == "random":
        return "random_song"
    if first_word in b_command_words:
        return "b_records"
    if first_word in FIRST_WORD_HELP_ALIASES:
        return FIRST_WORD_HELP_ALIASES[first_word]

    suffix_matches = (
        (("のレコード", "song-record", "record"), "song_record"),
        (("ってどんな曲", "info", "song-info"), "song_info"),
        (("のバージョンリスト", "version-list"), "version_songs"),
        (("の定数リスト", "のレベルリスト", "level-list"), "level_rank_list"),
    )
    for suffixes, help_key in suffix_matches:
        if lowered.endswith(suffixes):
            return help_key

    if re.match(r".+(のレコードリスト|record-list|records)(?:[ 　]*\d*)?$", lowered):
        return "level_records"
    if re.match(r"^.+(の達成状況|achievement)(\s*-(uc|up|c))?$", lowered):
        return "plate"
    if progress_rank_pattern and re.match(
        fr"^.+\s*{progress_rank_pattern}\s*(progress|進捗|进度)\s*(?:-(uc|up|c))?$",
        lowered,
    ):
        return "level_rank_progress"
    return detect_missing_param_help_key(lowered)


def detect_missing_param_help_key(text):
    lowered = text.strip().lower()
    if lowered not in REQUIRED_PARAM_HELP_WORDS:
        return None
    return SUFFIX_HELP_ALIASES.get(lowered) or FIRST_WORD_HELP_ALIASES.get(lowered)
