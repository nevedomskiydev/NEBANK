import { useState } from "react";
import type { Nav } from "../App";
import { api } from "../lib/api";
import { useAsync } from "../lib/hooks";
import { t } from "../i18n";
import type { Family as Fam } from "../lib/types";
import { Header, Field, Skeleton } from "../components/ui";
import { IUsers } from "../components/icons";
import { notify, shareLink } from "../lib/telegram";

export function Family({ nav }: { nav: Nav }) {
  const { data, loading, reload } = useAsync<Fam>(() => api.get("/family"));
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);

  async function create() {
    if (!name.trim()) { notify("error"); return; }  // TZ §12.11: never auto-name
    setBusy(true);
    try { await api.post("/family", { name }); notify("success"); reload(); }
    catch { notify("error"); } finally { setBusy(false); }
  }
  async function join() {
    if (!code.trim()) return; setBusy(true);
    try { await api.post("/family/join", { code: code.trim() }); notify("success"); reload(); }
    catch { notify("error"); } finally { setBusy(false); }
  }

  if (loading) return <div className="stack"><Header title={t("family")} onBack={() => nav("more")} /><Skeleton h={160} r={18} /></div>;

  if (data!.group) {
    const g = data!.group;
    return (
      <div className="stack">
        <Header title={g.name} sub={t("family")} onBack={() => nav("more")} />
        <div className="card" style={{ background: "linear-gradient(160deg,#fff,#f6f8fb)", textAlign: "center", padding: 24 }}>
          <span className="swatch" style={{ width: 54, height: 54, margin: "0 auto 12px", background: "#007AFF1f" }}>
            <IUsers width={26} height={26} color="var(--blue)" /></span>
          <div style={{ fontWeight: 700, fontSize: 18 }}>{g.name}</div>
          <div className="sub" style={{ marginTop: 2 }}>{t("invite_code")}: {g.invite_code}</div>
          <button className="btn btn-primary btn-block" style={{ marginTop: 16 }}
            onClick={() => shareLink(g.invite_link, t("family_hint"))}>{t("invite")}</button>
        </div>
        <div className="card">
          <div className="section-title">{t("members")}</div>
          <div className="list">
            {g.members.map((m, i) => (
              <div key={i} className="item">
                <span className="swatch" style={{ background: "var(--bg-2)" }}><IUsers width={18} height={18} color="var(--ink-2)" /></span>
                <span className="grow" style={{ fontWeight: 600 }}>{m.name}</span>
                <span className="pill">{m.role === "owner" ? (t("family")) : t("members")}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="stack">
      <Header title={t("family")} sub={t("family_hint")} onBack={() => nav("more")} />
      <div className="card stack">
        <div className="section-title">{t("create_family")}</div>
        <Field value={name} onChange={(e) => setName(e.target.value)} placeholder={t("family_name")} />
        <button className="btn btn-gold btn-block" onClick={create} disabled={busy || !name.trim()}>{t("create_family")}</button>
      </div>
      <div className="card stack">
        <div className="section-title">{t("join")}</div>
        <div className="row">
          <Field value={code} onChange={(e) => setCode(e.target.value)} placeholder={t("invite_code")} />
          <button className="btn btn-ghost" onClick={join} disabled={busy || !code.trim()}>{t("join")}</button>
        </div>
      </div>
    </div>
  );
}
