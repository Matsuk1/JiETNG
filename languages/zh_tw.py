"""Traditional Chinese language plugin."""

from modules.zh_tw import to_traditional


LANGUAGE = {
    "code": "zh-tw",
    "label": "繁體中文",
    "aliases": ("zh-hant", "zh-hk", "zh-mo"),
    "fallbacks": ("zh",),
    "transforms": {"zh": to_traditional, "*": to_traditional},
}

TEXTS = {
    "web": {
        "loading": "載入中",
        "notice_html": "<strong>使用須知</strong><br>您輸入的所有資訊都會以加密形式安全保存，不會提供給第三方。<br><br>不過，本服務由個人營運，不提供官方保證或支援。<br>基於本服務的性質，如果您對安全性或營運方針有疑慮，請勿使用。<br>資訊提供完全基於您自己的判斷與責任。",
        "error": {
            "title": "錯誤",
            "fallback_message": "處理請求時發生錯誤。",
        },
        "unbind": {
            "title": "解除帳號綁定",
            "lead": "請在此瀏覽器中確認，將已綁定帳號從 JiETNG 移除。",
            "type": "類型",
            "account": "SEGA 帳號",
            "server": "伺服器",
            "warning": "這會刪除已保存的帳號憑證、相關設定、成績與最近成績。此操作無法復原。",
            "submit": "解除綁定",
        },
        "success": {
            "titles": {
                "settings": "設定已保存",
                "import_token": "Import Token 已產生",
                "unbind": "已解除綁定",
                "rebind": "更新成功",
                "bind": "綁定成功",
            },
            "descriptions": {
                "settings": "您的設定已成功保存。",
                "import_token": "請將此 Token 儲存至書籤工具中。首次上傳成績後，JiETNG 會初始化您的使用者資料。",
                "unbind": "您的已綁定帳號與已保存成績已從 JiETNG 移除。",
                "rebind": "您的帳號設定已成功更新。",
                "bind": "已成功與 JiETNG 連結。",
            },
            "token": {
                "shown_once": "Token 僅顯示這一次",
                "copy": "複製 Token",
                "copied": "已複製",
            },
        },
    }
}

# BEGIN MAIN TEXTS
TEXTS["main"] = {'account_already_bound': '已綁定 SEGA 帳號。如需重新綁定，請先使用 unbind 命令解除綁定。',
 'account_not_linked': '未綁定帳號。',
 'already_linked_title': '已綁定',
 'candidates_failed': '取得帳號列表失敗。請稍後再試。',
 'constant_out_of_range': '定數 {level} 超出范圍。請輸入 1.0~15.0 范圍內的數值。',
 'constant_precision': '定數 {level} 無效。僅支持一位小數（例如：13.2）。',
 'correction_format_body': '請使用 7 行格式：fix-rcd 曲名、達成率，隨後依次填寫 TAP、HOLD、SLIDE、TOUCH、BREAK；每行格式為 '
                           'CP/PF/GR/GD/MS。',
 'correction_format_title': '修正格式錯誤',
 'fields_required': '請填寫所有欄位。',
 'invalid_constant': '無效的定數。請輸入 1.0~15.0 范圍內的數值。',
 'invalid_credentials': 'SEGA ID 或密碼不正確。請檢查後重試。',
 'maintenance': '官方網站正在維護中。請稍後再試。',
 'no_linked_account': '目前沒有已綁定帳號。',
 'not_linked_title': '未綁定',
 'private_chat_title': '請在私聊使用',
 'recognition_failed_body': '無法讀取這張成績圖，請確認圖片完整後重試。',
 'recognition_failed_title': '識別失敗',
 'score_image_required_body': '請回復一張成績圖并發送 {command_text}。',
 'score_image_required_title': '缺少成績圖',
 'sega_id_immutable': '無法更改 SEGA ID。',
 'token_invalid': '令牌無效。',
 'token_missing': '未提供令牌。',
 'unbind_token_invalid': '令牌無效或已過期。請重新發送 unbind。',
 'vote_success': '感謝您的投票！\n'
                 '\n'
                 '支持: {support_count}人 ({support_percent:.1f}%)\n'
                 '反對: {oppose_count}人 ({oppose_percent:.1f}%)'}
# END MAIN TEXTS

