import { useState } from "react";
import type { Nav } from "../App";
import { api } from "../lib/api";
import { useAsync } from "../lib/hooks";
import { t } from "../i18n";
import type { Achievement } from "../lib/types";
import { Header, Sheet, ProgressRing, Skeleton } from "../components/ui";
import { ITrophy, ICheck } from "../components/icons";
import { haptic } from "../lib/telegram";

export function Achievements({ nav }: { nav: Nav }) {
  const { data, loading } = useAsync<{ items: Achievement[] }>(() => api.get("/achievements"));
  const [open, setOpen] = useState<Achievement | null>(null);
  const unlocked = data?.items.filter((a) => a.unlocked).length ?? 0;

  return (
    <div className="stack">
      <Header title={t("achievements")} sub={data ? `${unlocked} / ${data.items.length} ${t("unlocked").toLowerCase()}` : ""}
        onBack={() => nav("more")} />
      {loading ? <Skeleton h={300} r={18} /> : (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          {data!.items.map((a) => (
            <button key={a.code} className="card" style={{ alignItems: "center", textAlign: "center", padding: 16 }}
              onClick={() => { haptic("light"); setOpen(a); }}>
              <ProgressRing progress={a.progress} size={66} stroke={6}
                color={a.unlocked ? "var(--gold)" : "var(--line-strong)"}>
                <span className="swatch" style={{
                  width: 42, height: 42,
                  background: a.unlocked ? "linear-gradient(140deg,var(--gold-soft),var(--gold))" : "var(--bg-2)",
                }}>
                  {a.unlocked ? <ICheck width={20} height={20} color="#2a2204" />
                    : <ITrophy width={20} height={20} color="var(--sub)" />}
                </span>
              </ProgressRing>
              <div style={{ fontWeight: 650, fontSize: 13.5, marginTop: 10 }}>{a.title}</div>
              <div className="sub" style={{ fontSize: 11.5, marginTop: 2 }}>
                {Math.round(a.value)} / {a.target}</div>
            </button>
          ))}
        </div>
      )}
      {open && (
        <Sheet onClose={() => setOpen(null)}>
          <div style={{ textAlign: "center" }}>
            <ProgressRing progress={open.progress} size={96} stroke={8}
              color={open.unlocked ? "var(--gold)" : "var(--line-strong)"}>
              <ITrophy width={34} height={34} color={open.unlocked ? "var(--gold)" : "var(--sub)"} />
            </ProgressRing>
            <h2 className="h2" style={{ marginTop: 12 }}>{open.title}</h2>
            <p className="sub" style={{ marginTop: 6 }}>{open.description}</p>
            <div className="bar" style={{ marginTop: 14 }}>
              <span style={{ width: `${open.progress * 100}%`, background: "var(--gold)" }} />
            </div>
            <div className="sub" style={{ marginTop: 8 }}>
              {open.unlocked ? t("unlocked") : `${Math.round(open.value)} / ${open.target}`}</div>
          </div>
        </Sheet>
      )}
    </div>
  );
}
