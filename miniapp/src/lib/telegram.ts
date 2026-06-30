// Telegram WebApp SDK wrapper.
type TG = any;

export function tg(): TG | null {
  return (window as any).Telegram?.WebApp ?? null;
}

export function initData(): string {
  return tg()?.initData ?? "";
}

export function tgUserLang(): "ru" | "en" {
  const code = tg()?.initDataUnsafe?.user?.language_code ?? "en";
  return code.startsWith("ru") ? "ru" : "en";
}

export function ready(): void {
  const w = tg();
  if (!w) return;
  try {
    w.ready();
    w.expand();
    // Keep header/background light per TZ §17.
    w.setHeaderColor?.("#FFFFFF");
    w.setBackgroundColor?.("#F5F6F8");
    w.disableVerticalSwipes?.();
  } catch { /* noop */ }
}

export function haptic(kind: "light" | "medium" | "soft" | "rigid" = "light"): void {
  try { tg()?.HapticFeedback?.impactOccurred?.(kind); } catch { /* noop */ }
}

export function notify(kind: "success" | "warning" | "error"): void {
  try { tg()?.HapticFeedback?.notificationOccurred?.(kind); } catch { /* noop */ }
}

export function openInvoice(url: string): Promise<string> {
  return new Promise((resolve) => {
    const w = tg();
    if (!w?.openInvoice) { resolve("failed"); return; }
    w.openInvoice(url, (status: string) => resolve(status));
  });
}

export function shareLink(url: string, text: string): void {
  const w = tg();
  const share = `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`;
  if (w?.openTelegramLink) w.openTelegramLink(share);
  else window.open(share, "_blank");
}
