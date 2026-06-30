import { useEffect, useMemo, useState } from "react";
import type { Nav } from "../App";
import { api } from "../lib/api";
import { useStore } from "../lib/store";
import { money, fmtDate } from "../lib/format";
import { t } from "../i18n";
import type { Tx, Category } from "../lib/types";
import { Header, Sheet, Field, Empty, Skeleton } from "../components/ui";
import { ISearch, ITrash } from "../components/icons";
import { haptic, notify } from "../lib/telegram";

export function History({ nav, params }: { nav: Nav; params?: Record<string, string> }) {
  const { me } = useStore();
  const cur = me!.base_currency;
  const [items, setItems] = useState<Tx[] | null>(null);
  const [cats, setCats] = useState<Category[]>([]);
  const [q, setQ] = useState("");
  const [catFilter, setCatFilter] = useState<number | null>(
    params?.category ? Number(params.category) : null);
  const [edit, setEdit] = useState<Tx | null>(null);

  async function load() {
    const qs = new URLSearchParams();
    if (q) qs.set("q", q);
    if (catFilter) qs.set("category_id", String(catFilter));
    qs.set("limit", "200");
    const res = await api.get<{ items: Tx[] }>(`/transactions?${qs}`);
    setItems(res.items);
  }
  useEffect(() => { api.get<{ items: Category[] }>("/categories").then((r) => setCats(r.items)); }, []);
  useEffect(() => { const id = setTimeout(load, 220); return () => clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q, catFilter]);

  const groups = useMemo(() => {
    const m = new Map<string, Tx[]>();
    (items ?? []).forEach((tx) => { const k = tx.occurred_at; (m.get(k) ?? m.set(k, []).get(k))!.push(tx); });
    return [...m.entries()].sort((a, b) => b[0].localeCompare(a[0]));
  }, [items]);

  return (
    <div className="stack">
      <Header title={t("history")} onBack={() => nav("home")} />

      <div className="card" style={{ padding: 10 }}>
        <div className="row" style={{ background: "var(--bg-2)", borderRadius: 12, padding: "0 12px" }}>
          <ISearch width={18} height={18} color="var(--sub)" />
          <input className="field" style={{ border: "none", background: "transparent", height: 44 }}
            placeholder={t("search")} value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <div className="row wrap" style={{ marginTop: 10, gap: 6 }}>
          <button className={`pill ${catFilter === null ? "" : ""}`}
            style={{ background: catFilter === null ? "var(--ink)" : "var(--bg-2)", color: catFilter === null ? "#fff" : "var(--ink-2)" }}
            onClick={() => setCatFilter(null)}>{t("all")}</button>
          {cats.map((c) => (
            <button key={c.id} className="pill"
              style={{ background: catFilter === c.id ? c.color : "var(--bg-2)", color: catFilter === c.id ? "#fff" : "var(--ink-2)" }}
              onClick={() => setCatFilter(catFilter === c.id ? null : c.id)}>{c.name}</button>
          ))}
        </div>
      </div>

      {items === null ? <><Skeleton h={60} r={16} /><Skeleton h={60} r={16} /></> :
        groups.length === 0 ? <Empty title={t("no_ops")} hint={t("add_first")} /> :
          groups.map(([day, txs]) => (
            <div key={day} className="card">
              <div className="section-title">{fmtDate(day, me!.language)}</div>
              <div className="list">
                {txs.map((tx) => (
                  <button key={tx.id} className="item" style={{ width: "100%", textAlign: "left" }}
                    onClick={() => { haptic("light"); setEdit(tx); }}>
                    <span className="swatch" style={{ background: (tx.category_color || "#C9A227") + "1f" }}>
                      <span className="dot" style={{ background: tx.category_color || "#C9A227" }} />
                    </span>
                    <span className="grow">
                      <div style={{ fontWeight: 600, fontSize: 14.5 }}>{tx.title || tx.category || "—"}</div>
                      <div className="sub" style={{ fontSize: 12 }}>
                        {tx.category}{tx.original_currency !== cur ? ` · ${tx.original_amount} ${tx.original_currency}` : ""}
                      </div>
                    </span>
                    <span className="amount" style={{ fontWeight: 650, color: tx.kind === "income" ? "var(--green)" : "var(--ink)" }}>
                      {tx.kind === "income" ? "+" : "−"} {money(tx.amount, cur)}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          ))}

      {edit && <EditSheet tx={edit} cats={cats} cur={cur}
        onClose={() => setEdit(null)}
        onSaved={() => { setEdit(null); load(); }}
        onDeleted={() => { setEdit(null); load(); }} />}
    </div>
  );
}

function EditSheet({ tx, cats, cur, onClose, onSaved, onDeleted }:
  { tx: Tx; cats: Category[]; cur: string; onClose: () => void; onSaved: () => void; onDeleted: () => void }) {
  const [amount, setAmount] = useState(String(tx.amount));
  const [title, setTitle] = useState(tx.title ?? "");
  const [catId, setCatId] = useState<number | null>(tx.category_id);
  const [date, setDate] = useState(tx.occurred_at);
  const [busy, setBusy] = useState(false);

  async function save() {
    setBusy(true);
    try {
      await api.patch(`/transactions/${tx.id}`, {
        amount: Number(amount), title, category_id: catId, occurred_at: date,
      });
      notify("success"); onSaved();
    } catch { notify("error"); } finally { setBusy(false); }
  }
  async function del() {
    setBusy(true);
    try { await api.del(`/transactions/${tx.id}`); notify("success"); onDeleted(); }
    catch { notify("error"); } finally { setBusy(false); }
  }

  return (
    <Sheet onClose={onClose}>
      <h2 className="h2" style={{ marginBottom: 14 }}>{t("edit")}</h2>
      <div className="stack">
        <label className="sub">{t("amount")} ({cur})</label>
        <Field type="number" inputMode="decimal" value={amount} onChange={(e) => setAmount(e.target.value)} />
        <label className="sub">{t("title")}</label>
        <Field value={title} onChange={(e) => setTitle(e.target.value)} />
        <label className="sub">{t("category")}</label>
        <div className="row wrap" style={{ gap: 6 }}>
          {cats.map((c) => (
            <button key={c.id} className="pill"
              style={{ background: catId === c.id ? c.color : "var(--bg-2)", color: catId === c.id ? "#fff" : "var(--ink-2)" }}
              onClick={() => setCatId(c.id)}>{c.name}</button>
          ))}
        </div>
        <label className="sub">{t("date")}</label>
        <Field type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        <div className="row" style={{ marginTop: 8 }}>
          <button className="btn btn-ghost" style={{ color: "var(--red)" }} onClick={del} disabled={busy}>
            <ITrash width={18} height={18} /> {t("delete")}
          </button>
          <button className="btn btn-primary grow" onClick={save} disabled={busy}>{t("save")}</button>
        </div>
      </div>
    </Sheet>
  );
}
