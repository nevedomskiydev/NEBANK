import { haptic } from "../lib/telegram";
import { t } from "../i18n";
import { IHome, IHistory, IBudget, IRates, IMore } from "./icons";

const TABS = [
  { key: "home", label: "nav_home", Icon: IHome },
  { key: "history", label: "nav_history", Icon: IHistory },
  { key: "budgets", label: "nav_budgets", Icon: IBudget },
  { key: "rates", label: "nav_rates", Icon: IRates },
  { key: "more", label: "nav_more", Icon: IMore },
] as const;

export function TabBar({ active, onSelect }: { active: string; onSelect: (k: string) => void }) {
  return (
    <nav className="tabbar">
      <div className="tabbar-inner">
        {TABS.map(({ key, label, Icon }) => (
          <button key={key} className={`tab ${active === key ? "active" : ""}`}
            onClick={() => { haptic("light"); onSelect(key); }}>
            <Icon />
            <span>{t(label)}</span>
          </button>
        ))}
      </div>
    </nav>
  );
}
