(() => {
  "use strict";

  const SUPPORTED_HOSTS = new Set(["maimaidx.jp", "maimaidx-eng.com"]);
  const DIFFICULTIES = ["basic", "advanced", "expert", "master", "remaster"];
  const RECORD_TYPES = [
    ["best50", "B50"],
    ["best40", "B40"],
    ["best35", "B35"],
    ["best15", "B15"],
    ["allb35", "AB35"],
    ["allb50", "AB50"],
    ["apb50", "AP50"],
    ["fdxb50", "FDX50"],
    ["idlb50", "IDLB50"],
  ];

  const state = {
    payload: null,
    profile: null,
    best: null,
    collectPromise: null,
  };

  const host = location.hostname;
  const isSupportedHost = SUPPORTED_HOSTS.has(host);
  const basePath = "/maimai-mobile";
  const baseUrl = `${location.origin}${basePath}`;
  const version = host === "maimaidx-eng.com" ? "intl" : "jp";
  const imageApiUrl = window.JIETNG_SESSION_IMAGE_API || "https://jietng-endpoint.matsuk1.com/api/web/session-image";
  const cacheKey = `jietng:maimai-session:${version}:best-records:v1`;
  const uiCacheKey = `jietng:maimai-session:${version}:ui:v1`;
  const previewCacheKey = `jietng:maimai-session:${version}:preview:v1`;

  function createPanel() {
    const old = document.getElementById("jietng-bookmarklet-panel");
    if (old) old.remove();

    const style = document.createElement("style");
    style.id = "jietng-bookmarklet-style";
    style.textContent = `
      #jietng-bookmarklet-panel {
        position: fixed;
        z-index: 2147483647;
        right: 16px;
        bottom: 16px;
        width: min(320px, calc(100vw - 32px));
        color: #111827;
        background: rgba(255,255,255,.96);
        border: 1px solid rgba(17,24,39,.12);
        border-radius: 12px;
        box-shadow: 0 18px 50px rgba(17,24,39,.22);
        font: 13px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        overflow: hidden;
        backdrop-filter: blur(10px);
      }
      #jietng-bookmarklet-panel * { box-sizing: border-box; }
      #jietng-bookmarklet-panel header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        padding: 9px 12px;
        background: linear-gradient(135deg, #111827, #273449);
        color: #ffffff;
        font-weight: 700;
      }
      #jietng-bookmarklet-panel button {
        border: 1px solid rgba(17,24,39,.14);
        border-radius: 8px;
        background: #ffffff;
        color: #111827;
        cursor: pointer;
        font: inherit;
        padding: 7px 10px;
      }
      #jietng-bookmarklet-panel header button {
        width: 28px;
        height: 28px;
        padding: 0;
        border-color: rgba(255,255,255,.25);
        background: rgba(255,255,255,.12);
        color: #fff;
        border-radius: 999px;
        font-size: 18px;
        line-height: 1;
      }
      #jietng-bookmarklet-panel main { padding: 12px; }
      #jietng-bookmarklet-controls {
        display: grid;
        gap: 9px;
        margin-bottom: 10px;
      }
      #jietng-bookmarklet-controls label {
        display: grid;
        gap: 4px;
        color: #4b5563;
        font-size: 12px;
        font-weight: 650;
      }
      #jietng-bookmarklet-controls select,
      #jietng-bookmarklet-controls input {
        width: 100%;
        min-height: 34px;
        border: 1px solid rgba(17,24,39,.16);
        border-radius: 8px;
        background: #ffffff;
        color: #111827;
        font: 13px/1.3 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        padding: 6px 8px;
        outline: none;
      }
      #jietng-bookmarklet-controls select:focus,
      #jietng-bookmarklet-controls input:focus {
        border-color: #2563eb;
        box-shadow: 0 0 0 3px rgba(37,99,235,.14);
      }
      #jietng-bookmarklet-generate {
        min-height: 36px;
        background: #111827;
        border-color: #111827;
        color: #ffffff;
        font-weight: 750;
      }
      #jietng-bookmarklet-generate:disabled,
      #jietng-bookmarklet-controls select:disabled,
      #jietng-bookmarklet-controls input:disabled {
        cursor: not-allowed;
        opacity: .58;
      }
      #jietng-bookmarklet-status {
        color: #374151;
        font-weight: 650;
      }
      #jietng-bookmarklet-preview {
        position: fixed;
        z-index: 2147483646;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 24px;
        background: rgba(15,23,42,.68);
        backdrop-filter: blur(6px);
      }
      #jietng-bookmarklet-preview .preview-card {
        width: min(1040px, 100%);
        max-height: min(92vh, 1200px);
        display: flex;
        flex-direction: column;
        overflow: hidden;
        background: #ffffff;
        border: 1px solid rgba(255,255,255,.55);
        border-radius: 14px;
        box-shadow: 0 24px 80px rgba(0,0,0,.38);
      }
      #jietng-bookmarklet-preview .preview-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        padding: 11px 12px 11px 16px;
        border-bottom: 1px solid #e5e7eb;
        font-weight: 700;
        color: #111827;
        background: #ffffff;
      }
      #jietng-bookmarklet-preview .preview-body {
        overflow: auto;
        background: #eef1f5;
        padding: 14px;
      }
      #jietng-bookmarklet-preview img {
        display: block;
        width: 100%;
        height: auto;
        margin: 0 auto;
        background: #fff;
        border-radius: 8px;
        box-shadow: 0 1px 4px rgba(15,23,42,.12);
      }
      #jietng-bookmarklet-preview-actions {
        display: flex;
        gap: 8px;
        flex-shrink: 0;
      }
      #jietng-bookmarklet-preview-actions button {
        min-width: 76px;
        border: 1px solid rgba(17,24,39,.14);
        border-radius: 8px;
        background: #ffffff;
        color: #111827;
        cursor: pointer;
        font: 13px/1.2 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        padding: 8px 11px;
      }
      #jietng-bookmarklet-preview-actions button:first-child {
        background: #2563eb;
        border-color: #1d4ed8;
        color: #ffffff;
      }
    `;
    document.head.appendChild(style);

    const panel = document.createElement("section");
    panel.id = "jietng-bookmarklet-panel";
    panel.innerHTML = `
      <header>
        <span>JiETNG Image Generator</span>
        <button type="button" title="Close" aria-label="Close">×</button>
      </header>
      <main>
        <div id="jietng-bookmarklet-controls">
          <label>
            Type
            <select id="jietng-bookmarklet-type">
              ${RECORD_TYPES.map(([value, label]) => `<option value="${value}">${label}</option>`).join("")}
            </select>
          </label>
          <label>
            Command
            <input id="jietng-bookmarklet-command" type="text" inputmode="text" autocomplete="off" placeholder="-lv 13 -diff mas -page 2">
          </label>
          <button id="jietng-bookmarklet-generate" type="button">Generate</button>
        </div>
        <div id="jietng-bookmarklet-status">Ready</div>
      </main>
    `;
    panel.querySelector("header button").addEventListener("click", () => panel.remove());
    document.body.appendChild(panel);
    restoreUiState();
    document.getElementById("jietng-bookmarklet-type")?.addEventListener("change", saveUiState);
    document.getElementById("jietng-bookmarklet-command")?.addEventListener("input", saveUiState);
  }

  function status(text) {
    const node = document.getElementById("jietng-bookmarklet-status");
    if (node) node.textContent = text;
  }

  function currentOptions() {
    return {
      cmdType: document.getElementById("jietng-bookmarklet-type")?.value || "best50",
      command: document.getElementById("jietng-bookmarklet-command")?.value?.trim() || "",
    };
  }

  function setControlsDisabled(disabled) {
    for (const id of ["jietng-bookmarklet-type", "jietng-bookmarklet-command", "jietng-bookmarklet-generate"]) {
      const node = document.getElementById(id);
      if (node) node.disabled = disabled;
    }
  }

  function restoreUiState() {
    try {
      const cached = JSON.parse(sessionStorage.getItem(uiCacheKey) || "null");
      if (!cached) return;
      const typeNode = document.getElementById("jietng-bookmarklet-type");
      const commandNode = document.getElementById("jietng-bookmarklet-command");
      if (typeNode && RECORD_TYPES.some(([value]) => value === cached.cmdType)) typeNode.value = cached.cmdType;
      if (commandNode && typeof cached.command === "string") commandNode.value = cached.command;
    } catch (_) {
      sessionStorage.removeItem(uiCacheKey);
    }
  }

  function saveUiState() {
    try {
      sessionStorage.setItem(uiCacheKey, JSON.stringify(currentOptions()));
    } catch (_) {
      // Ignore storage quota/private mode failures.
    }
  }

  function loadCachedSessionData() {
    try {
      const cached = JSON.parse(sessionStorage.getItem(cacheKey) || "null");
      if (cached?.profile && Array.isArray(cached?.best) && cached.best.length) {
        state.profile = cached.profile;
        state.best = cached.best;
        return {
          profile: cached.profile,
          best: cached.best,
        };
      }
    } catch (_) {
      sessionStorage.removeItem(cacheKey);
    }
    return null;
  }

  function saveCachedSessionData(profile, best) {
    try {
      sessionStorage.setItem(cacheKey, JSON.stringify({
        captured_at: new Date().toISOString(),
        profile,
        best,
      }));
    } catch (_) {
      // Ignore storage quota/private mode failures; in-memory cache still works.
    }
  }

  function makeButton(label, onClick, primary = false) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    if (primary) button.className = "primary";
    button.addEventListener("click", onClick);
    return button;
  }

  function textOf(node) {
    return (node?.textContent || "").replace(/\u00a0/g, " ").replace(/\s+/g, " ").trim();
  }

  function allText(node) {
    if (!node) return [];
    return Array.from(node.childNodes)
      .flatMap((child) => {
        if (child.nodeType === Node.TEXT_NODE) {
          return [child.textContent.replace(/\u00a0/g, " ").replace(/\s+/g, " ").trim()];
        }
        if (child.nodeType === Node.ELEMENT_NODE) return allText(child);
        return [];
      })
      .filter(Boolean);
  }

  function xpathNodes(context, expression) {
    const doc = context.ownerDocument || context;
    const result = doc.evaluate(expression, context, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
    return Array.from({ length: result.snapshotLength }, (_, index) => result.snapshotItem(index));
  }

  function xpathText(context, expression) {
    return xpathNodes(context, expression)
      .map((node) => (node.textContent || "").trim())
      .filter(Boolean);
  }

  function iconName(src) {
    if (!src) return "";
    return src
      .split("/")
      .pop()
      .split("?")[0]
      .replace(/\.png$/i, "")
      .replace(/^music_icon_/, "");
  }

  function musicType(src) {
    if (!src) return "N/A";
    if (src.includes("standard.png")) return "std";
    if (src.includes("dx.png")) return "dx";
    return "utage";
  }

  function parseTrophy(...docs) {
    const typeMap = {
      "ランダム": "rainbow",
      "虹": "rainbow",
      "金": "gold",
      "銀": "silver",
      "銅": "bronze",
      "通常": "normal",
    };
    const ignoredText = new Set([
      "ランダム", "虹", "金", "銀", "銅", "通常",
      "rainbow", "gold", "silver", "bronze", "normal",
      "設定中", "変更", "決定", "所持", "未所持", "獲得条件", "new",
    ]);

    for (const doc of docs.filter(Boolean)) {
      const trophyBlock = doc.querySelector(".trophy_block");
      const innerBlock = trophyBlock?.querySelector(".trophy_inner_block") || doc.querySelector(".trophy_inner_block.f_13");
      if (!trophyBlock && !innerBlock) continue;

      const blockClass = trophyBlock?.className || "";
      const classType = blockClass
        .split(/\s+/)
        .find((className) => className.startsWith("trophy_") && className !== "trophy_block")
        ?.replace("trophy_", "")
        .toLowerCase();
      const imageSrc = Array.from((trophyBlock || doc).querySelectorAll('img[src*="trophy_"]'))
        .map((img) => img.src)
        .find((src) => /trophy_[a-z_]+\.png/i.test(src));
      const imageType = imageSrc?.match(/trophy_([a-z_]+)\.png/i)?.[1]?.toLowerCase();
      const textTypeRaw = textOf((trophyBlock || doc).querySelector(".block_info.f_11.orange")).toLowerCase();
      const textType = typeMap[textTypeRaw] || textTypeRaw;
      const type = [classType, imageType, textType, "rainbow"].find(Boolean);

      const textCandidates = allText(innerBlock)
        .map((value) => value.trim())
        .filter((value) => value && !ignoredText.has(value.toLowerCase()) && !ignoredText.has(value));
      const content = textCandidates[1] || textCandidates[0] || "N/A";

      return {
        url: imageSrc || `${baseUrl}/img/trophy_${type}.png`,
        content,
      };
    }

    return {
      url: `${baseUrl}/img/trophy_rainbow.png`,
      content: "N/A",
    };
  }

  function parseHtml(html) {
    return new DOMParser().parseFromString(html, "text/html");
  }

  async function fetchPage(path) {
    const url = path.startsWith("http") ? path : `${baseUrl}${path}`;
    const response = await fetch(url, {
      credentials: "include",
      cache: "no-store",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
    });

    if (response.status === 503) {
      throw new Error("maimai server is under maintenance (503)");
    }
    if (!response.ok) {
      throw new Error(`fetch failed: ${response.status} ${url}`);
    }

    const html = await response.text();
    if (html.includes("再度ログインしてください") || html.includes("Please agree to the following terms of service before log in.")) {
      throw new Error("session is not logged in or needs terms agreement");
    }
    return parseHtml(html);
  }

  function parseProfile(playerDoc, collectionDoc, nameplateDoc, trophyDoc, currentDoc) {
    const rating = textOf(playerDoc.querySelector(".rating_block")) || "0";
    const trophy = parseTrophy(currentDoc, playerDoc, trophyDoc);

    return {
      name: textOf(playerDoc.querySelector(".name_block")) || "NAME_ERROR",
      rating,
      cource_rank_url: playerDoc.querySelector("img.h_35.f_l")?.src || "N/A",
      class_rank_url: playerDoc.querySelector("img.w_160.p_15.m_r_10")?.src || "N/A",
      icon_url: collectionDoc.querySelector("img.w_80.m_r_10.f_l")?.src || "N/A",
      nameplate_url: nameplateDoc.querySelector("img.w_396.m_r_10")?.src || "N/A",
      trophy_url: trophy.url,
      trophy_content: trophy.content,
    };
  }

  function parseBestRecords(doc, difficulty) {
    const records = [];
    const blocks = xpathNodes(doc, '//div[contains(@class, "w_450")]');
    for (const block of blocks) {
      const name = xpathText(block, './/div[contains(@class, "music_name_block")]/text()')[0] || "";
      const score = xpathText(block, './/div[contains(@class, "music_score_block") and contains(@class, "w_112")]/text()')[0] || "";
      if (!name || !score) continue;

      const dxImg = xpathNodes(block, './/div[contains(@class, "music_score_block") and contains(@class, "w_190")]/img')[0];
      const dxScore = (dxImg?.nextSibling?.textContent || "N/A").trim().replace(/,/g, "") || "N/A";
      const typeIcon = xpathNodes(block, './/img[contains(@class, "music_kind_icon")]')[0]?.getAttribute("src") || "";
      const type = musicType(typeIcon);
      const icons = xpathNodes(block, './/img[contains(@class, "h_30")]').map((img) => iconName(img.getAttribute("src") || ""));

      records.push({
        name,
        difficulty,
        type,
        score,
        dx_score: dxScore,
        score_icon: icons[2] || "",
        combo_icon: icons[1] || "",
        sync_icon: icons[0] || "",
      });
    }
    return records;
  }

  function safeFilenamePart(value) {
    return String(value || "maimai").replace(/[\\/:*?"<>|\s]+/g, "_").slice(0, 40);
  }

  function filenameFor(payload, extension = "png") {
    const safeName = safeFilenamePart(payload.profile?.name);
    const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
    return `jietng_maimai_${payload.version}_${safeName}_${stamp}.${extension}`;
  }

  function downloadImage(source, payload, extension = "png") {
    const link = document.createElement("a");
    const shouldRevoke = source instanceof Blob;
    link.href = shouldRevoke ? URL.createObjectURL(source) : source;
    link.download = filenameFor(payload, extension);
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      if (shouldRevoke) URL.revokeObjectURL(link.href);
      link.remove();
    }, 1000);
  }

  function showImagePreview(source, payload) {
    const old = document.getElementById("jietng-bookmarklet-preview");
    if (old) old.remove();

    const shouldRevoke = source instanceof Blob;
    const url = shouldRevoke ? URL.createObjectURL(source) : source;
    const overlay = document.createElement("section");
    overlay.id = "jietng-bookmarklet-preview";
    overlay.innerHTML = `
      <div class="preview-card" role="dialog" aria-label="JiETNG generated score image">
        <div class="preview-head">
          <span>JiETNG Score Image</span>
          <div id="jietng-bookmarklet-preview-actions"></div>
        </div>
        <div class="preview-body">
          <img alt="Generated maimai score image">
        </div>
      </div>
    `;
    overlay.querySelector("img").src = url;
    overlay.addEventListener("click", (event) => {
      if (event.target === overlay) {
        if (shouldRevoke) URL.revokeObjectURL(url);
        overlay.remove();
      }
    });

    const actionNode = overlay.querySelector("#jietng-bookmarklet-preview-actions");
    actionNode.appendChild(makeButton("Download", () => downloadImage(source, payload)));
    actionNode.appendChild(makeButton("Close", () => {
      if (shouldRevoke) URL.revokeObjectURL(url);
      overlay.remove();
    }));

    document.body.appendChild(overlay);
  }

  function blobToDataUrl(blob) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.addEventListener("load", () => resolve(reader.result));
      reader.addEventListener("error", () => reject(reader.error));
      reader.readAsDataURL(blob);
    });
  }

  async function saveCachedPreview(blob, payload) {
    try {
      sessionStorage.setItem(previewCacheKey, JSON.stringify({
        captured_at: new Date().toISOString(),
        payload,
        image_data_url: await blobToDataUrl(blob),
      }));
    } catch (_) {
      // Ignore storage quota/private mode failures; the current overlay still works.
    }
  }

  function restoreCachedPreview() {
    try {
      const cached = JSON.parse(sessionStorage.getItem(previewCacheKey) || "null");
      if (!cached?.image_data_url || !cached?.payload) return;
      showImagePreview(cached.image_data_url, cached.payload);
      status("Restored previous image. Generate again to update it.");
    } catch (_) {
      sessionStorage.removeItem(previewCacheKey);
    }
  }

  async function generateImage(payload) {
    status("Generating image...");
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);
    let response;
    try {
      response = await fetch(imageApiUrl, {
        method: "POST",
        mode: "cors",
        signal: controller.signal,
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
    } catch (error) {
      if (error?.name === "AbortError") {
        throw new Error("Image generation timed out. Please refresh the page and try again.");
      }
      throw error;
    } finally {
      clearTimeout(timeoutId);
    }

    if (!response.ok) {
      let message = `image api failed: ${response.status}`;
      try {
        const errorBody = await response.json();
        if (errorBody?.error) message = `${message} ${errorBody.error}`;
      } catch (_) {
        message = `${message} ${await response.text()}`;
      }
      throw new Error(message);
    }

    const blob = await response.blob();
    await saveCachedPreview(blob, payload);
    showImagePreview(blob, payload);
  }

  async function collectSessionData() {
    if (state.profile && state.best) {
      status(`Using cached ${state.best.length} records...`);
      return {
        profile: state.profile,
        best: state.best,
      };
    }
    const cached = loadCachedSessionData();
    if (cached) {
      status(`Using cached ${cached.best.length} records...`);
      return cached;
    }
    if (state.collectPromise) {
      return state.collectPromise;
    }

    state.collectPromise = (async () => {
      status("Collecting profile...");

      const [playerDoc, collectionDoc, nameplateDoc, trophyDoc] = await Promise.all([
        fetchPage("/playerData/"),
        fetchPage("/collection/"),
        fetchPage("/collection/nameplate/"),
        fetchPage("/collection/trophy/"),
      ]);
      const profile = parseProfile(playerDoc, collectionDoc, nameplateDoc, trophyDoc, document);

      status("Collecting best records...");
      const bestDocs = await Promise.all(
        DIFFICULTIES.map((_, index) => fetchPage(`/record/musicGenre/search/?genre=99&diff=${index}`))
      );
      const best = bestDocs.flatMap((doc, index) => parseBestRecords(doc, DIFFICULTIES[index]));

      state.profile = profile;
      state.best = best;
      saveCachedSessionData(profile, best);
      return { profile, best };
    })();

    try {
      return await state.collectPromise;
    } catch (error) {
      state.collectPromise = null;
      throw error;
    }
  }

  async function generateFromPage() {
    const options = currentOptions();
    saveUiState();
    setControlsDisabled(true);
    const { profile, best } = await collectSessionData();
    status(`Generating image from ${best.length} records...`);

    state.payload = {
      schema: "jietng.maimai.session_image.v1",
      source: "maimai-session-bookmarklet",
      captured_at: new Date().toISOString(),
      origin: location.origin,
      version,
      cmd_type: options.cmdType,
      command: options.command,
      profile,
      records: {
        best,
      },
    };

    await generateImage(state.payload);
  }

  function run() {
    createPanel();
    if (!isSupportedHost) {
      status("Wrong page");
      setControlsDisabled(true);
      return;
    }

    document.getElementById("jietng-bookmarklet-generate")?.addEventListener("click", () => {
      generateFromPage()
        .catch((error) => {
          status(`Failed: ${error?.message || String(error)}`);
        })
        .finally(() => {
          setControlsDisabled(false);
        });
    });
    restoreCachedPreview();
  }

  run();
})();
