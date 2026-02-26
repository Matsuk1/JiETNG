---
layout: page
---

<script setup>
import { ref } from 'vue'

const segaid = ref('')
const password = ref('')
const ver = ref('jp')
const loading = ref(false)
const error = ref('')
const imageUrl = ref('')

async function generate() {
  if (!segaid.value || !password.value) return
  error.value = ''
  if (imageUrl.value) { URL.revokeObjectURL(imageUrl.value); imageUrl.value = '' }
  loading.value = true
  try {
    const fd = new FormData()
    fd.append('segaid', segaid.value)
    fd.append('password', password.value)
    fd.append('ver', ver.value)
    const res = await fetch('/linebot/demo', { method: 'POST', body: fd })
    if (res.ok) {
      const blob = await res.blob()
      imageUrl.value = URL.createObjectURL(blob)
    } else {
      const data = await res.json().catch(() => ({}))
      error.value = data.error || 'Generation failed. Please try again.'
    }
  } catch {
    error.value = 'Network error. Please check your connection and try again.'
  } finally {
    loading.value = false
  }
}

function reset() {
  if (imageUrl.value) { URL.revokeObjectURL(imageUrl.value); imageUrl.value = '' }
  error.value = ''
}
</script>

<div class="demo-page">
  <div class="demo-hero">
    <h1>Try It Online</h1>
    <p>No LINE required — just enter your SEGA account to generate your Best 50 score card.</p>
  </div>

  <div class="demo-card" v-if="!imageUrl">
    <form @submit.prevent="generate">
      <div class="field">
        <label for="segaid">SEGA ID</label>
        <input id="segaid" v-model="segaid" type="text" placeholder="Your SEGA ID" autocomplete="username" required :disabled="loading" />
      </div>
      <div class="field">
        <label for="password">Password</label>
        <input id="password" v-model="password" type="password" placeholder="Your SEGA password" autocomplete="current-password" required :disabled="loading" />
      </div>
      <div class="field">
        <label for="ver">Server</label>
        <select id="ver" v-model="ver" :disabled="loading">
          <option value="jp">Japan — maimaidx.jp</option>
          <option value="intl">International — maimaidx-eng.com</option>
        </select>
      </div>
      <button type="submit" :disabled="loading" class="btn-primary">
        <span v-if="loading" class="spinner"></span>
        <span>{{ loading ? 'Generating, please wait…' : 'Generate Best 50' }}</span>
      </button>
      <p v-if="error" class="error-msg">{{ error }}</p>
    </form>
    <p class="notice">Your credentials are used only for this request and are never stored. This is an unofficial service with no affiliation to SEGA.</p>
  </div>

  <div class="demo-card result-card" v-if="imageUrl">
    <img :src="imageUrl" alt="Best 50 score card" class="result-img" />
    <div class="result-actions">
      <a :href="imageUrl" download="best50.png" class="btn-primary">Save image</a>
      <button @click="reset" class="btn-secondary">Try again</button>
    </div>
  </div>
</div>

<style>
.demo-page {
  max-width: 520px;
  margin: 0 auto;
  padding: 48px 24px 80px;
}

.demo-hero {
  text-align: center;
  margin-bottom: 32px;
}

.demo-hero h1 {
  font-size: 2rem;
  font-weight: 700;
  color: var(--vp-c-text-1);
  margin-bottom: 8px;
}

.demo-hero p {
  font-size: 1rem;
  color: var(--vp-c-text-2);
}

.demo-card {
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  padding: 32px;
}

.field {
  margin-bottom: 20px;
}

.field label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--vp-c-text-1);
  margin-bottom: 8px;
}

.field input,
.field select {
  width: 100%;
  padding: 10px 14px;
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  font-size: 15px;
  color: var(--vp-c-text-1);
  font-family: inherit;
  box-sizing: border-box;
  transition: border-color 0.2s;
}

.field input:focus,
.field select:focus {
  outline: none;
  border-color: var(--vp-c-brand-1);
}

.field input:disabled,
.field select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px;
  background: var(--vp-c-brand-1);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: opacity 0.2s;
  text-decoration: none;
  margin-top: 4px;
  box-sizing: border-box;
  text-align: center;
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.85;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  flex: 1;
  padding: 11px;
  background: transparent;
  color: var(--vp-c-text-2);
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
}

.btn-secondary:hover {
  border-color: var(--vp-c-brand-1);
  color: var(--vp-c-brand-1);
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-msg {
  margin-top: 12px;
  font-size: 14px;
  color: var(--vp-c-danger-1, #f43f5e);
  line-height: 1.5;
}

.notice {
  margin-top: 20px;
  font-size: 12px;
  color: var(--vp-c-text-3);
  line-height: 1.6;
  text-align: center;
}

.result-card {
  text-align: center;
}

.result-img {
  width: 100%;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  margin-bottom: 16px;
}

.result-actions {
  display: flex;
  gap: 12px;
}

.result-actions .btn-primary {
  flex: 1;
  margin-top: 0;
}
</style>
