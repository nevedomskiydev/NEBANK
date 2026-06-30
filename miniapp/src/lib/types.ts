export interface Me {
  id: number; telegram_id: number; first_name: string | null;
  language: "ru" | "en"; base_currency: string; voice_lang: "ru" | "en";
  theme: string; onboarded: boolean; is_premium: boolean; premium_until: string | null;
  stash_enabled: boolean; stash_round_to: number; stash_balance: number;
  referral_code: string | null;
  currencies: { fiat: string[]; crypto: string[] };
}
export interface Tx {
  id: number; kind: "income" | "expense"; amount: number;
  original_amount: number; original_currency: string;
  title: string | null; category: string | null; category_id: number | null;
  category_color: string | null; source: string; occurred_at: string;
  crypto_network: string | null;
}
export interface CatAgg { category_id: number; name: string; color: string; total: number; count: number; }
export interface Dashboard {
  period: string; currency: string; income: number; expense: number; net: number;
  categories: CatAgg[]; trend: { date: string; amount: number }[]; recent: Tx[];
}
export interface Category { id: number; name: string; kind: string; color: string; icon: string; }
export interface Budget {
  id: number; category_id: number; name: string; color: string;
  limit: number; spent: number; progress: number; over: boolean;
}
export interface Subscription {
  id: number; name: string; amount: number; currency: string; period: string;
  next_charge: string; is_active: boolean; auto_detected: boolean;
}
export interface Habit {
  id: number; name: string; daily_cost: number; clean_days: number;
  best_streak: number; saved: number; started_at: string;
}
export interface Goal {
  id: number; name: string; target: number; current: number; progress: number; achieved: boolean;
}
export interface Achievement {
  code: string; title: string; description: string; target: number;
  value: number; progress: number; unlocked: boolean;
}
export interface Insights {
  current: { income: number; expense: number; net: number };
  previous: { income: number; expense: number; net: number };
  expense_change_pct: number | null; income_change_pct: number | null;
  forecast_expense: number; days_elapsed: number; days_total: number; currency: string;
}
export interface RateItem {
  symbol: string; price: number | null; vs: string; change_pct: number | null; spark: number[];
}
export interface Family {
  group: null | {
    id: number; name: string; invite_code: string; role: string;
    invite_link: string; members: { name: string; role: string }[];
  };
}
