// Signature ring chart with tap-to-drill-into-category (TZ §12.1).
import { useState } from "react";
import { haptic } from "../lib/telegram";
import { money } from "../lib/format";
import type { CatAgg } from "../lib/types";

const PALETTE = ["#C9A227", "#34C759", "#5AC8FA", "#AF52DE", "#FF9500", "#FF2D55", "#30B0C7", "#007AFF", "#8E8E93"];

function polar(cx: number, cy: number, r: number, deg: number) {
  const a = ((deg - 90) * Math.PI) / 180;
  return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
}
function arc(cx: number, cy: number, r: number, start: number, end: number, width: number) {
  const [x1, y1] = polar(cx, cy, r, end);
  const [x2, y2] = polar(cx, cy, r, start);
  const [x3, y3] = polar(cx, cy, r - width, start);
  const [x4, y4] = polar(cx, cy, r - width, end);
  const large = end - start > 180 ? 1 : 0;
  return `M${x1} ${y1} A${r} ${r} 0 ${large} 0 ${x2} ${y2} L${x3} ${y3} A${r - width} ${r - width} 0 ${large} 1 ${x4} ${y4} Z`;
}

export function DonutChart({ data, total, currency, centerLabel, onOpen }:
  { data: CatAgg[]; total: number; currency: string; centerLabel: string;
    onOpen?: (categoryId: number) => void }) {
  const [sel, setSel] = useState<number | null>(null);
  const size = 230, cx = size / 2, cy = size / 2, R = 100, W = 30;
  const items = data.slice(0, 9);
  const sum = items.reduce((s, c) => s + c.total, 0) || 1;

  let angle = 0;
  const segs = items.map((c, i) => {
    const sweep = (c.total / sum) * 360;
    const seg = { c, i, start: angle, end: angle + sweep - (items.length > 1 ? 1.5 : 0) };
    angle += sweep;
    return seg;
  });

  const selected = sel !== null ? items[sel] : null;
  const centerMain = selected ? money(selected.total, currency) : money(total, currency);
  const centerSub = selected ? selected.name : centerLabel;
  const centerPct = selected ? `${Math.round((selected.total / sum) * 100)}%` : "";

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
      <svg width={size} height={size} style={{ overflow: "visible" }}>
        {segs.map((s) => {
          const active = sel === s.i;
          const dim = sel !== null && !active;
          const color = s.c.color || PALETTE[s.i % PALETTE.length];
          const w = active ? W + 7 : W;
          return (
            <path key={s.c.category_id} d={arc(cx, cy, active ? R + 3 : R, s.start, s.end, w)}
              fill={color} opacity={dim ? 0.28 : 1}
              style={{ transition: "opacity .25s, d .25s", cursor: "pointer" }}
              onClick={() => {
                haptic("medium");
                if (sel === s.i) { onOpen?.(s.c.category_id); }
                else setSel(s.i);
              }} />
          );
        })}
        <text x={cx} y={cy - 8} textAnchor="middle" fontSize="22" fontWeight="700"
          fill="var(--ink)" style={{ letterSpacing: "-0.5px" }}>{centerMain}</text>
        <text x={cx} y={cy + 14} textAnchor="middle" fontSize="12.5" fill="var(--sub)">{centerSub}</text>
        {centerPct && <text x={cx} y={cy + 33} textAnchor="middle" fontSize="12" fontWeight="700"
          fill="var(--gold)">{centerPct}</text>}
      </svg>

      <div className="list" style={{ width: "100%", marginTop: 8 }}>
        {items.map((c, i) => (
          <button key={c.category_id} className="item" style={{ textAlign: "left", width: "100%" }}
            onClick={() => { haptic("light"); setSel(sel === i ? null : i); }}>
            <span className="dot" style={{ background: c.color || PALETTE[i % PALETTE.length] }} />
            <span className="grow" style={{ fontWeight: 600, fontSize: 14.5,
              color: sel === null || sel === i ? "var(--ink)" : "var(--sub)" }}>{c.name}</span>
            <span className="sub" style={{ fontSize: 12 }}>{Math.round((c.total / sum) * 100)}%</span>
            <span className="amount" style={{ fontWeight: 650, fontSize: 14.5, minWidth: 70, textAlign: "right" }}>
              {money(c.total, currency)}</span>
          </button>
        ))}
      </div>
      {selected && onOpen && (
        <button className="btn btn-ghost btn-sm" style={{ marginTop: 12 }}
          onClick={() => onOpen(selected.category_id)}>{selected.name} →</button>
      )}
    </div>
  );
}
