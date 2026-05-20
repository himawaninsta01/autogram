const NICHES = ["teknologi", "AI", "tips produktivitas", "desain", "bisnis online"];

export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("AutoGram Worker aktif ✅", { status: 200 });
    }

    let update;
    try {
      update = await request.json();
    } catch {
      return new Response("Bad request", { status: 400 });
    }

    // ── Callback Query (inline keyboard) ─────────────────────────────────────
    if (update.callback_query) {
      const cb     = update.callback_query;
      const cbChat = String(cb.message.chat.id);
      const data   = cb.data;

      if (cbChat !== String(env.TELEGRAM_CHAT_ID)) {
        return new Response("OK", { status: 200 });
      }

      await answerCallback(env.BOT_TOKEN, cb.id);

      if (data.startsWith("post:")) {
        const niche = data === "post:__auto__" ? null : data.replace("post:", "");
        const label = niche || "otomatis dari trend";
        await sendMessage(env.BOT_TOKEN, cbChat, `🚀 Pipeline dengan niche *${escapeMarkdown(label)}* dimulai\\. Tunggu notifikasi Telegram\\.`, "MarkdownV2");
        const ok = await triggerGitHubActions(env, { niche });
        if (!ok) await sendMessage(env.BOT_TOKEN, cbChat, "❌ Gagal trigger GitHub Actions. Cek GH_TOKEN.");
      }

      return new Response("OK", { status: 200 });
    }

    // ── Regular Message ───────────────────────────────────────────────────────
    const msg = update.message;
    if (!msg) return new Response("OK", { status: 200 });

    const chatId = String(msg.chat.id);
    const text   = (msg.text || "").trim();

    if (chatId !== String(env.TELEGRAM_CHAT_ID)) {
      await sendMessage(env.BOT_TOKEN, chatId, "⛔ Akses tidak diizinkan.");
      return new Response("OK", { status: 200 });
    }

    if (text === "/start" || text === "/help") {
      await sendMessage(env.BOT_TOKEN, chatId,
        "🤖 *AutoGram Bot* aktif\\!\n\n" +
        "Commands:\n" +
        "  /run — Pipeline otomatis \\(niche dari trend\\)\n" +
        "  /post — Pilih niche, lalu pipeline jalan\n" +
        "  /help — Tampilkan pesan ini",
        "MarkdownV2"
      );

    } else if (text === "/run") {
      await sendMessage(env.BOT_TOKEN, chatId, "🚀 Memulai pipeline... tunggu notifikasi Telegram.");
      const ok = await triggerGitHubActions(env, { niche: null });
      if (!ok) await sendMessage(env.BOT_TOKEN, chatId, "❌ Gagal trigger GitHub Actions. Cek GH_TOKEN.");

    } else if (text.startsWith("/post")) {
      const parts = text.split(" ");
      if (parts.length > 1) {
        const niche = parts.slice(1).join(" ");
        await sendMessage(env.BOT_TOKEN, chatId, `🚀 Pipeline dengan niche *${escapeMarkdown(niche)}* dimulai\\. Tunggu notifikasi Telegram\\.`, "MarkdownV2");
        const ok = await triggerGitHubActions(env, { niche });
        if (!ok) await sendMessage(env.BOT_TOKEN, chatId, "❌ Gagal trigger GitHub Actions. Cek GH_TOKEN.");
      } else {
        await sendInlineKeyboard(env.BOT_TOKEN, chatId);
      }

    } else {
      await sendMessage(env.BOT_TOKEN, chatId, "Ketik /help untuk daftar command.");
    }

    return new Response("OK", { status: 200 });
  }
};

// ── Helpers ───────────────────────────────────────────────────────────────────

async function triggerGitHubActions(env, { niche }) {
  const url = `https://api.github.com/repos/${env.GH_OWNER}/${env.GH_REPO}/dispatches`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${env.GH_TOKEN}`,
      "Accept": "application/vnd.github.v3+json",
      "Content-Type": "application/json",
      "User-Agent": "autogram-worker"
    },
    body: JSON.stringify({
      event_type: "manual_run",
      client_payload: { niche: niche || "" }
    })
  });
  return res.status === 204; // GitHub returns 204 on success
}

async function sendMessage(token, chatId, text, parseMode = null) {
  const body = { chat_id: chatId, text };
  if (parseMode) body.parse_mode = parseMode;
  await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
}

async function sendInlineKeyboard(token, chatId) {
  const keyboard = NICHES.map(n => ([{ text: n, callback_data: `post:${n}` }]));
  keyboard.push([{ text: "🎲 Biarkan AI pilih", callback_data: "post:__auto__" }]);
  await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text: "📌 Pilih niche untuk post:",
      reply_markup: { inline_keyboard: keyboard }
    })
  });
}

async function answerCallback(token, callbackQueryId) {
  await fetch(`https://api.telegram.org/bot${token}/answerCallbackQuery`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ callback_query_id: callbackQueryId })
  });
}

function escapeMarkdown(text) {
  return text.replace(/[_*[\]()~`>#+\-=|{}.!]/g, "\\$&");
}