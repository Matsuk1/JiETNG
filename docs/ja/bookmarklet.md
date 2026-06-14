---
title: ブックマークレットツール
description: maimai 公式サイトの現在のログイン状態を使って Best 50 スコア画像を生成する JiETNG ブックマークレット。
---

# JiETNG ブックマークレットツール

このブックマークレットは maimai DX 公式モバイルサイト上で動作します。現在のブラウザのログイン状態を使ってプロフィールと Best レコードを読み取り、JiETNG API でスコア画像を生成します。SEGA ID のパスワードを読み取ったり入力させたりすることはありません。

<div class="bookmarklet-installer">
  <div class="bookmarklet-card">
    <img src="/logo.svg" alt="JiETNG" class="bookmarklet-logo">
    <div>
      <p class="bookmarklet-eyebrow">Bookmarklet</p>
      <h2>JiETNG スコア画像</h2>
      <p>下のボタンをブラウザのブックマークバーへドラッグしてください。maimai 公式サイトにログインした後、そのブックマークをクリックすると同じページ上にスコア画像が表示されます。</p>
    </div>
    <a id="jietng-bookmarklet-link" class="bookmarklet-button" href="#">JiETNG スコア画像</a>
    <button id="jietng-copy-bookmarklet" class="bookmarklet-copy" type="button">ブックマークURLをコピー</button>
    <p id="jietng-copy-status" class="bookmarklet-status"></p>
  </div>
</div>

## 使い方

1. 上の **JiETNG スコア画像** ボタンをブックマークバーへドラッグします。
2. 公式 maimai DX サイトを開いてログインします。
   - `https://maimaidx.jp/maimai-mobile/home/`
   - `https://maimaidx-eng.com/maimai-mobile/home/`
3. 公式ページ上で保存したブックマークをクリックします。
4. 生成が完了すると、ページ内のオーバーレイで画像を確認できます。

ドラッグ操作が使いにくい場合は、**ブックマークURLをコピー** を押して手動でブックマークを作成し、URL 欄にコピーした `javascript:...` を貼り付けてください。

<script setup>
import { onMounted } from 'vue'

onMounted(async () => {
  const link = document.getElementById('jietng-bookmarklet-link')
  const copyButton = document.getElementById('jietng-copy-bookmarklet')
  const status = document.getElementById('jietng-copy-status')
  let bookmarklet = ''

  try {
    const response = await fetch('/bookmarklet/maimai-session-image.txt', { cache: 'no-store' })
    bookmarklet = (await response.text()).trim()
    link.href = bookmarklet
  } catch (error) {
    status.textContent = 'ブックマークレットの読み込みに失敗しました。しばらくしてから再試行してください。'
    copyButton.disabled = true
  }

  copyButton.addEventListener('click', async () => {
    if (!bookmarklet) return
    try {
      await navigator.clipboard.writeText(bookmarklet)
      status.textContent = 'コピーしました。手動でブックマークを作成し、URL として貼り付けてください。'
    } catch (error) {
      status.textContent = 'コピーに失敗しました。ボタンをブックマークバーへドラッグしてください。'
    }
  })
})
</script>

<style>
.bookmarklet-installer {
  margin: 24px 0 28px;
}

.bookmarklet-card {
  display: grid;
  grid-template-columns: 64px 1fr;
  gap: 16px;
  align-items: center;
  padding: 20px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(37, 99, 235, .08), rgba(255, 255, 255, .92));
  box-shadow: 0 14px 36px rgba(15, 23, 42, .10);
}

.bookmarklet-logo {
  width: 64px;
  height: 64px;
  border-radius: 14px;
}

.bookmarklet-eyebrow {
  margin: 0 0 4px;
  color: var(--vp-c-brand-1);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
}

.bookmarklet-card h2 {
  margin: 0 0 6px;
  border: 0;
  padding: 0;
}

.bookmarklet-card p {
  margin: 0;
}

.bookmarklet-button,
.bookmarklet-copy {
  display: inline-flex;
  grid-column: 2;
  align-items: center;
  justify-content: center;
  width: fit-content;
  min-height: 40px;
  padding: 0 16px;
  border-radius: 10px;
  font-weight: 700;
  text-decoration: none;
}

.bookmarklet-button {
  margin-top: 4px;
  color: #fff;
  background: #2563eb;
}

.bookmarklet-button::before {
  content: "";
  width: 18px;
  height: 18px;
  margin-right: 8px;
  background: url('/logo.svg') center / contain no-repeat;
  filter: drop-shadow(0 1px 1px rgba(0,0,0,.18));
}

.bookmarklet-copy {
  border: 1px solid var(--vp-c-divider);
  color: var(--vp-c-text-1);
  background: var(--vp-c-bg);
  cursor: pointer;
}

.bookmarklet-status {
  grid-column: 2;
  min-height: 20px;
  color: var(--vp-c-text-2);
  font-size: 13px;
}

@media (max-width: 640px) {
  .bookmarklet-card {
    grid-template-columns: 1fr;
  }

  .bookmarklet-button,
  .bookmarklet-copy,
  .bookmarklet-status {
    grid-column: 1;
  }
}
</style>
