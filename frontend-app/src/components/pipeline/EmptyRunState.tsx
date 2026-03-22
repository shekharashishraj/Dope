import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { useTab } from "../../context/TabContext";
import { Play } from "lucide-react";

export function EmptyRunState() {
  const { setActiveTab } = useTab();

  return (
    <Card className="max-w-md mx-auto">
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Play className="h-5 w-5 text-[var(--muted)]" aria-hidden />
          No active pipeline run
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-[var(--muted)]">
          Start the shielding workflow from the Main tab to process the uploaded
          assessment and generate results.
        </p>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setActiveTab("main")}
          className="rounded-lg"
        >
          Go to Main
        </Button>
      </CardContent>
    </Card>
  );
}
