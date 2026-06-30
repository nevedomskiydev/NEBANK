import { useState } from "react";
import type { Nav } from "../App";
import { api } from "../lib/api";
import { useAsync } from "../lib/hooks";
import { useStore } from "../lib/store";
import { money } from "../lib/format";
import { t } from "../i18n";
import type { Budget, Category } from "../lib/types";
import { Header, Sheet, Field, Empty, Skeleton } from "../components/ui";
import { notify } from "../lib/telegram";

export function Budgets({ nav }: { nav: Nav }) {
  const { me } = useStore();
  const cur = me!.base_currency;
  const { data, loading, reload } = useAsync<{ items: Budget[]; currency: string }>(() => api.get("/budgets"));
  const [editing, setEditing] = useState<Budget | "new" | null>(null);

  return (
    <div className="stack">
      <Header title={t("budgets")} sub={t("budgets_hint")} onBack={() => nav("home")}
        right={<button className="btn btn-gold btn-sm" onClick={() => setEditing("new")}>{t("set_limit")}</button>} />

      {loading ? <><Skeleton h={80} r={18} /><Skeleton h={80} r={18} /></> :
        !data!.items.length ? <Empty title={t("budgets")} hint={t("budgets_hint")} /> :
          data!.items.map((b) => {
            const p = Math.min(1, b.progress);
            const color = b.over ? "var(--red)" : p > 0.85 ? "var(--c5)" : "var(--green)";
            return (
              <button key={b.id} className="card" style={{ textAlign: "left", width: "100%" }}
                onClick={() => setEditing(b)}>
                <div className="between">
                  <div className="row"><span className="dot" style={{ background: b.color }} />
                    <span style={{ fontWeight: 650 }}>{b.name}</span></div>
                  <span className="amount sub" style={{ fontSize: 13 }}>
                    {money(b.spent, cur)} {t("of")} {money(b.limit, cur)}</span>
                </div>
                <div className="bar" style={{ marginTop: 12 }}>
                  <span style={{ width: `${p * 100}%`, background: color }} />
                </div>
                <div className="between" style={{ marginTop: 8 }}>
                  <span className="sub" style={{ color, fontWeight: 600, fontSize: 12.5 }}>
                    {b.over ? t("over_budget") : `${Math.round(p * 100)}%`}</span>
                  <span className="sub" style={{ fontSize: 12.5 }}>
                    {b.over ? money(b.spent - b.limit, cur) : `${money(Math.max(0, b.limit - b.spent), cur)} ${t("left")}`}</span>
                </div>
              </button>
            );
          })}

      {editing && <BudgetSheet budget={editing === "new" ? null : editing} cur={cur}
        onClose={() => setEditing(null)} onSaved={() => { setEditing(null); reload(); }} />}
    </div>
  );
}

function BudgetSheet({ budget, cur, onClose, onSaved }:
  { budget: Budget | null; cur: string; onClose: () => void; onSaved: () => void }) {
  const { data } = useAsync<{ items: Category[] }>(() => api.get("/categories"));
  const [catId, setCatId] = useState<number | null>(budget?.category_id ?? null);
  const [limit, setLimit] = useState(budget ? String(budget.limit) : "");
  const [busy, setBusy] = useState(false);

  async function save() {
    if (!catId || !Number(limit)) return;
    setBusy(true);
    try { await api.put("/budgets", { category_id: catId, limit: Number(limit) }); notify("success"); onSaved(); }
    catch { notify("error"); } finally { setBusy(false); }
  }
  async function del() {
    if (!budget) return; setBusy(true);
    try { await api.del(`/budgets/${budget.id}`); notify("success"); onSaved(); }
    catch { notify("error"); } finally { setBusy(false); }
  }

  return (
    <Sheet onClose={onClose}>
      <h2 className="h2" style={{ marginBottom: 14 }}>{t("set_limit")}</h2>
      <div className="stack">
        <label className="sub">{t("category")}</label>
        <div className="row wrap" style={{ gap: 6 }}>
          {(data?.items ?? []).filter((c) => c.kind === "expense").map((c) => (
            <button key={c.id} className="pill"
              style={{ background: catId === c.id ? c.color : "var(--bg-2)", color: catId === c.id ? "#fff" : "var(--ink-2)" }}
              onClick={() => setCatId(c.id)}>{c.name}</button>
          ))}
        </div>
        <label className="sub">{t("limit")} ({cur})</label>
        <Field type="number" inputMode="decimal" value={limit} onChange={(e) => setLimit(e.target.value)} placeholder="0" />
        <div className="row" style={{ marginTop: 8 }}>
          {budget && <button className="btn btn-ghost" style={{ color: "var(--red)" }} onClick={del} disabled={busy}>{t("delete")}</button>}
          <button className="btn btn-primary grow" onClick={save} disabled={busy || !catId || !Number(limit)}>{t("save")}</button>
        </div>
      </div>
    </Sheet>
  );
}
