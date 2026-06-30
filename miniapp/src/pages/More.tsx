import type { Nav } from "../App";
import { useStore } from "../lib/store";
import { money } from "../lib/format";
import { t } from "../i18n";
import { Header } from "../components/ui";
import {
  IRepeat, IShield, ITarget, IPiggy, IUsers, ITrophy, ISpark, IGear, IChevron, IPremium, IGrid,
} from "../components/icons";

export function More({ nav }: { nav: Nav }) {
  const { me } = useStore();
  const rows = [
    { key: "subscriptions", label: t("subscriptions"), Icon: IRepeat },
    { key: "habits", label: t("habits"), Icon: IShield },
    { key: "goals", label: t("goals"), Icon: ITarget },
    { key: "stash", label: t("stash"), Icon: IPiggy },
    { key: "family", label: t("family"), Icon: IUsers },
    { key: "achievements", label: t("achievements"), Icon: ITrophy },
    { key: "insights", label: t("insights"), Icon: ISpark },
    { key: "categories", label: t("manage_categories"), Icon: IGrid },
    { key: "settings", label: t("settings"), Icon: IGear },
  ];

  return (
    <div className="stack">
      <Header title={t("more")} />

      {!me!.is_premium ? (
        <button className="card" style={{ background: "linear-gradient(135deg,#1f2330,#14161f)", color: "#fff", textAlign: "left" }}
          onClick={() => nav("settings")}>
          <div className="row"><IPremium color="var(--gold-soft)" />
            <div className="grow">
              <div style={{ fontWeight: 700, fontSize: 16 }}>NEBANK Premium</div>
              <div style={{ opacity: .7, fontSize: 13 }}>{t("go_premium")}</div>
            </div>
            <IChevron color="rgba(255,255,255,.6)" />
          </div>
        </button>
      ) : (
        <div className="card" style={{ background: "linear-gradient(135deg,#fbf6e6,#fff)" }}>
          <div className="row"><IPremium color="var(--gold)" />
            <div className="grow"><div style={{ fontWeight: 700 }}>{t("premium_active")}</div>
              <div className="sub">{me!.premium_until?.slice(0, 10)}</div></div>
          </div>
        </div>
      )}

      {me!.stash_enabled && (
        <button className="card between" style={{ width: "100%" }} onClick={() => nav("stash")}>
          <div className="row"><span className="swatch" style={{ background: "#C9A2271f" }}><IPiggy width={20} height={20} color="var(--gold)" /></span>
            <span style={{ fontWeight: 650 }}>{t("stash")}</span></div>
          <span className="amount" style={{ fontWeight: 700 }}>{money(me!.stash_balance, me!.base_currency)}</span>
        </button>
      )}

      <div className="card" style={{ padding: 4 }}>
        <div className="list">
          {rows.map(({ key, label, Icon }) => (
            <button key={key} className="item" style={{ width: "100%", textAlign: "left", padding: "14px 12px" }}
              onClick={() => nav(key)}>
              <span className="swatch" style={{ background: "var(--bg-2)" }}><Icon width={20} height={20} color="var(--ink-2)" /></span>
              <span className="grow" style={{ fontWeight: 600, fontSize: 15 }}>{label}</span>
              <IChevron width={18} height={18} color="var(--sub)" />
            </button>
          ))}
        </div>
      </div>

      <div className="sub" style={{ textAlign: "center", marginTop: 6 }}>
        <span className="brand-wordmark">NEBANK</span> · v1.0
      </div>
    </div>
  );
}
