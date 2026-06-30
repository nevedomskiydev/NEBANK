import type { ReactNode } from "react";
import { useEffect } from "react";
import { haptic } from "../lib/telegram";
import { IBack } from "./icons";

export function Segmented<T extends string>({ value, options, onChange }:
  { value: T; options: { value: T; label: string }[]; onChange: (v: T) => void }) {
  return (
    <div className="segmented" role="tablist">
      {options.map((o) => (
        <button key={o.value} className={o.value === value ? "active" : ""}
          onClick={() => { haptic("light"); onChange(o.value); }}>{o.label}</button>
      ))}
    </div>
  );
}

export function Header({ title, sub, onBack, right }:
  { title: string; sub?: string; onBack?: () => void; right?: ReactNode }) {
  return (
    <div className="between" style={{ margin: "6px 2px 16px" }}>
      <div className="row" style={{ gap: 10 }}>
        {onBack && (
          <button className="swatch" style={{ background: "var(--bg-2)" }}
            onClick={() => { haptic("light"); onBack(); }} aria-label="back">
            <IBack width={20} height={20} />
          </button>
        )}
        <div>
          <h1 className="h1">{title}</h1>
          {sub && <div className="sub" style={{ marginTop: 2 }}>{sub}</div>}
        </div>
      </div>
      {right}
    </div>
  );
}

export function ProgressRing({ progress, size = 56, stroke = 6, color = "var(--gold)", track = "var(--bg-2)", children }:
  { progress: number; size?: number; stroke?: number; color?: string; track?: string; children?: ReactNode }) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const off = c * (1 - Math.max(0, Math.min(1, progress)));
  return (
    <div style={{ position: "relative", width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle cx={size / 2} cy={size / 2} r={r} stroke={track} strokeWidth={stroke} fill="none" />
        <circle cx={size / 2} cy={size / 2} r={r} stroke={color} strokeWidth={stroke} fill="none"
          strokeDasharray={c} strokeDashoffset={off} strokeLinecap="round"
          style={{ transition: "stroke-dashoffset .7s cubic-bezier(.2,.8,.2,1)" }} />
      </svg>
      <div style={{ position: "absolute", inset: 0, display: "grid", placeItems: "center" }}>{children}</div>
    </div>
  );
}

export function Sheet({ onClose, children }: { onClose: () => void; children: ReactNode }) {
  useEffect(() => {
    const h = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [onClose]);
  return (
    <div className="scrim" onClick={onClose}>
      <div className="sheet" onClick={(e) => e.stopPropagation()}>
        <div className="sheet-grip" />
        {children}
      </div>
    </div>
  );
}

export function Skeleton({ h = 18, w = "100%", r = 10, style = {} }:
  { h?: number; w?: number | string; r?: number; style?: React.CSSProperties }) {
  return <div className="skeleton" style={{ height: h, width: w, borderRadius: r, ...style }} />;
}

export function Empty({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="empty">
      <div style={{ fontWeight: 650, color: "var(--ink-2)", marginBottom: 6 }}>{title}</div>
      {hint && <div style={{ fontSize: 13 }}>{hint}</div>}
    </div>
  );
}

export function Field(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input className="field" {...props} />;
}
