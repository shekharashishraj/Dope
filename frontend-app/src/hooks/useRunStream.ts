/**
 * Hook to subscribe to backend run events (SSE/WS).
 * Currently the backend does not expose an SSE endpoint; the pipeline runner
 * updates RunState directly via sequential REST calls.
 * When the backend adds e.g. GET /runs/:runId/stream, implement EventSource here
 * and dispatch RUN_STARTED, STEP_STARTED, STEP_PROGRESS, STEP_COMPLETED,
 * STEP_FAILED, ARTIFACT_CREATED, RUN_COMPLETED, LOG_LINE to the RunState context.
 */
export function useRunStream(_runId: string | undefined): void {
  // No-op until backend supports SSE. Pipeline runner drives state via REST.
}
