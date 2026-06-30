import type { Nav } from "../App";
import { api } from "../lib/api";
import { useAsync } from "../lib/hooks";
import { money, pct } from "../lib/format";
import { t } from "../i18n";
import type { Insights as Ins } from "../lib/types";
import { Header, Skeleton, ProgressRing } from "../components/ui";

export function Insights({ nav }: { nav: Nav }) {
  const { data, loading } = useAsync<Ins>(() => api.get("/insights"));
  if (loading || !data) return <div className="stack"><Header title={t("insights")} onBack={() => nav("more")} /><Skeleton h={140} r={18} /><Skeleton h={120} r={18} /></div>;
  const cur = data.currency;
  const expDown = (data.expense_change_pct ?? 0) <= 0;
  const forecastP = data.days_total ? data.days_elapsed / data.days_total : 0;

  return (
    <div className="stack">
      <Header title={t("insights")} onBack={() => nav("more")} />

      <div className="card">
        <div className="section-title">{t("expense")} · {t("vs_last_month")}</div>
        <div className="between">
          <div>
            <div className="amount" style={{ fontWeight: 750, fontSize: 28 }}>{money(data.current.expense, cur)}</div>
            <div className="sub">{t("this_month").toLowerCase()}</div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div className={expDown ? "up" : "down"} style={{ fontWeight: 750, fontSize: 20 }}>{pct(data.expense_change_pct)}</div>
            <div className="sub">{money(data.previous.expense, cur)}</div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="row" style={{ gap: 16 }}>
          <ProgressRing progress={forecastP} size={72} stroke={8}>
            <div style={{ fontSize: 12, fontWeight: 700 }}>{data.days_elapsed}/{data.days_total}</div>
          </ProgressRing>
          <div className="grow">
            <div className="section-title" style={{ margin: 0 }}>{t("forecast")}</div>
            <div className="amount" style={{ fontWeight: 750, fontSize: 24 }}>{money(data.forecast_expense, cur)}</div>
            <div className="sub">{t("forecast_note")}</div>
          </div>
        </div>
      </div>

      <div className="card between">
        <div><div className="section-title" style={{ margin: 0 }}>{t("income")}</div>
          <div className="amount" style={{ fontWeight: 700, fontSize: 20 }}>{money(data.current.income, cur)}</div></div>
        <div className={`${(data.income_change_pct ?? 0) >= 0 ? "up" : "down"}`} style={{ fontWeight: 700 }}>{pct(data.income_change_pct)}</div>
      </div>
    </div>
  );
}
