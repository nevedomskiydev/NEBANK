import type { Nav } from "../App";
import { api } from "../lib/api";
import { useStore } from "../lib/store";
import { money } from "../lib/format";
import { t } from "../i18n";
import { Header } from "../components/ui";
import { IPiggy } from "../components/icons";
import { notify } from "../lib/telegram";

const ROUND_OPTS = [10, 50, 100, 500];

export function Stash({ nav }: { nav: Nav }) {
  const { me, update, refresh } = useStore();
  const cur = me!.base_currency;

  async function withdraw() {
    await api.post("/stash/withdraw"); notify("success"); refresh();
  }

  return (
    <div className="stack">
      <Header title={t("stash")} sub={t("stash_hint")} onBack={() => nav("more")} />

      <div className="card" style={{ background: "linear-gradient(160deg,#fbf6e6,#fff)", textAlign: "center", padding: 26 }}>
        <span className="swatch" style={{ width: 56, height: 56, margin: "0 auto 12px", background: "#C9A22722" }}>
          <IPiggy width={28} height={28} color="var(--gold)" /></span>
        <div className="sub">{t("stash")}</div>
        <div className="amount" style={{ fontWeight: 800, fontSize: 40, letterSpacing: "-1px" }}>
          {money(me!.stash_balance, cur)}</div>
        <button className="btn btn-gold btn-block" style={{ marginTop: 16 }}
          onClick={withdraw} disabled={me!.stash_balance <= 0}>{t("withdraw")}</button>
      </div>

      <div className="card">
        <div className="between">
          <span style={{ fontWeight: 650 }}>{t("enabled")}</span>
          <Toggle on={me!.stash_enabled} onChange={(v) => update({ stash_enabled: v })} />
        </div>
      </div>

      <div className="card">
        <div className="section-title">{t("round_to")} ({cur})</div>
        <div className="row wrap" style={{ gap: 8 }}>
          {ROUND_OPTS.map((r) => (
            <button key={r} className="pill"
              style={{ background: me!.stash_round_to === r ? "var(--gold)" : "var(--bg-2)", color: me!.stash_round_to === r ? "#2a2204" : "var(--ink-2)", padding: "10px 16px" }}
              onClick={() => update({ stash_round_to: r })}>{r}</button>
          ))}
        </div>
      </div>
    </div>
  );
}

function Toggle({ on, onChange }: { on: boolean; onChange: (v: boolean) => void }) {
  return (
    <button onClick={() => onChange(!on)} style={{
      width: 50, height: 30, borderRadius: 999, padding: 3,
      background: on ? "var(--green)" : "var(--line-strong)", transition: "background .2s",
    }}>
      <span style={{
        display: "block", width: 24, height: 24, borderRadius: 999, background: "#fff",
        boxShadow: "var(--shadow-sm)", transform: on ? "translateX(20px)" : "translateX(0)",
        transition: "transform .2s cubic-bezier(.2,.8,.2,1)",
      }} />
    </button>
  );
}
