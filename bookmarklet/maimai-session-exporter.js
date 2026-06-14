(() => {
  "use strict";

  const SUPPORTED_HOSTS = new Set(["maimaidx.jp", "maimaidx-eng.com"]);
  const DIFFICULTIES = ["basic", "advanced", "expert", "master", "remaster"];

  const state = { payload: null };

  const host = location.hostname;
  const isSupportedHost = SUPPORTED_HOSTS.has(host);
  const basePath = "/maimai-mobile";
  const baseUrl = `${location.origin}${basePath}`;
  const version = host === "maimaidx-eng.com" ? "intl" : "jp";
  const imageApiUrl = window.JIETNG_SESSION_IMAGE_API || "https://jietng-endpoint.matsuk1.com/api/web/session-image";

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
        <div id="jietng-bookmarklet-status">Ready</div>
      </main>
    `;
    panel.querySelector("header button").addEventListener("click", () => panel.remove());
    document.body.appendChild(panel);
  }

  function status(text) {
    const node = document.getElementById("jietng-bookmarklet-status");
    if (node) node.textContent = text;
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
    const blocks = doc.querySelectorAll("div.w_450");
    for (const block of blocks) {
      const name = textOf(block.querySelector(".music_name_block"));
      const score = textOf(block.querySelector(".music_score_block.w_112"));
      if (!name || !score) continue;

      const dxBlock = block.querySelector(".music_score_block.w_190");
      const dxScore = textOf(dxBlock).replace(/,/g, "") || "N/A";
      const type = musicType(block.querySelector("img.music_kind_icon")?.getAttribute("src") || "");
      const icons = Array.from(block.querySelectorAll("img.h_30")).map((img) => iconName(img.getAttribute("src") || ""));

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

  function downloadBlob(blob, payload, extension = "png") {
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filenameFor(payload, extension);
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      URL.revokeObjectURL(link.href);
      link.remove();
    }, 1000);
  }

  function showImagePreview(blob, payload) {
    const old = document.getElementById("jietng-bookmarklet-preview");
    if (old) old.remove();
    const panel = document.getElementById("jietng-bookmarklet-panel");
    if (panel) panel.remove();

    const url = URL.createObjectURL(blob);
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
        URL.revokeObjectURL(url);
        overlay.remove();
      }
    });

    const actionNode = overlay.querySelector("#jietng-bookmarklet-preview-actions");
    actionNode.appendChild(makeButton("Download", () => downloadBlob(blob, payload)));
    actionNode.appendChild(makeButton("Close", () => {
      URL.revokeObjectURL(url);
      overlay.remove();
    }));

    document.body.appendChild(overlay);
  }

  async function generateImage(payload) {
    status("Generating image...");
    const response = await fetch(imageApiUrl, {
      method: "POST",
      mode: "cors",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

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
    showImagePreview(blob, payload);
  }

  async function run() {
    createPanel();
    if (!isSupportedHost) {
      status("Wrong page");
      return;
    }

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
    status(`Generating image from ${best.length} records...`);

    state.payload = {
      schema: "jietng.maimai.session_image.v1",
      source: "maimai-session-bookmarklet",
      captured_at: new Date().toISOString(),
      origin: location.origin,
      version,
      cmd_type: "best50",
      profile,
      records: {
        best,
      },
    };

    await generateImage(state.payload);
  }

  run().catch((error) => {
    status(`Failed: ${error?.message || String(error)}`);
  });
})();
