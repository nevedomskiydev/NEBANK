import { useState } from "react";
import type { Nav } from "../App";
import { api } from "../lib/api";
import { useAsync } from "../lib/hooks";
import { useStore } from "../lib/store";
import { money, fmtDate } from "../lib/format";
import { t } from "../i18n";
import type { Subscription } from "../lib/types";
import { Header, Sheet, Field, Empty, Skeleton } from "../components/ui";
import { IPlus, IRepeat, IBell, ITrash } from "../components/icons";
import { notify } from "../lib/telegram";

interface Suggestion { fingerprint: string; name: string; amount: number; next_charge: string; }

export function Subscriptions({ nav }: { nav: Nav }) {
  const { me } = useStore();
  const cur = me!.base_currency;
  const { data, loading, reload } = useAsync<{ items: Subscription[]; currency: string }>(() => api.get("/subscriptions"));
  const { data: sugg, reload: reloadSugg } = useAsync<{ items: Suggestion[] }>(() => api.get("/subscriptions/suggestions"));
  const [add, setAdd] = useState(false);

  const totalMonthly = (data?.items ?? []).filter((s) => s.period === "monthly")
    .reduce((s, x) => s + x.amount, 0);

  async function accept(s: Suggestion) {
    await api.post("/subscriptions", { name: s.name, amount: s.amount, currency: cur, period: "monthly", next_charge: s.next_charge });
    notify("success"); reload(); reloadSugg();
  }

  return (
    <div className="stack">
      <Header title={t("subscriptions")} onBack={() => nav("more")}
        right={<button className="btn btn-gold btn-sm" onClick={() => setAdd(true)}><IPlus width={16} height={16} />{t("add")}</button>} />

      {!!totalMonthly && (
        <div className="card" style={{ background: "linear-gradient(160deg,#fff,#fbfaf6)" }}>
          <div className="sub">{t("per_month")}</div>
          <div className="amount" style={{ fontWeight: 750, fontSize: 28 }}>{money(totalMonthly, cur)}</div>
        </div>
      )}

      {sugg && sugg.items.length > 0 && (
        <div className="card">
          <div className="section-title">{t("suggestions")}</div>
          <div className="list">
            {sugg.items.map((s) => (
              <div key={s.fingerprint} className="item">
                <span className="swatch" style={{ background: "#007AFF1f" }}><IBell width={18} height={18} color="var(--blue)" /></span>
                <span className="grow"><div style={{ fontWeight: 600 }}>{s.name}</div>
                  <div className="sub" style={{ fontSize: 12 }}>{money(s.amount, cur)} · {fmtDate(s.next_charge, me!.language)}</div></span>
                <button className="btn btn-ghost btn-sm" onClick={() => accept(s)}>{t("add")}</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {loading ? <Skeleton h={120} r={18} /> :
        !data!.items.length ? <Empty title={t("subscriptions")} hint={t("add_sub")} /> :
          <div className="card"><div className="list">
            {data!.items.map((s) => (
              <div key={s.id} className="item">
                <span className="swatch" style={{ background: "#C9A2271f" }}><IRepeat width={18} height={18} color="var(--gold)" /></span>
                <span className="grow"><div style={{ fontWeight: 600 }}>{s.name}</div>
                  <div className="sub" style={{ fontSize: 12 }}>{t("next_charge")}: {fmtDate(s.next_charge, me!.language)}</div></span>
                <span className="amount" style={{ fontWeight: 650 }}>{money(s.amount, s.currency)}</span>
                <button className="swatch" style={{ background: "transparent" }}
                  onClick={async () => { await api.del(`/subscriptions/${s.id}`); reload(); }}>
                  <ITrash width={18} height={18} color="var(--sub)" /></button>
              </div>
            ))}
          </div></div>}

      {add && <AddSub cur={cur} onClose={() => setAdd(false)} onSaved={() => { setAdd(false); reload(); }} />}
    </div>
  );
}

function AddSub({ cur, onClose, onSaved }: { cur: string; onClose: () => void; onSaved: () => void }) {
  const [name, setName] = useState(""); const [amount, setAmount] = useState("");
  const [period, setPeriod] = useState("monthly"); const [busy, setBusy] = useState(false);
  async function save() {
    if (!name.trim() || !Number(amount)) return; setBusy(true);
    try { await api.post("/subscriptions", { name, amount: Number(amount), currency: cur, period }); notify("success"); onSaved(); }
    catch { notify("error"); } finally { setBusy(false); }
  }
  return (
    <Sheet onClose={onClose}>
      <h2 className="h2" style={{ marginBottom: 14 }}>{t("add_sub")}</h2>
      <div className="stack">
        <Field value={name} onChange={(e) => setName(e.target.value)} placeholder={t("title")} />
        <Field type="number" inputMode="decimal" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder={`${t("amount")} (${cur})`} />
        <select className="field" value={period} onChange={(e) => setPeriod(e.target.value)}>
          <option value="monthly">{t("monthly")}</option>
          <option value="weekly">{t("weekly")}</option>
          <option value="yearly">{t("yearly")}</option>
        </select>
        <button className="btn btn-primary btn-block" onClick={save} disabled={busy}>{t("save")}</button>
      </div>
    </Sheet>
  );
}
