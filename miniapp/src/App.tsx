import { useState } from "react";
import { useStore } from "./lib/store";
import { TabBar } from "./components/TabBar";
import { Skeleton } from "./components/ui";
import { Dashboard } from "./pages/Dashboard";
import { History } from "./pages/History";
import { Budgets } from "./pages/Budgets";
import { Rates } from "./pages/Rates";
import { More } from "./pages/More";
import { Subscriptions } from "./pages/Subscriptions";
import { Habits } from "./pages/Habits";
import { Goals } from "./pages/Goals";
import { Stash } from "./pages/Stash";
import { Family } from "./pages/Family";
import { Achievements } from "./pages/Achievements";
import { Insights } from "./pages/Insights";
import { Settings } from "./pages/Settings";
import { Categories } from "./pages/Categories";

export type Route = { name: string; params?: Record<string, string> };
export type Nav = (name: string, params?: Record<string, string>) => void;

const MAIN_TABS = ["home", "history", "budgets", "rates", "more"];

export default function App() {
  const { me } = useStore();
  const [route, setRoute] = useState<Route>({ name: "home" });
  const nav: Nav = (name, params) => { window.scrollTo(0, 0); setRoute({ name, params }); };

  if (!me) {
    return (
      <div className="app">
        <div className="stack" style={{ marginTop: 20 }}>
          <Skeleton h={40} w={180} />
          <Skeleton h={150} r={20} />
          <Skeleton h={260} r={20} />
        </div>
      </div>
    );
  }

  const page = (() => {
    switch (route.name) {
      case "home": return <Dashboard nav={nav} />;
      case "history": return <History nav={nav} params={route.params} />;
      case "budgets": return <Budgets nav={nav} />;
      case "rates": return <Rates nav={nav} />;
      case "more": return <More nav={nav} />;
      case "subscriptions": return <Subscriptions nav={nav} />;
      case "habits": return <Habits nav={nav} />;
      case "goals": return <Goals nav={nav} />;
      case "stash": return <Stash nav={nav} />;
      case "family": return <Family nav={nav} />;
      case "achievements": return <Achievements nav={nav} />;
      case "insights": return <Insights nav={nav} />;
      case "settings": return <Settings nav={nav} />;
      case "categories": return <Categories nav={nav} />;
      default: return <Dashboard nav={nav} />;
    }
  })();

  const activeTab = MAIN_TABS.includes(route.name) ? route.name : "more";

  return (
    <div className="app">
      {page}
      <TabBar active={activeTab} onSelect={(k) => nav(k)} />
    </div>
  );
}