# BEGIN COMMAND HELP
TEXTS["command_help"] = {'bind': '命令: bind\n'
         '說明: 返回一次性 SEGA 帳號綁定連結，用於首次綁定帳號。\n'
         '參數: 無需參數: 直接發送 bind。\n'
         '限制: 只能在私聊使用，群聊會返回安全提示。\n'
         '示例: bind',
 'calc_notes': '命令: calc <tap> <hold> <slide> [touch] <break>\n'
               '說明: 根據譜面物量計算單個 Note 分值。\n'
               '參數: 必填: <tap> <hold> <slide> <break>，當只給 4 個數字時按 TAP/HOLD/SLIDE/BREAK 解析。\n'
               '可選: [touch]，當給 5 個數字時第 4 個為 TOUCH，第 5 個為 BREAK。\n'
               '格式: 所有參數必須是非負整數，用空格分隔。\n'
               '示例: calc 500 50 80 30\n'
               'calc 500 50 80 20 30',
 'calc_song': '命令: calc-song <6位歌曲ID>\n'
              '說明: 計算指定歌曲的達成率相關資訊。\n'
              '參數: 必填: <6位歌曲ID>，必須是完整歌曲 ID，不支持曲名。\n'
              '格式: calc-song 後空一格再寫 ID；ID 長度必須為 6。\n'
              '示例: calc-song 114514',
 'export': '命令: export <json|xml> / 成績導出 <json|xml>\n'
           '說明: 將自己的成績資料導出為指定格式。\n'
           '參數: 必填: <格式>，只能填寫 json 或 xml。\n'
           '輸出: 成功後返回臨時下載連結和複製連結按鈕。\n'
           '要求: 需要已有成績資料；如果沒有資料會返回空資料提示。\n'
           '示例: export json\n'
           '成績導出 xml',
 'friend_list': '命令: friend list / friends\n'
                '說明: 查看已添加的好友列表。\n'
                '參數: 無需參數: 直接發送命令，會從 maimai NET 讀取好友列表。\n'
                '示例: friends',
 'friend_rcd': '命令: friend-rcd <好友編號或名稱> [成績圖類型] [篩選參數]\n'
               '說明: 查看指定好友的成績。\n'
               '參數: 必填: <好友編號或名稱>，編號來自 friends 列表，也可以填寫可匹配的好友名。\n'
               '可選: [成績圖類型]，默認 best50；支持 b50、b40、ab50、ap50、fdx50、r50 等 B 系列類型。\n'
               '可選: [篩選參數]，與 b50-help 中的篩選參數一致，例如 -lv、-diff、-scr、-page。\n'
               '示例: friend-rcd 1\n'
               'friend-rcd 1 b50 -lv 14 14.9',
 'level_rank_list': '命令: <等級或定數> level-list / <等級或定數>の定數リスト\n'
                    '說明: 查看指定等級或定數相關歌曲列表。\n'
                    '參數: 必填: <等級或定數>，支持 13、13+、14、13.6 等格式。\n'
                    '匹配: 整數/帶 + 按等級匹配，小數按定數精確匹配。\n'
                    '示例: 13.6 level-list\n'
                    '14+ level-list',
 'level_rank_progress': '命令: <等級或分類><評價> progress [-uc|-up|-c]\n'
                        '說明: 查看指定等級或分類中評價目標的達成進度。\n'
                        '參數: 必填: <等級或分類>，等級支持 11-15；分類支持 '
                        'vocaloid、touhou、popani、gekichu、game、maimai。\n'
                        '必填: <評價>，緊跟等級/分類書寫，支持 s、s+、ss、ss+、sss、sss+、fc、fc+、ap、ap+、fdx、fdx+。\n'
                        '可選: -uc 僅看未完成目標，-up 僅看未游玩，-c 僅看已完成目標。\n'
                        '格式: 等級可直接連寫，例如 14sss+ progress；分類建議和評價之間加空格，例如 vocaloid sss+ progress。\n'
                        '示例: 14sss+ progress\n'
                        '13ap progress -uc\n'
                        'vocaloid sss+ progress\n'
                        'popani ss+ progress -up',
 'level_records': '命令: <等級或定數> records [頁碼] / <等級或定數> record-list [頁碼]\n'
                  '說明: 查看指定等級或定數的成績列表。\n'
                  '參數: 必填: <等級或定數>，支持 13、13+、14、13.6 等格式。\n'
                  '可選: [頁碼]，正整數，從 1 開始；省略時顯示第 1 頁。\n'
                  '匹配: 整數/帶 + 按等級匹配，小數按定數精確匹配。\n'
                  '示例: 13.6 records\n'
                  '14 records 2',
 'maimai_update': '命令: maimai update / update\n'
                  '說明: 從 maimai NET 獲取并更新已游玩的歌曲成績資料。\n'
                  '參數: 無需參數: 直接發送命令即可開始同步。\n'
                  '示例: maimai update\n'
                  '註意: 需要先綁定 SEGA 帳號。',
 'plate': '命令: <牌子名> achievement [-uc|-up|-c] / <牌子名>の達成狀況\n'
          '說明: 查看版本牌子或稱號類目標的完成情況。\n'
          '參數: 必填: <牌子名>，寫在 achievement 前面，例如 真極、檄將 等。\n'
          '可選: -uc 僅看未完成項目，-up 僅看未游玩項目，-c 僅看已完成項目。\n'
          '格式: 過濾項寫在命令最後；不寫過濾項時顯示完整完成度。\n'
          '示例: 真極 achievement\n'
          '真極 achievement -uc',
 'profile': '命令: profile / getme\n'
            '說明: 查看自己的 JiETNG 帳號資訊，包括綁定狀態、伺服器和語言設定。\n'
            '參數: 無需參數: 直接發送 profile 或 getme。\n'
            '限制: 只能在私聊使用，避免公開個人資訊。\n'
            '示例: profile\n'
            'getme',
 'random_song': '命令: random [條件]\n'
                '說明: 隨機推薦一首歌曲。\n'
                '參數: 可選: [條件]，可寫等級、定數、譜面類型、難度等關鍵詞。\n'
                '格式: 多個條件用空格分隔；省略條件時從全部歌曲中隨機。\n'
                '示例: random\n'
                'random 13+ dx\n'
                'random 14 mas',
 'ranking': '命令: rank [jp|intl] / ranking [jp|intl]\n'
            '說明: 查看 DX Rating 排行榜。私聊顯示總體榜，群聊顯示目前 LINE 群內榜。\n'
            '參數: 可選: [伺服器]，支持 jp、intl；省略時使用目前使用者綁定的伺服器。\n'
            '格式: 伺服器參數寫在 rank / ranking 後面，用空格分隔。\n'
            '示例: rank\n'
            'ranking intl',
 'rc': '命令: rc <定數>\n'
       '說明: 查詢 Rating Composition / レート內訳相關資訊。\n'
       '參數: 必填: <定數>，支持 1.0 到 15.0 之間的數字。\n'
       '格式: 可寫整數或小數，例如 13、13.6、14.9。\n'
       '限制: 超出 1.0-15.0 或無法轉成數字會返回輸入錯誤。\n'
       '示例: rc 14\n'
       'rc 13.6',
 'rebind': '命令: rebind\n'
           '說明: 返回 SEGA 帳號編輯連結，用於更新已綁定帳號的資訊。\n'
           '參數: 無需參數: 直接發送 rebind。\n'
           '要求: 必須已經綁定 SEGA 帳號。\n'
           '限制: 只能在私聊使用。\n'
           '示例: rebind',
 'refreshmenu': '命令: refreshmenu\n'
                '說明: 根據目前綁定狀態重新關聯發送者自己的 LINE Rich Menu。\n'
                '參數: 無需參數: 直接發送 refreshmenu。\n'
                '限制: 僅影響發送者自己的 Rich Menu。\n'
                '示例: refreshmenu',
 'score_recognition': '命令: rec\n'
                      'rec-flex\n'
                      'crop\n'
                      'fix-rcd <曲名>\n'
                      '說明: rec 識別完整成績；能完全校驗時返回成績圖片，需要修正時返回可複製的修正卡片。rec-flex 是 rec 的 -flex '
                      '後綴形式，會強制返回 FlexMsg。crop 只返回裁切圖，用於檢查識別區域。\n'
                      '參數: rec、rec-flex 和 crop 都必須回復一張成績圖，不接受其他參數。\n'
                      'fix-rcd: 第一行填寫不含 [DX]/[STD] 的曲名，第二行填寫達成率，隨後依次填寫 '
                      'TAP、HOLD、SLIDE、TOUCH、BREAK。\n'
                      '格式: 達成率可帶 %；判定行必須為 CP/PF/GR/GD/MS 五個非負整數。\n'
                      '示例: rec-flex\n'
                      'fix-rcd HECATONCHEIR\n'
                      '98.4298%\n'
                      '357/211/46/6/3\n'
                      '58/15/3/0/1\n'
                      '130/0/1/1/1\n'
                      '93/1/0/0/0\n'
                      '54/38/5/2/1',
 'search_by_artist': '命令: artist <關鍵詞> [頁碼]\n'
                     '說明: 按藝術家名搜索歌曲。\n'
                     '參數: 必填: <關鍵詞>，artist 後面的文本會作為藝術家名進行不區分大小寫的包含匹配。\n'
                     '可選: [頁碼]，正整數，從 1 開始；寫在關鍵詞最後。\n'
                     '限制: 僅限私聊使用，避免群聊刷屏。\n'
                     '示例: artist Nanahira\n'
                     'artist sasakure 2',
 'search_by_bpm': '命令: bpm <BPM或范圍> [頁碼]\n'
                  '說明: 按 BPM 精確值或范圍搜索歌曲。\n'
                  '參數: 必填: <BPM或范圍>，支持單值、連字符范圍、空格范圍。\n'
                  '單值: bpm 180 表示精確匹配 BPM 180。\n'
                  '范圍: bpm 0-120 或 bpm 120 180 表示閉區間，端點可為 0。\n'
                  '可選: [頁碼]，正整數，從 1 開始；寫在最後。\n'
                  '限制: 僅限私聊使用。\n'
                  '示例: bpm 180\n'
                  'bpm 0-120\n'
                  'bpm 120 180 2',
 'search_by_designer': '命令: designer <關鍵詞> [頁碼]\n'
                       '說明: 按譜面設計師名搜索歌曲。\n'
                       '參數: 必填: <關鍵詞>，designer 後面的文本會匹配各難度譜面的 noteDesigner 字段。\n'
                       '可選: [頁碼]，正整數，從 1 開始；寫在關鍵詞最後。\n'
                       '限制: 僅限私聊使用，避免群聊刷屏。\n'
                       '示例: designer Jack\n'
                       'designer 譜面 2',
 'search_by_id': '命令: search <6位歌曲ID>\n'
                 '說明: 用歌曲 ID 精確查詢歌曲資訊。\n'
                 '參數: 必填: <6位歌曲ID>，必須是完整歌曲 ID，不支持曲名。\n'
                 '格式: search 後空一格再寫 ID；ID 長度必須為 6。\n'
                 '示例: search 114514',
 'search_record': '命令: search-record <6位歌曲ID>\n'
                  '說明: 用歌曲 ID 精確查詢自己的單曲成績。\n'
                  '參數: 必填: <6位歌曲ID>，必須是完整歌曲 ID，不支持曲名。\n'
                  '格式: 6 個字符，通常為數字；不足或過長都會視為無效。\n'
                  '示例: search-record 114514',
 'settings': '命令: settings\n'
             '說明: 返回個人設定頁面連結，用於修改時區、語言、背景圖片、隱私等選項。\n'
             '參數: 無需參數: 直接發送 settings。\n'
             '限制: 只能在私聊使用。\n'
             '示例: settings',
 'song_info': '命令: <曲名> info / <曲名> song-info / <曲名>ってどんな曲\n'
              '說明: 查詢歌曲基本資訊、譜面資訊和 BPM；也可以回復成績圖片直接發送 info，自動識別曲名。\n'
              '參數: 文本查詢時填寫 <曲名>，可以是完整曲名、部分曲名或別名；圖片查詢時無需填寫曲名。\n'
              '匹配: 如果匹配到多首歌，會返回可選擇的候選結果。\n'
              '示例: ヒバナ info\n'
              'ヒバナってどんな曲\n'
              '（回復圖片）info',
 'song_record': '命令: <曲名> record / <曲名> song-record / <曲名>のレコード\n'
                '說明: 按曲名或別名查詢自己的單曲成績。\n'
                '參數: 必填: <曲名>，寫在 record / song-record 前面，可以是完整曲名、部分曲名或別名。\n'
                '匹配: 如果匹配到多首歌，會返回可選擇的候選結果。\n'
                '示例: ヒバナ record\n'
                'ヒバナ song-record',
 'status': '命令: status\n說明: 查看機器人服務狀態，包括運行時間、任務隊列和系統資源。\n參數: 無需參數: 直接發送 status。\n示例: status',
 'unbind_prompt': '命令: unbind\n'
                  '說明: 返回一次性 SEGA 帳號解除綁定連結，在瀏覽器內確認後才會刪除帳號資料。\n'
                  '參數: 無需參數: 直接發送 unbind。\n'
                  '要求: 必須已經綁定 SEGA 帳號或已啟用 Import Token 帳號。\n'
                  '限制: 只能在私聊使用。\n'
                  '示例: unbind',
 'version_songs': '命令: <版本名> version-list / <版本名>のバージョンリスト\n'
                  '說明: 查看指定版本歌曲列表。\n'
                  '參數: 必填: <版本名>，寫在 version-list 前面，支持版本完整名或可識別簡稱。\n'
                  '格式: 版本名可包含空格；整段 version-list 前的文本都會作為版本查詢詞。\n'
                  '示例: BUDDiES version-list\n'
                  'PRiSM PLUS version-list'}
