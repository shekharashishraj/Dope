import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { ScrollArea } from "../ui/scroll-area";
import { useRunState } from "../../context/RunStateContext";

const MAX_FEED = 10;

export function StatusFeed() {
  const { state } = useRunState();
  const feed = state.statusFeed.slice(-MAX_FEED).reverse();

  if (feed.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Status</CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-32">
          <ul className="space-y-1 text-sm text-[var(--muted)]">
            {feed.map((item, i) => (
              <li key={i} className="flex gap-2">
                <span className="shrink-0 text-xs opacity-70">
                  {new Date(item.ts).toLocaleTimeString()}
                </span>
                <span>{item.msg}</span>
              </li>
            ))}
          </ul>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
