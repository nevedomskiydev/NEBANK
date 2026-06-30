import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "./api";
import type { Me } from "./types";
import { setLang, type Lang } from "../i18n";

interface Ctx {
  me: Me | null;
  refresh: () => Promise<void>;
  update: (patch: Partial<Me> & Record<string, unknown>) => Promise<void>;
}
const StoreCtx = createContext<Ctx>({ me: null, refresh: async () => {}, update: async () => {} });

export function StoreProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);

  async function refresh() {
    const data = await api.get<Me>("/me");
    setLang(data.language as Lang);
    setMe(data);
  }
  async function update(patch: Partial<Me> & Record<string, unknown>) {
    const data = await api.patch<Me>("/me", patch);
    setLang(data.language as Lang);
    setMe(data);
  }
  useEffect(() => { refresh().catch(() => {}); }, []);

  return <StoreCtx.Provider value={{ me, refresh, update }}>{children}</StoreCtx.Provider>;
}

export const useStore = () => useContext(StoreCtx);
