import { Sheet, SheetContent, SheetHeader, SheetTitle } from "../ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { ScrollArea } from "../ui/scroll-area";
import { LogsViewer } from "./LogsViewer";
import { useRunState } from "../../context/RunStateContext";

interface DeveloperDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DeveloperDrawer({ open, onOpenChange }: DeveloperDrawerProps) {
  const { state } = useRunState();

  const copyLogs = () => {
    const text = state.logs
      .map(
        (e) =>
          `[${e.ts}] ${e.level.toUpperCase()} ${e.msg}${e.meta ? " " + JSON.stringify(e.meta) : ""}`
      )
      .join("\n");
    navigator.clipboard.writeText(text);
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex flex-col w-full sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>Developer</SheetTitle>
        </SheetHeader>
        <Tabs defaultValue="logs" className="flex-1 flex flex-col min-h-0">
          <TabsList>
            <TabsTrigger value="logs">Logs</TabsTrigger>
            <TabsTrigger value="trace">Trace JSON</TabsTrigger>
          </TabsList>
          <TabsContent value="logs" className="flex-1 min-h-0 mt-2">
            <LogsViewer logs={state.logs} onCopy={copyLogs} />
          </TabsContent>
          <TabsContent value="trace" className="flex-1 min-h-0 mt-2">
            <ScrollArea className="h-[60vh] rounded-md border border-[var(--card-border)] p-2 font-mono text-xs">
              <pre className="text-[var(--muted)] whitespace-pre-wrap">
                {JSON.stringify(
                  {
                    runId: state.runId,
                    status: state.status,
                    steps: state.steps,
                    artifacts: state.artifacts,
                  },
                  null,
                  2
                )}
              </pre>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </SheetContent>
    </Sheet>
  );
}
