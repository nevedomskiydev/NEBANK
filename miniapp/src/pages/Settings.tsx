import { useState } from "react";
import type { Nav } from "../App";
import { api } from "../lib/api";
import { useStore } from "../lib/store";
import { t, setLang } from "../i18n";
import { Header, Segmented } from "../components/ui";
import { IChevron, IGrid, IPremium, IUsers, IPiggy } from "../components/icons";
import { openInvoice, shareLink, notify } from "../lib/telegram";

export function Settings({ nav }: { nav: Nav }) {
  const { me, update, refresh } = useStore();
  const [busy, setBusy] = useState(false);

  async function buyPremium() {
    setBusy(true);
    try {
      const { invoice_link } = await api.post<{ invoice_link: string }>("/premium/invoice");
      const status = await openInvoice(invoice_link);
      if (status === "paid") { notify("success"); setTimeout(refresh, 1500); }
    } catch { notify("error"); } finally { setBusy(false); }
  }

  async function exportXlsx() {
    if (!me!.is_premium) { buyPremium(); return; }
    // open via fetch -> blob (auth header required)
    const res = await fetch("/api/export.xlsx", { headers: { "X-Init-Data": (window as any).Telegram?.WebApp?.initData ?? "" } });
    if (!res.ok) { notify("error"); return; }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "nebank-export.xlsx"; a.click();
    URL.revokeObjectURL(url);
  }

  const fiat = me!.currencies.fiat;

  return (
    <div className="stack">
      <Header title={t("settings")} onBack={() => nav("more")} />

      {!me!.is_premium ? (
        <button className="card" style={{ background: "linear-gradient(135deg,#1f2330,#14161f)", color: "#fff", textAlign: "left" }}
          onClick={buyPremium} disabled={busy}>
          <div className="row"><IPremium color="var(--gold-soft)" />
            <div className="grow"><div style={{ fontWeight: 700, fontSize: 16 }}>NEBANK Premium</div>
              <div style={{ opacity: .7, fontSize: 13 }}>250 Stars · {t("per_month")}</div></div>
            <IChevron color="rgba(255,255,255,.6)" /></div>
        </button>
      ) : (
        <div className="card row" style={{ background: "linear-gradient(135deg,#fbf6e6,#fff)" }}>
          <IPremium color="var(--gold)" />
          <div className="grow"><div style={{ fontWeight: 700 }}>{t("premium_active")}</div>
            <div className="sub">{me!.premium_until?.slice(0, 10)}</div></div>
        </div>
      )}

      <div className="card stack">
        <div className="section-title">{t("language")}</div>
        <Segmented value={me!.language} onChange={(v) => { setLang(v); update({ language: v }); }}
          options={[{ value: "ru" as const, label: "Русский" }, { value: "en" as const, label: "English" }]} />
      </div>

      <div className="card stack">
        <div className="section-title">{t("base_currency")}</div>
        <select className="field" value={me!.base_currency} onChange={(e) => update({ base_currency: e.target.value })}>
          {fiat.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      <div className="card stack">
        <div className="section-title">{t("theme")}</div>
        <Segmented value="light" onChange={() => {}} options={[{ value: "light", label: t("light") }]} />
      </div>

      <div className="card" style={{ padding: 4 }}>
        <div className="list">
          <Row label={t("manage_categories")} Icon={IGrid} onClick={() => nav("categories")} />
          <Row label={t("stash")} Icon={IPiggy} onClick={() => nav("stash")} />
          <Row label={t("export")} Icon={IPremium} onClick={exportXlsx} badge={!me!.is_premium ? t("premium") : undefined} />
          <Row label={t("referral")} Icon={IUsers} onClick={() =>
            shareLink(`https://t.me/share`, me!.language === "ru" ? "Веду финансы в NEBANK" : "I track my money with NEBANK")} />
        </div>
      </div>
    </div>
  );
}

function Row({ label, Icon, onClick, badge }: { label: string; Icon: any; onClick: () => void; badge?: string }) {
  return (
    <button className="item" style={{ width: "100%", textAlign: "left", padding: "14px 12px" }} onClick={onClick}>
      <span className="swatch" style={{ background: "var(--bg-2)" }}><Icon width={20} height={20} color="var(--ink-2)" /></span>
      <span className="grow" style={{ fontWeight: 600, fontSize: 15 }}>{label}</span>
      {badge && <span className="pill" style={{ background: "var(--gold)", color: "#2a2204" }}>{badge}</span>}
      <IChevron width={18} height={18} color="var(--sub)" />
    </button>
  );
}
