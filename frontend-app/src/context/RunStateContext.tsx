import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  createInitialRunState,
  type EvaluationData,
  type RunState,
  type StepId,
} from "../lib/types";

type StepUpdate = Partial<RunState["steps"][number]>;

interface RunStateContextValue {
  state: RunState;
  /** Files to send to ingest (not stored in RunState) */
  files: { pdf: File | null; answer: File | null };
  setPdfFile: (file: File | null) => void;
  setAnswerFile: (file: File | null) => void;
  setDevMode: (on: boolean) => void;
  setConfig: (patch: Partial<RunState["config"]>) => void;
  updateStep: (stepId: StepId, update: StepUpdate) => void;
  addArtifact: (artifact: RunState["artifacts"][number]) => void;
  pushStatus: (msg: string) => void;
  pushLog: (entry: RunState["logs"][number]) => void;
  setRunId: (id: string | undefined) => void;
  setStatus: (status: RunState["status"]) => void;
  setEvaluationMetrics: (m: Record<string, number | string> | undefined) => void;
  setEvaluationData: (d: EvaluationData | undefined) => void;
  setRunStartedAt: (t: number | undefined) => void;
  reset: () => void;
  /** Replace full state (e.g. when starting a run) */
  setState: (s: RunState | ((prev: RunState) => RunState)) => void;
}

const RunStateContext = createContext<RunStateContextValue | null>(null);

export function RunStateProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<RunState>(createInitialRunState);
  const [files, setFiles] = useState<{ pdf: File | null; answer: File | null }>({
    pdf: null,
    answer: null,
  });

  const setPdfFile = useCallback((file: File | null) => {
    setFiles((prev) => ({ ...prev, pdf: file }));
  }, []);
  const setAnswerFile = useCallback((file: File | null) => {
    setFiles((prev) => ({ ...prev, answer: file }));
    setState((prev) => ({ ...prev, config: { ...prev.config, answerKeyProvided: !!file } }));
  }, []);

  const setDevMode = useCallback((on: boolean) => {
    setState((prev) => ({ ...prev, devMode: on }));
  }, []);

  const setConfig = useCallback((patch: Partial<RunState["config"]>) => {
    setState((prev) => ({
      ...prev,
      config: { ...prev.config, ...patch },
    }));
  }, []);

  const updateStep = useCallback((stepId: StepId, update: StepUpdate) => {
    setState((prev) => ({
      ...prev,
      steps: prev.steps.map((s) =>
        s.id === stepId ? { ...s, ...update } : s
      ),
    }));
  }, []);

  const addArtifact = useCallback((artifact: RunState["artifacts"][number]) => {
    setState((prev) => ({
      ...prev,
      artifacts: [...prev.artifacts, artifact],
    }));
  }, []);

  const pushStatus = useCallback((msg: string) => {
    const ts = new Date().toISOString();
    setState((prev) => ({
      ...prev,
      statusFeed: [...prev.statusFeed.slice(-9), { ts, msg }],
    }));
  }, []);

  const pushLog = useCallback((entry: RunState["logs"][number]) => {
    setState((prev) => ({
      ...prev,
      logs: [...prev.logs, entry],
    }));
  }, []);

  const setRunId = useCallback((id: string | undefined) => {
    setState((prev) => ({ ...prev, runId: id }));
  }, []);

  const setStatus = useCallback((status: RunState["status"]) => {
    setState((prev) => ({ ...prev, status }));
  }, []);

  const setEvaluationMetrics = useCallback(
    (m: Record<string, number | string> | undefined) => {
      setState((prev) => ({ ...prev, evaluationMetrics: m }));
    },
    []
  );

  const setEvaluationData = useCallback((d: EvaluationData | undefined) => {
    setState((prev) => ({ ...prev, evaluationData: d }));
  }, []);

  const setRunStartedAt = useCallback((t: number | undefined) => {
    setState((prev) => ({ ...prev, runStartedAt: t }));
  }, []);

  const reset = useCallback(() => {
    setState(createInitialRunState());
    setFiles({ pdf: null, answer: null });
  }, []);

  const value = useMemo<RunStateContextValue>(
    () => ({
      state,
      files,
      setPdfFile,
      setAnswerFile,
      setDevMode,
      setConfig,
      updateStep,
      addArtifact,
      pushStatus,
      pushLog,
      setRunId,
      setStatus,
      setEvaluationMetrics,
      setEvaluationData,
      setRunStartedAt,
      reset,
      setState,
    }),
    [
      state,
      files,
      setPdfFile,
      setAnswerFile,
      setDevMode,
      setConfig,
      updateStep,
      addArtifact,
      pushStatus,
      pushLog,
      setRunId,
      setStatus,
      setEvaluationMetrics,
      setEvaluationData,
      setRunStartedAt,
      reset,
    ]
  );

  return (
    <RunStateContext.Provider value={value}>
      {children}
    </RunStateContext.Provider>
  );
}

export function useRunState(): RunStateContextValue {
  const ctx = useContext(RunStateContext);
  if (!ctx) throw new Error("useRunState must be used within RunStateProvider");
  return ctx;
}
