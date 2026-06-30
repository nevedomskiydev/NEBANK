import { useState } from "react";
import type { Nav } from "../App";
import { api } from "../lib/api";
import { useAsync } from "../lib/hooks";
import { useStore } from "../lib/store";
import { money, fmtDate } from "../lib/format";
import { t } from "../i18n";
import type { Dashboard as Dash } from "../lib/types";
import { Segmented, Skeleton, Empty } from "../components/ui";
import { DonutChart } from "../components/DonutChart";
import { TrendBars } from "../components/Charts";
import { IChevron } from "../components/icons";

type Period = "today" | "week" | "month" | "year";

export function Dashboard({ nav }: { nav: Nav }) {
  const { me } = useStore();
  const [period, setPeriod] = useState<Period>("month");
  const { data, loading } = useAsync<Dash>(() => api.get(`/dashboard?period=${period}`), [period]);
  const cur = me!.base_currency;

  return (
    <div className="stack">
      <div className="between" style={{ marginTop: 4 }}>
        <div>
          <div className="brand-wordmark">NEBANK</div>
          <h1 className="h1" style={{ marginTop: 2 }}>
            {me!.first_name ? (me!.language === "ru" ? `Привет, ${me!.first_name}` : `Hi, ${me!.first_name}`) : "NEBANK"}
          </h1>
        </div>
      </div>

      <Segmented<Period> value={period} onChange={setPeriod} options={[
        { value: "today", label: t("this_today") },
        { value: "week", label: t("this_week") },
        { value: "month", label: t("this_month") },
        { value: "year", label: t("this_year") },
      ]} />

      {/* hero balance card */}
      <div className="card" style={{ background: "linear-gradient(160deg,#fff, #fbfaf6)", padding: 18 }}>
        <div className="sub">{t("net")}</div>
        <div className="amount" style={{ fontSize: 34, fontWeight: 750, marginTop: 2 }}>
          {loading ? <Skeleton h={36} w={170} /> : money(data!.net, cur, { sign: data!.net !== 0 })}
        </div>
        <div className="row" style={{ marginTop: 14, gap: 10 }}>
          <Stat label={t("income")} value={loading ? "" : money(data!.income, cur)} color="var(--green)" />
          <div style={{ width: 1, height: 30, background: "var(--line)" }} />
          <Stat label={t("expense")} value={loading ? "" : money(data!.expense, cur)} color="var(--red)" />
        </div>
      </div>

      {/* signature donut */}
      <div className="card">
        <div className="section-title">{t("by_category")}</div>
        {loading ? <Skeleton h={260} r={16} /> :
          data!.categories.length === 0 ? <Empty title={t("no_ops")} hint={t("add_first")} /> :
            <DonutChart data={data!.categories} total={data!.expense} currency={cur}
              centerLabel={t("spent")} onOpen={(id) => nav("history", { category: String(id) })} />}
      </div>

      {/* trend */}
      {!loading && data!.trend.length > 1 && (
        <div className="card">
          <div className="section-title">{t("trend")}</div>
          <TrendBars data={data!.trend} />
        </div>
      )}

      {/* recent */}
      <div className="card">
        <div className="between" style={{ marginBottom: 4 }}>
          <div className="section-title" style={{ margin: 0 }}>{t("recent")}</div>
          <button className="pill" onClick={() => nav("history")}>{t("see_all")}</button>
        </div>
        {loading ? <><Skeleton h={44} style={{ marginTop: 10 }} /><Skeleton h={44} style={{ marginTop: 10 }} /></> :
          data!.recent.length === 0 ? <Empty title={t("no_ops")} hint={t("add_first")} /> :
            <div className="list">
              {data!.recent.map((tx) => (
                <button key={tx.id} className="item" style={{ width: "100%", textAlign: "left" }}
                  onClick={() => nav("history")}>
                  <span className="swatch" style={{ background: (tx.category_color || "#C9A227") + "1f" }}>
                    <span className="dot" style={{ background: tx.category_color || "#C9A227" }} />
                  </span>
                  <span className="grow">
                    <div style={{ fontWeight: 600, fontSize: 14.5 }}>{tx.title || tx.category || "—"}</div>
                    <div className="sub" style={{ fontSize: 12 }}>{tx.category} · {fmtDate(tx.occurred_at, me!.language)}</div>
                  </span>
                  <span className="amount" style={{ fontWeight: 650, color: tx.kind === "income" ? "var(--green)" : "var(--ink)" }}>
                    {tx.kind === "income" ? "+" : "−"} {money(tx.amount, cur)}
                  </span>
                  <IChevron width={16} height={16} color="var(--sub)" />
                </button>
              ))}
            </div>}
      </div>
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="grow">
      <div className="sub" style={{ fontSize: 12 }}>{label}</div>
      <div className="amount" style={{ fontWeight: 650, color, fontSize: 16 }}>{value || "—"}</div>
    </div>
  );
}