# END COMMAND HELP

# BEGIN TEMPLATE TEXTS
TEXTS["web"]["bind"] = {
    "pageTitle": "SEGA 帳號綁定 | JiETNG",
    "pageTitleRebind": "編輯帳號設定 | JiETNG",
    "heading": "SEGA 帳號綁定",
    "headingRebind": "編輯帳號設定",
    "labelSegaid": "SEGA ID",
    "labelPassword": "SEGA 密碼",
    "labelVersion": "版本",
    "optJp": "日本版",
    "optIntl": "國際版",
    "labelTimezone": "時區",
    "labelLanguage": "語言",
    "languagePlatformHint": "語言設定可能不會套用到 LINE 以外的第三方平台。",
    "labelBindType": "綁定方式",
    "optBindSega": "SEGA 帳號",
    "optBindImport": "僅使用 Import Token",
    "bindTypeImportHelp": "不保存 SEGA 帳號密碼，之後透過匯出工具上傳成績。",
    "submitBtn": "綁定",
    "submitBtnImport": "產生 Token",
    "submitBtnRebind": "更新",
    "noticeTitle": "使用須知",
    "aimeModalTitle": "選擇 Aime",
    "aimeModalDescription": "請選擇要綁定的帳號。",
    "aimeConfirm": "確定",
    "aimeFallbackName": "Aime 帳號",
    "ratingLabel": "Rating",
    "trophyLabel": "稱號",
    "accountListError": "無法取得帳號列表。"
}
TEXTS["web"]["bind_notice_html"] = "您輸入的所有資訊都會以加密形式安全保存，不會提供給第三方。<br><br>不過，本服務由個人營運，不提供官方保證或支援。基於本服務的性質，如果您對安全性或營運政策有疑慮，請勿使用。資訊提供完全基於您自己的判斷與責任。"
TEXTS["web"]["settings"] = {
    "pageTitle": "設定 | JiETNG",
    "heading": "設定",
    "labelLanguage": "語言",
    "languagePlatformHint": "語言設定可能不會套用到 LINE 以外的第三方平台。",
    "labelTimezone": "時區",
    "labelBgEnabled": "背景圖片",
    "rankingPanelTitle": "排行榜設定",
    "labelGlobalRanking": "參與總體排行榜",
    "metaGlobalRanking": "會顯示在私聊的 rank / ranking 中。",
    "labelGroupRanking": "參與群內排行榜",
    "metaGroupRanking": "會顯示在同一個 LINE 群內的 rank / ranking 中。",
    "labelBgBlur": "背景模糊",
    "labelBgOverlay": "背景淡化",
    "bgHint": "不選擇時，會從所有背景中隨機使用。",
    "sectionCustomBg": "自訂背景",
    "customBgHint": "上傳您自己的背景圖片（限 1 張，5MB 以內）。",
    "customBgUploaded": "已上傳",
    "labelCustomBg": "選擇圖片",
    "uploadSub": "PNG / JPG / JPEG / WebP（5MB 以內）",
    "uploadBtn": "上傳",
    "uploadFailed": "上傳失敗。",
    "deleteCustomBgBtn": "刪除",
    "deleteCustomBgConfirm": "確定刪除自訂背景嗎？",
    "submitBtn": "保存",
    "importTokenTitle": "成績匯入 Token",
    "importTokenHelp": "用於讓外部工具把處理後的成績 JSON 上傳到 JiETNG。",
    "importTokenCreate": "產生 Token",
    "importTokenNoteLabel": "Token 標題",
    "importTokenNotePlaceholder": "例如：Bookmarklet / 工具名稱",
    "importTokenNoteRequired": "請輸入 Token 標題。",
    "importTokenCreateLabel": "新的 Token",
    "importTokenCreateMeta": "產生後，Token 只會顯示這一次。",
    "importTokenResultTitle": "Token（只顯示這一次）",
    "importTokenCopy": "複製",
    "importTokenCopied": "已複製",
    "importTokenEmpty": "還沒有 Token。",
    "importTokenRevoke": "撤銷",
    "importTokenRevoked": "已撤銷",
    "importTokenDelete": "刪除",
    "importTokenCreateError": "產生 Token 失敗。",
    "importTokenRevokeConfirm": "確定撤銷這個匯入 Token 嗎？",
    "importTokenRevokeError": "撤銷失敗。",
    "importTokenDeleteConfirm": "確定刪除這個已撤銷的匯入 Token 嗎？",
    "importTokenDeleteError": "刪除失敗。"
}
TEXTS["web"]["settings_permissions"] = {
    "panelTitle": "存取權限管理",
    "ownerLabel": "建立者",
    "revokeBtn": "撤銷",
    "revokeConfirm": "確定撤銷此服務的存取權限嗎？",
    "revokeError": "撤銷失敗，請重試"
}
# END TEMPLATE TEXTS

