import { useEffect, useState } from "react";
import type { Nav } from "../App";
import { api } from "../lib/api";
import { useAsync } from "../lib/hooks";
import { useStore } from "../lib/store";
import { money, pct } from "../lib/format";
import { t } from "../i18n";
import type { RateItem } from "../lib/types";
import { Header, Segmented, Skeleton } from "../components/ui";
import { Sparkline, AreaChart } from "../components/Charts";

const SYMBOLS = ["BTC", "ETH", "USDT", "TRX", "EUR", "GBP"];

export function Rates({ nav }: { nav: Nav }) {
  const { me } = useStore();
  const vs = me!.base_currency;
  const [tab, setTab] = useState<"market" | "converter">("market");
  const { data, loading } = useAsync<{ items: RateItem[] }>(
    () => api.get(`/rates?symbols=${SYMBOLS.join(",")}&vs=${vs}`));

  return (
    <div className="stack">
      <Header title={t("rates")} sub={t("rate_live")} onBack={() => nav("home")} />
      <Segmented value={tab} onChange={setTab} options={[
        { value: "market", label: t("market") }, { value: "converter", label: t("converter") }]} />

      {tab === "market" ? (
        loading ? <><Skeleton h={72} r={16} /><Skeleton h={72} r={16} /><Skeleton h={72} r={16} /></> :
          data!.items.map((r) => {
            const up = (r.change_pct ?? 0) >= 0;
            return (
              <div key={r.symbol} className="card">
                <div className="between">
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 16 }}>{r.symbol}<span className="sub" style={{ fontWeight: 500 }}> / {r.vs}</span></div>
                    <div className="amount" style={{ fontWeight: 650, fontSize: 18, marginTop: 2 }}>
                      {r.price != null ? money(r.price, r.vs) : "—"}</div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <Sparkline values={r.spark} up={up} />
                    <div className={up ? "up" : "down"} style={{ fontWeight: 700, fontSize: 13, marginTop: 2 }}>
                      {pct(r.change_pct)}</div>
                  </div>
                </div>
              </div>
            );
          })
      ) : <Converter vs={vs} />}
    </div>
  );
}

function Converter({ vs }: { vs: string }) {
  const { me } = useStore();
  const all = [...me!.currencies.crypto, ...me!.currencies.fiat];
  const [amount, setAmount] = useState("1");
  const [from, setFrom] = useState("BTC");
  const [to, setTo] = useState(vs);
  const [result, setResult] = useState<number | null>(null);
  const [series, setSeries] = useState<number[]>([]);

  useEffect(() => {
    const id = setTimeout(async () => {
      try {
        const r = await api.get<{ result: number | null }>(
          `/rates/convert?amount=${Number(amount) || 0}&from=${from}&to=${to}`);
        setResult(r.result);
        const s = await api.get<{ series: number[][] }>(`/rates/series?symbol=${from}&vs=${to}&days=30`);
        setSeries(s.series.map((p) => p[1]));
      } catch { setResult(null); }
    }, 250);
    return () => clearTimeout(id);
  }, [amount, from, to]);

  const up = series.length > 1 && series[series.length - 1] >= series[0];

  return (
    <>
      <div className="card stack">
        <label className="sub">{t("amount_label")}</label>
        <input className="field" type="number" inputMode="decimal" value={amount}
          onChange={(e) => setAmount(e.target.value)} />
        <div className="row" style={{ gap: 10 }}>
          <div className="grow">
            <label className="sub">{t("from")}</label>
            <select className="field" value={from} onChange={(e) => setFrom(e.target.value)}>
              {all.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div className="grow">
            <label className="sub">{t("to")}</label>
            <select className="field" value={to} onChange={(e) => setTo(e.target.value)}>
              {all.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
        </div>
        <div className="card" style={{ background: "var(--bg)", marginTop: 4 }}>
          <div className="sub">{t("result")}</div>
          <div className="amount" style={{ fontWeight: 750, fontSize: 26 }}>
            {result != null ? money(result, to) : "—"}</div>
        </div>
      </div>
      {series.length > 1 && (
        <div className="card">
          <div className="section-title">{from} / {to} · 30d</div>
          <AreaChart values={series} up={up} />
        </div>
      )}
    </>
  );
}
