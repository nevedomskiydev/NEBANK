// Minimal stroke icons. No emoji (TZ §17).
import type { SVGProps } from "react";

const base = (p: SVGProps<SVGSVGElement>) => ({
  width: 24, height: 24, viewBox: "0 0 24 24", fill: "none",
  stroke: "currentColor", strokeWidth: 1.7, strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const, ...p,
});

export const IHome = (p: SVGProps<SVGSVGElement>) => (
  <svg {...base(p)}><path d="M3 10.5 12 3l9 7.5" /><path d="M5 9.5V20h14V9.5" /><path d="M9.5 20v-6h5v6" /></svg>
);
export const IHistory = (p: SVGProps<SVGSVGElement>) => (
  <svg {...base(p)}><path d="M3.5 12a8.5 8.5 0 1 0 2.5-6" /><path d="M5 4v4h4" /><path d="M12 8v4l3 2" /></svg>
);
export const IBudget = (p: SVGProps<SVGSVGElement>) => (
  <svg {...base(p)}><rect x="3" y="5" width="18" height="14" rx="3" /><path d="M3 10h18" /><circle cx="16.5" cy="14.5" r="1.3" fill="currentColor" stroke="none" /></svg>
);
export const IRates = (p: SVGProps<SVGSVGElement>) => (
  <svg {...base(p)}><path d="M4 16l4-5 3 3 5-7" /><path d="M16 7h3v3" /><path d="M4 20h16" /></svg>
);
export const IMore = (p: SVGProps<SVGSVGElement>) => (
  <svg {...base(p)}><circle cx="5" cy="12" r="1.6" fill="currentColor" stroke="none" /><circle cx="12" cy="12" r="1.6" fill="currentColor" stroke="none" /><circle cx="19" cy="12" r="1.6" fill="currentColor" stroke="none" /></svg>
);
export const IChevron = (p: SVGProps<SVGSVGElement>) => (
  <svg {...base(p)}><path d="M9 6l6 6-6 6" /></svg>
);
export const IBack = (p: SVGProps<SVGSVGElement>) => (
  <svg {...base(p)}><path d="M15 6l-6 6 6 6" /></svg>
);
export const IPlus = (p: SVGProps<SVGSVGElement>) => (
  <svg {...base(p)}><path d="M12 5v14M5 12h14" /></svg>
);
export const ISearch = (p: SVGProps<SVGSVGElement>) => (
  <svg {...base(p)}><circle cx="11" cy="11" r="7" /><path d="M20 20l-3.5-3.5" /></svg>
);
export const ITrophy = (p: SVGProps<SVGSVGElement>) => (
  <svg {...base(p)}><path d="M7 4h10v4a5 5 0 0 1-10 0V4Z" /><path d="M7 6H4v1a3 3 0 0 0 3 3" /><path d="M17 6h3v1a3 3 0 0 1-3 3" /><path d="M9 20h6M12 13v4" /></svg>
);
export const ITarget = (p: SVGProps<SVGSVGElement>) => (
  <svg {...base(p)}><circle cx="12" cy="12" r="8" /><circle cx="12" cy="12" r="4" /><circle cx="12" cy="12" r="1" fill="currentColor" stroke="none" /></svg>
);
export const IShield = (p: SVGProps<SVGSVGElement>) => (
  <svg {...base(p)}><path d="M12 3l7 3v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3Z" /><path d="M9 12l2 2 4-4" /></svg>
);
export const IRepeat = (p: SVGProps<SVGSVGElement>) => (
  <svg {...base(p)}><path d="M4 9a6 6 0 0 1 10-3l2 2" /><path d="M20 15a6 6 0 0 1-10 3l-2-2" /><path d="M16 4v4h-4M8 20v-4h4" /></svg>
);
export const IPiggy = (p: SVGProps<SVGSVGElement>) => (
  <svg {...base(p)}><path d="M4 12a6 6 0 0 1 6-6h3a6 6 0 0 1 6 6 4 4 0 0 1-1.5 3v2h-2.5l-.5-1.2A6 6 0 0 1 10 16H8l-.6 1.5H5v-2.2A6 6 0 0 1 4 12Z" /><circle cx="9.5" cy="11" r="1" fill="currentColor" stroke="none" /></svg>
);
export const IUsers = (p: SVGProps<SVGSVGElement>) => (
  <svg {...base(p)}><circle cx="9" cy="8" r="3" /><path d="M3.5 19a5.5 5.5 0 0 1 11 0" /><path d="M16 6a3 3 0 0 1 0 5.5" /><path d="M16.5 14.5A5.5 5.5 0 0 1 20.5 19" /></svg>
);
export const IBell = (p: SVGProps<SVGSVGElement>) => (
  <svg {...base(p)}><path d="M6 9a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6Z" /><path d="M10 19a2 2 0 0 0 4 0" /></svg>
);
export const ISpark = (p: SVGProps<SVGSVGElement>) => (
  <svg {...base(p)}><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z" /></svg>
);
export const IGear = (p: SVGProps<SVGSVGElement>) => (
  <svg {...base(p)}><circle cx="12" cy="12" r="3" /><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2" /></svg>
);
export const IGrid = (p: SVGProps<SVGSVGElement>) => (
  <svg {...base(p)}><rect x="3.5" y="3.5" width="7" height="7" rx="2" /><rect x="13.5" y="3.5" width="7" height="7" rx="2" /><rect x="3.5" y="13.5" width="7" height="7" rx="2" /><rect x="13.5" y="13.5" width="7" height="7" rx="2" /></svg>
);
export const ICheck = (p: SVGProps<SVGSVGElement>) => (
  <svg {...base(p)}><path d="M5 12l4.5 4.5L19 7" /></svg>
);
export const ITrash = (p: SVGProps<SVGSVGElement>) => (
  <svg {...base(p)}><path d="M4 7h16M9 7V5h6v2M6 7l1 13h10l1-13" /></svg>
);
export const IPremium = (p: SVGProps<SVGSVGElement>) => (
  <svg {...base(p)}><path d="M4 8l4 3 4-6 4 6 4-3-1.5 11H5.5L4 8Z" /></svg>
);
