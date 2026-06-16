# プライバシーポリシー

## 概要

JiETNG は個人が保守する maimai DX スコア管理ツールです。このページでは現在のプロジェクトが収集・処理する可能性のあるデータを説明します。

## データ元

- **SEGA アカウント同期**：連携ページで SEGA ID、パスワード、サーバー、Aime を入力し、maimai NET から成績を同期します。
- **Import Token 取り込み**：設定ページでユーザー Import Token を作成し、ブックマークレットまたは信頼できるツールが加工済み `profile`、`best`、`recent` をアップロードします。

## 保存されるデータ

LINE ユーザー ID、言語/タイムゾーン/背景設定、暗号化された SEGA 認証情報、サーバー、Aime、maimai プロフィール表示情報、Best/Recent、Import Token のハッシュと状態、開発者 Token、権限関係、コマンド利用イベント、エラーログを保存する場合があります。

Import Token の平文は一度だけ表示され、サーバーにはハッシュが保存されます。

## 利用目的

成績同期または取り込み、スコア画像と進捗表示の生成、設定/エクスポート/API 機能、不正利用防止、デバッグ、サービス安定化のために使います。

## 削除とエクスポート

```text
unbind
unbind confirm
```

保存済みユーザーデータを削除します。

```text
export json
export xml
```

内部 DB の生構造ではなく、加工済み成績データを出力します。

## セキュリティ

- Web ページは HTTPS を使用します。
- SEGA パスワードは暗号化して保存されます。
- Import Token と開発者 Token はパスワード同様に扱ってください。
- 撤回済み Token はアップロードやアクセスを継続できません。

## 連絡先

- GitHub Issues：[github.com/Matsuk1/JiETNG/issues](https://github.com/Matsuk1/JiETNG/issues)
- Discord：[サーバーに参加](https://discord.gg/NXxFn9T8Xz)

発効日：2026-06-16
