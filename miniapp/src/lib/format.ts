// Currency / number formatting (mirrors backend rules).
const SYM: Record<string, string> = {
  USD: "$", EUR: "€", GBP: "£", RUB: "₽", JPY: "¥", CNY: "¥", TRY: "₺",
  UAH: "₴", KZT: "₸", GEL: "₾", AED: "د.إ", INR: "₹", KRW: "₩", BRL: "R$",
};
const ZERO_DEC = new Set(["JPY", "KRW", "VND", "IDR", "CLP", "HUF", "ISK"]);
const CRYPTO = new Set(["BTC", "ETH", "USDT", "TRX"]);

export function decimals(code: string): number {
  if (code === "BTC" || code === "ETH") return 8;
  if (code === "USDT" || code === "TRX") return 6;
  if (ZERO_DEC.has(code)) return 0;
  return 2;
}

export function money(amount: number, code: string, opts: { sign?: boolean } = {}): string {
  const d = decimals(code);
  if (CRYPTO.has(code)) {
    const s = amount.toFixed(d).replace(/\.?0+$/, "");
    return `${s} ${code}`;
  }
  const n = Math.abs(amount).toLocaleString("en-US", {
    minimumFractionDigits: d, maximumFractionDigits: d,
  }).replace(/,/g, " ");
  const sym = SYM[code];
  const body = sym && sym.length === 1 ? `${sym}${n}` : `${n} ${code}`;
  const prefix = opts.sign ? (amount < 0 ? "−" : "+") + " " : (amount < 0 ? "−" : "");
  return prefix + body;
}

export function compact(amount: number, code: string): string {
  const abs = Math.abs(amount);
  const sym = SYM[code] ?? "";
  let s: string;
  if (abs >= 1_000_000) s = (amount / 1_000_000).toFixed(1).replace(/\.0$/, "") + "M";
  else if (abs >= 1000) s = (amount / 1000).toFixed(1).replace(/\.0$/, "") + "K";
  else s = String(Math.round(amount));
  return sym && sym.length === 1 ? `${sym}${s}` : `${s} ${code}`;
}

export function pct(v: number | null): string {
  if (v === null || v === undefined) return "—";
  return `${v > 0 ? "+" : ""}${v.toFixed(1)}%`;
}

export function fmtDate(iso: string, lang: string): string {
  const d = new Date(iso + (iso.length === 10 ? "T00:00:00" : ""));
  return d.toLocaleDateString(lang === "ru" ? "ru-RU" : "en-US", { day: "numeric", month: "short" });
}
