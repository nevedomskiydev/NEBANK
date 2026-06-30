import { useState } from "react";
import type { Nav } from "../App";
import { api } from "../lib/api";
import { useAsync } from "../lib/hooks";
import { useStore } from "../lib/store";
import { money } from "../lib/format";
import { t } from "../i18n";
import type { Habit } from "../lib/types";
import { Header, Sheet, Field, Empty, Skeleton } from "../components/ui";
import { IPlus, IShield } from "../components/icons";
import { notify, shareLink } from "../lib/telegram";

export function Habits({ nav }: { nav: Nav }) {
  const { me } = useStore();
  const cur = me!.base_currency;
  const { data, loading, reload } = useAsync<{ items: Habit[]; currency: string }>(() => api.get("/habits"));
  const [add, setAdd] = useState(false);

  return (
    <div className="stack">
      <Header title={t("habits")} sub={t("habits_hint")} onBack={() => nav("more")}
        right={<button className="btn btn-gold btn-sm" onClick={() => setAdd(true)}><IPlus width={16} height={16} />{t("start")}</button>} />
      {loading ? <Skeleton h={150} r={18} /> :
        !data!.items.length ? <Empty title={t("habits")} hint={t("habits_hint")} /> :
          data!.items.map((h) => (
            <div key={h.id} className="card" style={{ background: "linear-gradient(160deg,#fff,#f7faf7)" }}>
              <div className="row" style={{ gap: 12 }}>
                <span className="swatch" style={{ width: 44, height: 44, background: "#34C7591f" }}>
                  <IShield width={22} height={22} color="var(--green)" /></span>
                <div className="grow">
                  <div style={{ fontWeight: 700, fontSize: 16 }}>{h.name}</div>
                  <div className="sub">{h.clean_days} {t("days_clean")} · {t("best")} {h.best_streak}</div>
                </div>
              </div>
              <div className="between" style={{ marginTop: 14 }}>
                <div><div className="sub" style={{ fontSize: 12 }}>{t("saved")}</div>
                  <div className="amount" style={{ fontWeight: 750, fontSize: 22, color: "var(--green)" }}>{money(h.saved, cur)}</div></div>
                <div className="row" style={{ gap: 8 }}>
                  <button className="btn btn-ghost btn-sm" onClick={() =>
                    shareLink("https://t.me/" + (me!.referral_code ? "" : ""),
                      me!.language === "ru"
                        ? `NEBANK: ${h.clean_days} дней без «${h.name}», сэкономлено ${money(h.saved, cur)}.`
                        : `NEBANK: ${h.clean_days} days without "${h.name}", saved ${money(h.saved, cur)}.`)}>
                    {t("share_result")}</button>
                  <button className="btn btn-ghost btn-sm" style={{ color: "var(--red)" }}
                    onClick={async () => { await api.post(`/habits/${h.id}/relapse`); notify("warning"); reload(); }}>
                    {t("relapse")}</button>
                </div>
              </div>
            </div>
          ))}
      {add && <AddHabit cur={cur} onClose={() => setAdd(false)} onSaved={() => { setAdd(false); reload(); }} />}
    </div>
  );
}

function AddHabit({ cur, onClose, onSaved }: { cur: string; onClose: () => void; onSaved: () => void }) {
  const [name, setName] = useState(""); const [cost, setCost] = useState(""); const [busy, setBusy] = useState(false);
  async function save() {
    if (!name.trim()) return; setBusy(true);
    try { await api.post("/habits", { name, daily_cost: Number(cost) || 0 }); notify("success"); onSaved(); }
    catch { notify("error"); } finally { setBusy(false); }
  }
  return (
    <Sheet onClose={onClose}>
      <h2 className="h2" style={{ marginBottom: 14 }}>{t("new_habit")}</h2>
      <div className="stack">
        <label className="sub">{t("habit_name")}</label>
        <Field value={name} onChange={(e) => setName(e.target.value)} />
        <label className="sub">{t("daily_cost")} ({cur})</label>
        <Field type="number" inputMode="decimal" value={cost} onChange={(e) => setCost(e.target.value)} placeholder="0" />
        <button className="btn btn-primary btn-block" onClick={save} disabled={busy}>{t("start")}</button>
      </div>
    </Sheet>
  );
}
