import { Toaster } from "sonner";
import { RunStateProvider } from "./context/RunStateContext";
import { Dashboard } from "./pages/Dashboard";

function App() {
  return (
    <RunStateProvider>
      <Dashboard />
      <Toaster theme="dark" position="top-right" />
    </RunStateProvider>
  );
}

export default App;
