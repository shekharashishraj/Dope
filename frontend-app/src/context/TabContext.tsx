import { createContext, useContext, useState, type ReactNode } from "react";

export type AppTab = "main" | "pipeline" | "results";

const TabContext = createContext<{
  activeTab: AppTab;
  setActiveTab: (tab: AppTab) => void;
} | null>(null);

export function TabProvider({ children }: { children: ReactNode }) {
  const [activeTab, setActiveTab] = useState<AppTab>("main");
  return (
    <TabContext.Provider value={{ activeTab, setActiveTab }}>
      {children}
    </TabContext.Provider>
  );
}

export function useTab() {
  const ctx = useContext(TabContext);
  if (!ctx) throw new Error("useTab must be used within TabProvider");
  return ctx;
}