# BEGIN GENERATED MESSAGE TEXTS
MESSAGE_TEXTS = {'access_error_text': '🙇 現在訪問量很大…請稍後再試！',
 'already_bound_text': '目前已經綁定 SEGA 帳號。\n'
                       '\n'
                       '修改密碼、伺服器版本或 Aime 請使用 rebind。\n'
                       '修改時區、語言、背景圖片、隱私等個人設定請使用 settings。\n'
                       '如需綁定其他帳號，請先使用 unbind 解除目前綁定。',
 'bind_group_warning_text': 'bind 只能在私聊使用。請直接向機器人發送消息。',
 'calc_button_text': 'Note 計算',
 'calc_flex_text': {'alt_multi': 'Note 計算結果',
                    'alt_single': 'Note 計算結果',
                    'max_tap_great': '最多 {count} 個 TAP GREAT',
                    'subtitle': 'Note 計算',
                    'title_distribution': 'Note 分布'},
 'cannot_do_for_others_text': '該命令只能用於你自己的帳號。',
 'devtoken_create_failed_text': '❌ Token 建立失敗。',
 'devtoken_create_success_text': '✅ 開發者 Token 建立成功！\n'
                                 '\n'
                                 'Token ID: {token_id}\n'
                                 'Token: {token}\n'
                                 '備註: {note}\n'
                                 '建立時間: {created_at}\n'
                                 '\n'
                                 '⚠️ 此 Token 僅顯示一次，請妥善保管。',
 'devtoken_info_not_found_text': '❌ 找不到 Token。',
 'devtoken_info_text': '📝 Token 詳細資訊\n'
                       '\n'
                       'Token ID: {token_id}\n'
                       'Token: {token}\n'
                       '備註: {note}\n'
                       '建立者: {created_by}\n'
                       '建立時間: {created_at}\n'
                       '最後使用: {last_used}\n'
                       '狀態: {status}',
 'devtoken_list_empty_text': '還沒有建立任何 Token。',
 'devtoken_list_header_text': '📋 開發者 Token 列表',
 'devtoken_revoke_failed_text': '❌ 找不到 Token {token_id}。',
 'devtoken_revoke_success_text': '✅ 已撤銷 Token {token_id}。',
 'devtoken_usage_text': '📚 開發者 Token 管理\n'
                        '\n'
                        'devtoken create <備註> - 建立新 Token\n'
                        'devtoken list - 顯示所有 Token\n'
                        'devtoken revoke <token_id> - 撤銷 Token\n'
                        'devtoken info <token_id> - 顯示 Token 詳情',
 'dxdata_current_stats_text': '📈 目前: {songs}首歌曲 / {sheets}個譜面',
 'dxdata_fetch_failed_text': '❌ 資料獲取失敗！',
 'dxdata_first_update_text': '(首次更新完成！)',
 'dxdata_initial_stats_sheets_text': '📊 譜面: {count}個',
 'dxdata_initial_stats_songs_text': '📈 歌曲: {count}首',
 'dxdata_last_update_text': '📅 上次更新: {timestamp}',
 'dxdata_new_sheets_text': '📊 新增譜面: +{count}個',
 'dxdata_new_songs_text': '🎵 新增歌曲: +{count}首',
 'dxdata_no_new_sheets_text': '📊 新增譜面: 無',
 'dxdata_no_new_songs_text': '🎵 新增歌曲: 無',
 'dxdata_parse_failed_text': '❌ 資料解析失敗！',
 'dxdata_sheets_decreased_text': '📊 譜面: {count}個',
 'dxdata_songs_decreased_text': '🎵 歌曲: {count}首',
 'dxdata_update_notification_text': '📢 Dxdata 更新通知\n\n{message}',
 'dxdata_update_success_text': '✅ Dxdata 更新成功！',
 'dxdata_update_text': '✅ Dxdata 已更新！',
 'export_alt_text': '成績資料已導出',
 'export_empty_text': '還沒有可導出的成績資料。請先使用『maimai update』更新後再試。',
 'export_failed_text': '成績資料導出失敗，請稍後再試。',
 'export_flex_button_text': '下載',
 'export_flex_copy_button_text': '複製連結',
 'export_flex_footnote_text': '下載連結將在 {ttl} 分鐘後失效',
 'export_flex_summary_text': 'Best: {best} 條  ·  Recent: {recent} 條\n格式: {fmt}（{size_kb} KB）',
 'export_flex_title_text': '成績資料已導出',
 'friend_error_text': '還沒有收藏的好友。',
 'friend_list_alt_text': '收藏的好友',
 'friend_rcd_error_text': '指定使用者不在你的好友列表中。',
 'friend_rcd_group_warning_text': '好友成績命令只能在私聊使用。請直接向機器人發送消息。',
 'friend_rcd_text': '{name} 的資料',
 'info_error_text': '你的 maimai 玩家資料尚未保存。請先使用『maimai update』更新後再試。',
 'input_error_text': '無法識別該命令，請檢查輸入內容。',
 'language_set_success_text': '✅ 語言已設定為中文！',
 'level_not_supported_text': '不支持該等級的定數表。\n僅支持12級及以上。',
 'level_record_not_found_text': '指定等級「{level}」的第 {page} 頁記錄可能不存在...',
 'level_record_page_hint_text': '這是第 {page} 頁的資料！',
 'maintenance_error_text': '🔧 咦？官方網站好像在維護中！\n維護時間無法訪問，請稍後再試~',
 'mention_error_text': '被提到的使用者尚未註冊 JiETNG。',
 'mention_no_matching_data_text': '被提到的使用者沒有符合條件的成績資料。',
 'mention_record_error_text': '被提到的使用者還沒有 maimai 成績資料。',
 'nearby_stores_alt_text': '附近的 maimai 機廳',
 'no_matching_data_text': '沒有找到符合條件的成績資料。',
 'notice_header_text': '📢 公告',
 'perm_request_accept_button_text': '接受',
 'perm_request_accept_success_text': '✅ 已接受存取權限請求！\n'
                                     '\n'
                                     'Token ID: {token_id}\n'
                                     '申請者: {requester_name}\n'
                                     '\n'
                                     '該 token 現在可以訪問你的帳戶資訊了。',
 'perm_request_already_processed_text': '該請求已經處理過了。',
 'perm_request_notification_alt_text': '你有 {count} 個存取權限請求',
 'perm_request_notification_subtitle_text': '{count} 個新請求',
 'perm_request_notification_title_text': '存取權限請求',
 'perm_request_reject_button_text': '拒絕',
 'perm_request_reject_success_text': '✅ 已拒絕存取權限請求。\n\nToken ID: {token_id}\n申請者: {requester_name}',
 'plate_error_text': '沒有找到指定的牌子。',
 'private_info_group_warning_text': '個人資訊命令只能在私聊使用。請直接向機器人發送消息。',
 'quick_reply_labels': {'account_bind': '綁定帳號',
                        'all_best_50': 'All Best 50',
                        'maimai_update': '更新資料',
                        'recent_50': 'Recent 50',
                        'retry': '再試一次',
                        'support': '幫助'},
 'ranking_alt_text': 'Rating 排行榜',
 'ranking_no_data_text': '暫無排行榜資料。',
 'ranking_title_text': 'Rating 排行榜',
 'rate_limit_msg_text': '🔄 系統目前較為繁忙，請稍後再試。',
 'rebind_button_text': '編輯帳號',
 'rebind_description_text': '修改已綁定 SEGA 帳號的密碼、伺服器版本或 Aime。',
 'rebind_group_warning_text': 'rebind 只能在私聊使用。請直接向機器人發送消息。',
 'rebind_msg_text': '✅ SEGA 帳號資訊已更新。',
 'rebind_not_bound_text': '尚未綁定 SEGA 帳號。請先使用 bind 完成綁定。',
 'rebind_title_alt_text': '編輯帳號設定',
 'record_error_text': '還沒有 maimai 成績資料。請先使用『maimai update』更新後再試。',
 'save_image_button_text': '保存圖片',
 'search_group_warning_text': 'artist / designer / bpm 搜索只能在私聊使用。',
 'sega_bind_alt_text': '綁定 SEGA 帳號',
 'sega_bind_button_text': '開始綁定',
 'sega_bind_description_text': '打開首次綁定用的 SEGA 帳號綁定頁面。',
 'sega_bind_title_text': '綁定 SEGA 帳號',
 'segaid_error_text': '你還沒有綁定 SEGA 帳號吧？',
 'settings_button_text': '打開設定',
 'settings_description_text': '修改時區、語言、背景圖片和隱私設定。',
 'settings_group_warning_text': 'settings 只能在私聊使用。請直接向機器人發送消息。',
 'settings_title_alt_text': '個人設定',
 'song_error_text': '沒有找到符合條件的歌曲。',
 'song_info_alt_text': '歌曲資訊',
 'song_record_alt_text': '歌曲成績',
 'store_error_text': '🥹 附近沒有找到遊戲廳',
 'system_error_text': '😵 發生系統錯誤…已通知管理員。請稍後再試。',
 'unbind_button_text': '打開解除綁定頁面',
 'unbind_description_text': '在瀏覽器內確認并刪除已綁定 SEGA 帳號和已保存成績資料。',
 'unbind_group_warning_text': 'unbind 只能在私聊使用。請直接向機器人發送消息。',
 'unbind_title_alt_text': '解除帳號綁定',
 'update_result_flex_text': {'alt_text_error': '成績更新失敗',
                             'alt_text_success': '成績更新完成',
                             'elapsed_time_label': '耗時',
                             'failed': '失敗',
                             'status_best_records': 'Best 成績',
                             'status_label': '未更新項目',
                             'status_recent_records': 'Recent 成績',
                             'status_user_info': '玩家資料',
                             'summary_section': '概要',
                             'title_error': '成績更新失敗',
                             'title_success': '成績更新完成',
                             'update_time_label': '更新時間'},
 'user_info_flex_text': {'account_section': '帳號',
                         'alt_text': '使用者資訊',
                         'copy_id': '複製ID',
                         'intl_server': '國際服',
                         'jp_server': '日服',
                         'lang_en': '英語',
                         'lang_ja': '日語',
                         'lang_zh': '中文',
                         'language_label': '語言',
                         'last_update_label': '最後更新',
                         'name_label': '玩家名稱',
                         'not_bound': '未綁定',
                         'password_label': '密碼',
                         'profile_section': '玩家資訊',
                         'rating_label': 'Rating',
                         'sega_id_label': 'SEGA ID',
                         'server_label': '伺服器',
                         'settings_section': '設定',
                         'title': '使用者資訊',
                         'user_id_label': 'LINE ID'},
 'version_error_text': '沒有找到指定的版本。',
 'view_info_button_text': '查看歌曲資訊',
 'view_record_button_text': '查看成績'}
# END GENERATED MESSAGE TEXTS

TEXTS["messages"] = MESSAGE_TEXTS
