# 基本コマンド

アカウント、設定、状態、エクスポート、サポート関連のコマンドです。特記がない限り大文字小文字は区別されません。

## アカウントと設定

```text
bind
```

個別チャットで連携リンクを送信します。SEGA 連携と Import Token モードに対応しています。

```text
rebind
```

完全な SEGA 連携ユーザー向けに、パスワード、サーバー、Aime を更新します。SEGA ID は変更できません。

```text
settings
```

設定ページを開きます。言語、タイムゾーン、背景、表示設定、Import Token を管理できます。

```text
profile
getme
```

プロフィールと連携状態を表示します。

```text
unbind
unbind confirm
```

確認後、保存済みユーザーデータを削除します。

## 更新

```text
maimai update
update
```

maimai NET から最新成績を同期します。完全な SEGA 連携が必要で、自分自身にのみ作用します。

Import Token ユーザーはブックマークレットでアップロードしてください。

## エクスポート

```text
export json
export xml
```

DB の生データではなく、JiETNG が加工したプロフィール、Best、Recent、標準化済み成績フィールドを出力します。

## その他

```text
donate
status
rank
rank jp
rank intl
```

`rank` / `ranking` は DX Rating ランキングを表示します。`jp` / `intl` を指定できます。
