import { Toaster } from "sonner";
import { RunStateProvider } from "./context/RunStateContext";
import { ThemeProvider, useTheme } from "./context/ThemeContext";
import { Dashboard } from "./pages/Dashboard";

function ThemedToaster() {
  const { theme } = useTheme();
  return <Toaster theme={theme} position="top-right" />;
}

function App() {
  return (
    <ThemeProvider>
      <RunStateProvider>
        <Dashboard />
        <ThemedToaster />
      </RunStateProvider>
    </ThemeProvider>
  );
}

export default App;
