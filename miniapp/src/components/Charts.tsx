// Lightweight SVG charts: sparkline + market area (green/red), trend bars.
function path(values: number[], w: number, h: number, pad = 2) {
  if (values.length < 2) return { line: "", area: "" };
  const min = Math.min(...values), max = Math.max(...values);
  const range = max - min || 1;
  const dx = (w - pad * 2) / (values.length - 1);
  const pts = values.map((v, i) => [pad + i * dx, pad + (h - pad * 2) * (1 - (v - min) / range)]);
  const line = pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(" ");
  const area = `${line} L${pts[pts.length - 1][0].toFixed(1)} ${h} L${pts[0][0].toFixed(1)} ${h} Z`;
  return { line, area };
}

export function Sparkline({ values, up, w = 88, h = 32 }:
  { values: number[]; up: boolean; w?: number; h?: number }) {
  if (!values || values.length < 2) return <svg width={w} height={h} />;
  const { line } = path(values, w, h);
  const color = up ? "var(--green)" : "var(--red)";
  return (
    <svg width={w} height={h}>
      <path d={line} fill="none" stroke={color} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function AreaChart({ values, up, w = 320, h = 140 }:
  { values: number[]; up: boolean; w?: number; h?: number }) {
  if (!values || values.length < 2) return <div className="skeleton" style={{ height: h, borderRadius: 16 }} />;
  const { line, area } = path(values, w, h, 6);
  const color = up ? "var(--green)" : "var(--red)";
  const id = `g${up ? "u" : "d"}`;
  return (
    <svg width="100%" height={h} viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.22" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${id})`} />
      <path d={line} fill="none" stroke={color} strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function TrendBars({ data, color = "var(--gold)", h = 120 }:
  { data: { date: string; amount: number }[]; color?: string; h?: number }) {
  const max = Math.max(...data.map((d) => d.amount), 1);
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 3, height: h }}>
      {data.map((d, i) => (
        <div key={i} className="grow" title={`${d.date}: ${d.amount}`}
          style={{
            height: `${Math.max(3, (d.amount / max) * 100)}%`,
            background: d.amount > 0 ? color : "var(--bg-2)",
            borderRadius: 5, opacity: d.amount > 0 ? 1 : 0.5,
            transition: "height .5s cubic-bezier(.2,.8,.2,1)",
          }} />
      ))}
    </div>
  );
}
