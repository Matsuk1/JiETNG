---
title: Bookmarklet Tool
description: JiETNG maimai DX bookmarklet that uses the current maimai official website session to generate a Best 50 score image.
---

# JiETNG Bookmarklet Tool

This bookmarklet runs on the official maimai DX mobile website. It uses your current browser session to read your profile and Best records, then calls the JiETNG API to generate a score image. It never reads or asks for your SEGA ID password.

<div class="bookmarklet-installer">
  <div class="bookmarklet-card">
    <img src="/logo.svg" alt="JiETNG" class="bookmarklet-logo">
    <div>
      <p class="bookmarklet-eyebrow">Bookmarklet</p>
      <h2>JiETNG Score Image</h2>
      <p>Drag the button below to your bookmarks bar. After logging in on the official maimai site, click it to open the generated score image on the same page.</p>
    </div>
    <a id="jietng-bookmarklet-link" class="bookmarklet-button" href="#">JiETNG Score Image</a>
    <button id="jietng-copy-bookmarklet" class="bookmarklet-copy" type="button">Copy bookmark URL</button>
    <p id="jietng-copy-status" class="bookmarklet-status"></p>
  </div>
</div>

## How to Use

1. Drag the **JiETNG Score Image** button above to your bookmarks bar.
2. Open and log in to one of the official maimai DX sites:
   - `https://maimaidx.jp/maimai-mobile/home/`
   - `https://maimaidx-eng.com/maimai-mobile/home/`
3. Click the saved bookmark while staying on the official page.
4. Wait for generation to finish, then view the image in the page overlay.

If dragging is inconvenient in your browser, click **Copy bookmark URL**, create a bookmark manually, and paste the copied `javascript:...` content into the URL field.

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
    status.textContent = 'Failed to load the bookmarklet. Please try again later.'
    copyButton.disabled = true
  }

  copyButton.addEventListener('click', async () => {
    if (!bookmarklet) return
    try {
      await navigator.clipboard.writeText(bookmarklet)
      status.textContent = 'Copied. You can now create a bookmark manually and paste it as the URL.'
    } catch (error) {
      status.textContent = 'Copy failed. Try dragging the button to your bookmarks bar.'
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
