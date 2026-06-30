import { useState } from "react";
import type { Nav } from "../App";
import { api } from "../lib/api";
import { useAsync } from "../lib/hooks";
import { t } from "../i18n";
import type { Category } from "../lib/types";
import { Header, Sheet, Field, Skeleton } from "../components/ui";
import { IPlus, ITrash } from "../components/icons";
import { notify } from "../lib/telegram";

const COLORS = ["#C9A227", "#34C759", "#5AC8FA", "#AF52DE", "#FF9500", "#FF2D55", "#30B0C7", "#007AFF", "#8E8E93", "#FF3B30"];

export function Categories({ nav }: { nav: Nav }) {
  const { data, loading, reload } = useAsync<{ items: Category[] }>(() => api.get("/categories"));
  const [sheet, setSheet] = useState<"new" | Category | null>(null);

  return (
    <div className="stack">
      <Header title={t("manage_categories")} onBack={() => nav("more")}
        right={<button className="btn btn-gold btn-sm" onClick={() => setSheet("new")}><IPlus width={16} height={16} />{t("add")}</button>} />
      {loading ? <Skeleton h={200} r={18} /> : (
        <div className="card"><div className="list">
          {data!.items.map((c) => (
            <button key={c.id} className="item" style={{ width: "100%", textAlign: "left" }} onClick={() => setSheet(c)}>
              <span className="swatch" style={{ background: c.color + "22" }}><span className="dot" style={{ background: c.color }} /></span>
              <span className="grow" style={{ fontWeight: 600 }}>{c.name}</span>
              <span className="pill">{c.kind === "income" ? t("income") : t("expense")}</span>
            </button>
          ))}
        </div></div>
      )}
      {sheet && <CatSheet cat={sheet === "new" ? null : sheet}
        onClose={() => setSheet(null)} onSaved={() => { setSheet(null); reload(); }} />}
    </div>
  );
}

function CatSheet({ cat, onClose, onSaved }: { cat: Category | null; onClose: () => void; onSaved: () => void }) {
  const [name, setName] = useState(cat?.name ?? "");
  const [color, setColor] = useState(cat?.color ?? COLORS[0]);
  const [kind, setKind] = useState(cat?.kind ?? "expense");
  const [busy, setBusy] = useState(false);

  async function save() {
    if (!name.trim()) return; setBusy(true);
    try {
      if (cat) await api.patch(`/categories/${cat.id}`, { name, color, kind });
      else await api.post("/categories", { name, color, kind });
      notify("success"); onSaved();
    } catch { notify("error"); } finally { setBusy(false); }
  }
  async function del() {
    if (!cat) return; setBusy(true);
    try { await api.del(`/categories/${cat.id}`); notify("success"); onSaved(); }
    catch { notify("error"); } finally { setBusy(false); }
  }

  return (
    <Sheet onClose={onClose}>
      <h2 className="h2" style={{ marginBottom: 14 }}>{cat ? t("edit") : t("add")}</h2>
      <div className="stack">
        <Field value={name} onChange={(e) => setName(e.target.value)} placeholder={t("category")} />
        <div className="row wrap" style={{ gap: 10 }}>
          {COLORS.map((c) => (
            <button key={c} onClick={() => setColor(c)} style={{
              width: 32, height: 32, borderRadius: 10, background: c,
              outline: color === c ? "3px solid var(--ink)" : "none", outlineOffset: 2,
            }} />
          ))}
        </div>
        <div className="row" style={{ marginTop: 6 }}>
          {cat && <button className="btn btn-ghost" style={{ color: "var(--red)" }} onClick={del} disabled={busy}>
            <ITrash width={18} height={18} /></button>}
          <button className="btn btn-primary grow" onClick={save} disabled={busy}>{t("save")}</button>
        </div>
      </div>
    </Sheet>
  );
}
