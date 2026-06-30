# NEBANK — Requirements traceability (from TZ)

Re-verified each iteration per TZ §18. Status: `done` / `partial` / `pending`.

| # | TZ § | Requirement | Status | Where |
|---|------|-------------|--------|-------|
| R1 | 1–2 | Telegram product = bot (fast layer) + Mini App (the home). Both first-class. | done | `backend/app/bot`, `miniapp` |
| R2 | 3 | RU + EN everywhere; bot command menu localizes on language switch; auto-detect at start + visible switch | done | `backend/app/locales`, `bot/i18n.py`, `miniapp/src/i18n` |
| R3 | 3 | Language switch styled like the budget switch (segmented, shows options + current) | done | `bot` segmented kb, `miniapp Segmented` |
| R4 | 4 | Onboarding: auto language, RU/EN button, base currency (all fiats, default USD), single clean guide msg, never leaves lang/currency unset | done | `bot/handlers/onboarding.py` |
| R5 | 5 | Entry: text, voice (RU/EN), photo (receipt/QR/screenshot), forwarded bank SMS, crypto tx link | done | `bot/handlers/capture.py`, `services/parser`, `services/ocr.py`, `services/voice.py` |
| R6 | 5 | Multi-entry: "кофе 200, такси 350, кино 500" → one message, several categories/sums | done | `services/parser/expense_parser.py` |
| R7 | 5 | Per-line category selectable; words-to-number & fractions ("ноль точка ноль ноль ноль шесть биткоинов"→0.0006 BTC); dates in all RU/EN formats, day/month never swapped; keep item/place name | done | `services/parser` |
| R8 | 5 | Any fiat/crypto converted to base by the rate on the purchase day | done | `services/rates.py` (historical) |
| R9 | 5 | After-record reaction: short confirm, "Open" (Mini App) button, Cancel-before-commit, then change category / delete | done | `bot/handlers/capture.py`, `bot/keyboards.py` |
| R10 | 6 | Categories: never auto-create empty defaults; create on new input; per-tx category change & management (add/rename/delete); tidy single-column premium layout | done | `services/categories.py`, `miniapp` Settings/Categories |
| R11 | 7 | Crypto: exactly BTC, ETH, USDT, TRX; networks bitcoin/erc20/trc20; tx link → crypto expense; USDT asks amount; input hints | done | `services/crypto.py`, `bot/handlers/capture.py` |
| R12 | 8 | Bank SMS: forward → auto record; dedup so the same SMS never doubles | done | `services/parser/sms_parser.py`, dedup hash |
| R13 | 9 | Voice RU/EN with recognition-language choice; real quality | partial (real via Whisper if key/binary present; graceful guidance otherwise) | `services/voice.py` |
| R14 | 10 | OCR: printed receipts, screenshots, QR, documents; multi-entry from one photo; handwriting best-effort; always reacts meaningfully | done (vision-LLM path for high quality when `LLM_API_KEY` set; Tesseract+QR keyless fallback) | `services/vision.py`, `services/ocr.py` |
| R15 | 11 | Chat reports: now/week/month image w/ chart + numbers (chart in ALL reports); balance debit/credit/net; history by day; share-by-link; Excel export; quick lang/currency; subscriptions & categories partly in chat | done | `services/reports.py`, `bot/handlers/reports.py`, `services/export.py` |
| R16 | 12.1 | Dashboard: balance/income/expense per period; signature donut with drill-into-category on tap; trend graph; recent ops; pleasant colors | done | `miniapp/src/pages/Dashboard.tsx`, `DonutChart` |
| R17 | 12.2 | History: full ops, filters + search, edit/delete; data never disappears; consistent across chat+dashboard | done | `miniapp History`, shared DB |
| R18 | 12.3 | Habits = "отказ от вредных платежей" (not daily-habit); saved & days-clean (whole days); share card | done | `miniapp Habits`, `services/habits.py` |
| R19 | 12.4 | Subscriptions: manage + calendar; auto-detect recurring from txs & offer reminder; remind 3d & 1d; ask regular/one-off when category=Subscriptions | done | `services/subscriptions.py`, `services/scheduler.py`, `miniapp Subscriptions` |
| R20 | 12.5 | Per-category budgets: limit, progress bar, status color, overspend indicator; set/edit by tap in web | done | `miniapp Budgets`, `services/budgets.py` |
| R21 | 12.6 | Insights: this month vs last + forecast to month end | done | `services/insights.py`, `miniapp Insights` |
| R22 | 12.7 | Rates & calculator: exchange-style green/red moving history, REAL data (crypto + fiat); converter (fiat+crypto). No fake values. | done | `services/rates.py` (CoinGecko + Frankfurter), `miniapp Rates` |
| R23 | 12.8 | 12 progressive achievements on real data; gold medallions, progress ring, tap→sheet; computed live, best result stored | done | `services/achievements.py`, `miniapp Achievements` |
| R24 | 12.9 | Savings goals: goal + progress bar; top-up; mark achieved | done | `services/goals.py`, `miniapp Goals` |
| R25 | 12.10 | Round-up stash: round expenses into virtual stash | done | `services/stash.py`, `miniapp Stash` |
| R26 | 12.11 | Shared/family budget = built-in referral (invite to co-manage); never auto-create; don't apply default name mid-flow | done | `services/family.py`, `miniapp Family` |
| R27 | 12.12 | Deep settings: language, base currency, theme, etc. | done | `miniapp Settings` |
| R28 | 13 | Achievements list (streaks 7/30, 100/500 ops, category variety, subscriptions, 30/100 clean days, goal reached, income, month-in-budget) | done | `services/achievements.py` (12 defined) |
| R29 | 14 | Monetization via Telegram Stars; Premium ≈ 250 Stars/month; free vs premium gating per table | done | `services/payments.py`, `bot/handlers/premium.py` |
| R30 | 15 | Privacy: no real-bank link; manual + semi-auto; trust narrative incl. optional Google-Sheet export of user's own data | partial (CSV/Excel export done; Google Sheets export documented as optional) | `services/export.py`, docs |
| R31 | 16 | Out of scope honored (no bank sync, no investing/net-worth, no scoring) | done | not implemented (by design) |
| R32 | 17 | Design: strictly light always; premium iOS "Liquid Glass"; NO emoji anywhere; no "schoolish"/cheap; no cramped rows; nothing that reveals AI; brand NEBANK (full word); avatar = "NEBANK" one line on light | done | `miniapp/src/design`, brand assets |
| R33 | 18 | Real data only (esp. rates); load-ready server; test before delivery; track requirements; deliver one zip + clean copy-paste install/restart; finish before install | done | this file, `deploy/`, `scripts/package.sh` |
| R34 | 19 | Infra: bot @nebanknebot; VPS Ubuntu London 4GB; IP 104.194.143.122; Mini App at https://104-194-143-122.sslip.io (HTTPS Let's Encrypt) | done | `deploy/install.sh`, `.env.example` |

## Notes on "real" AI features (honesty per §18, §33)
- **Exchange/crypto rates**: fully real, keyless — CoinGecko (crypto) + Frankfurter/exchangerate.host (fiat), with historical (purchase-day) rates and on-disk caching. No invented values anywhere.
- **Expense NLP parser**: deterministic, multilingual (RU/EN), covers multi-entry, words-to-numbers, fractions, all date formats, crypto units — works with zero API keys. An optional LLM pass (if `LLM_API_KEY` set) only *augments* edge cases; it never fabricates amounts.
- **OCR**: Tesseract (printed text, RU+EN) + ZBar (QR) are real and keyless. Handwriting/low-quality is best-effort; if an optional vision LLM key is set, it improves results. The bot always responds meaningfully, never silent.
- **Voice**: real transcription via local `whisper.cpp`/`faster-whisper` if model present, or OpenAI/Groq Whisper if a key is set. Without either, the bot clearly tells the user to install the model — it never returns nonsense.

These three are the only places needing optional external compute. Everything else is fully functional with no third-party keys beyond the Telegram bot token.
