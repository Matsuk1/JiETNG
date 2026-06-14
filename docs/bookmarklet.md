---
title: 网页书签工具
description: JiETNG maimai DX 网页书签工具，使用当前 maimai 官方网站登录状态生成 Best 50 成绩图。
---

# JiETNG 网页书签工具

这个书签工具会在 maimai DX 官方网站中运行，使用当前浏览器登录状态读取资料与 Best 记录，然后调用 JiETNG API 生成成绩图。它不会读取或要求输入 SEGA ID 密码。

<div class="bookmarklet-installer">
  <div class="bookmarklet-card">
    <img src="/logo.svg" alt="JiETNG" class="bookmarklet-logo">
    <div>
      <p class="bookmarklet-eyebrow">Bookmarklet</p>
      <h2>JiETNG 生成成绩图</h2>
      <p>把下面的按钮拖到浏览器书签栏。之后在 maimai 官方页面登录后点击它，就会在当前页面弹出成绩图。</p>
    </div>
    <a id="jietng-bookmarklet-link" class="bookmarklet-button" href="#">JiETNG 成绩图</a>
    <button id="jietng-copy-bookmarklet" class="bookmarklet-copy" type="button">复制书签地址</button>
    <p id="jietng-copy-status" class="bookmarklet-status"></p>
  </div>
</div>

## 使用方法

1. 把上面的 **JiETNG 成绩图** 按钮拖到浏览器书签栏。
2. 打开并登录日服或国际服 maimai DX 官方网站：
   - `https://maimaidx.jp/maimai-mobile/home/`
   - `https://maimaidx-eng.com/maimai-mobile/home/`
3. 在官方页面点击刚才保存的书签。
4. 等待生成完成，在页面弹窗中查看图片。

如果你的浏览器不方便拖拽按钮，可以点击 **复制书签地址**，然后手动新建书签，把 URL 设置为复制出来的 `javascript:...` 内容。

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
    status.textContent = '书签脚本加载失败，请稍后重试。'
    copyButton.disabled = true
  }

  copyButton.addEventListener('click', async () => {
    if (!bookmarklet) return
    try {
      await navigator.clipboard.writeText(bookmarklet)
      status.textContent = '已复制。现在可以手动新建书签并粘贴到 URL。'
    } catch (error) {
      status.textContent = '复制失败，请尝试拖拽按钮到书签栏。'
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
