import { useState } from "react";
import type { Nav } from "../App";
import { api } from "../lib/api";
import { useAsync } from "../lib/hooks";
import { useStore } from "../lib/store";
import { money } from "../lib/format";
import { t } from "../i18n";
import type { Goal } from "../lib/types";
import { Header, Sheet, Field, Empty, Skeleton, ProgressRing } from "../components/ui";
import { IPlus, ICheck, ITrash } from "../components/icons";
import { notify } from "../lib/telegram";

export function Goals({ nav }: { nav: Nav }) {
  const { me } = useStore();
  const cur = me!.base_currency;
  const { data, loading, reload } = useAsync<{ items: Goal[]; currency: string }>(() => api.get("/goals"));
  const [sheet, setSheet] = useState<"new" | Goal | null>(null);

  return (
    <div className="stack">
      <Header title={t("goals")} onBack={() => nav("more")}
        right={<button className="btn btn-gold btn-sm" onClick={() => setSheet("new")}><IPlus width={16} height={16} />{t("add")}</button>} />
      {loading ? <Skeleton h={120} r={18} /> :
        !data!.items.length ? <Empty title={t("goals")} hint={t("new_goal")} /> :
          data!.items.map((g) => (
            <button key={g.id} className="card" style={{ width: "100%", textAlign: "left" }} onClick={() => setSheet(g)}>
              <div className="row" style={{ gap: 14 }}>
                <ProgressRing progress={g.progress} size={60} stroke={7} color={g.achieved ? "var(--green)" : "var(--gold)"}>
                  {g.achieved ? <ICheck width={22} color="var(--green)" /> : <span style={{ fontSize: 12, fontWeight: 700 }}>{Math.round(g.progress * 100)}%</span>}
                </ProgressRing>
                <div className="grow">
                  <div style={{ fontWeight: 700, fontSize: 16 }}>{g.name}</div>
                  <div className="amount" style={{ fontWeight: 650, marginTop: 2 }}>
                    {money(g.current, cur)} <span className="sub" style={{ fontWeight: 500 }}>/ {money(g.target, cur)}</span></div>
                </div>
              </div>
            </button>
          ))}
      {sheet && <GoalSheet goal={sheet === "new" ? null : sheet} cur={cur}
        onClose={() => setSheet(null)} onSaved={() => { setSheet(null); reload(); }} />}
    </div>
  );
}

function GoalSheet({ goal, cur, onClose, onSaved }:
  { goal: Goal | null; cur: string; onClose: () => void; onSaved: () => void }) {
  const [name, setName] = useState(goal?.name ?? "");
  const [target, setTarget] = useState(goal ? String(goal.target) : "");
  const [topup, setTopup] = useState("");
  const [busy, setBusy] = useState(false);

  async function create() {
    if (!name.trim() || !Number(target)) return; setBusy(true);
    try { await api.post("/goals", { name, target: Number(target) }); notify("success"); onSaved(); }
    catch { notify("error"); } finally { setBusy(false); }
  }
  async function addFunds() {
    if (!goal || !Number(topup)) return; setBusy(true);
    try { await api.post(`/goals/${goal.id}/topup`, { amount: Number(topup) }); notify("success"); onSaved(); }
    catch { notify("error"); } finally { setBusy(false); }
  }
  async function del() {
    if (!goal) return; setBusy(true);
    try { await api.del(`/goals/${goal.id}`); notify("success"); onSaved(); }
    catch { notify("error"); } finally { setBusy(false); }
  }

  return (
    <Sheet onClose={onClose}>
      <h2 className="h2" style={{ marginBottom: 14 }}>{goal ? goal.name : t("new_goal")}</h2>
      <div className="stack">
        {!goal && <>
          <label className="sub">{t("goal_name")}</label>
          <Field value={name} onChange={(e) => setName(e.target.value)} placeholder={t("goal_name")} />
          <label className="sub">{t("target")} ({cur})</label>
          <Field type="number" inputMode="decimal" value={target} onChange={(e) => setTarget(e.target.value)} />
          <button className="btn btn-primary btn-block" onClick={create} disabled={busy}>{t("save")}</button>
        </>}
        {goal && <>
          <label className="sub">{t("top_up")} ({cur})</label>
          <div className="row">
            <Field type="number" inputMode="decimal" value={topup} onChange={(e) => setTopup(e.target.value)} placeholder="0" />
            <button className="btn btn-gold" onClick={addFunds} disabled={busy || !Number(topup)}>{t("top_up")}</button>
          </div>
          <button className="btn btn-ghost" style={{ color: "var(--red)" }} onClick={del} disabled={busy}>
            <ITrash width={18} height={18} /> {t("delete")}</button>
        </>}
      </div>
    </Sheet>
  );
}
