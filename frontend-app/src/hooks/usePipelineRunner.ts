import { useCallback } from "react";
import { toast } from "sonner";
import * as api from "../lib/api";
import { useRunState } from "../context/RunStateContext";
import { createInitialRunState, type StepId } from "../lib/types";

function inferArtifactType(name: string): "pdf" | "tex" | "json" | "zip" {
  const lower = name.toLowerCase();
  if (lower.endsWith(".pdf")) return "pdf";
  if (lower.endsWith(".tex")) return "tex";
  if (lower.endsWith(".json")) return "json";
  if (lower.endsWith(".zip")) return "zip";
  return "json";
}

export function usePipelineRunner() {
  const {
    state,
    files,
    setState,
    setRunId,
    setStatus,
    setRunStartedAt,
    updateStep,
    addArtifact,
    pushStatus,
    pushLog,
    setEvaluationMetrics,
    setEvaluationData,
  } = useRunState();

  const runPipeline = useCallback(async () => {
    if (!files.pdf) {
      toast.error("Upload a PDF to continue.");
      return;
    }
    if (state.config.attacks.length === 0) {
      toast.error("Choose at least one shielding method to continue.");
      return;
    }
    if (state.status === "running") return;

    const initial = createInitialRunState();
    initial.config = { ...state.config };
    initial.devMode = state.devMode;
    setState(initial);
    setRunId(undefined);
    setStatus("running");
    setRunStartedAt(Date.now());
    toast.info("Pipeline started. Open the Pipeline Run tab to watch progress, or Results when complete.");

    pushStatus("PDF uploaded");
    pushLog({
      ts: new Date().toISOString(),
      level: "info",
      msg: "Starting pipeline",
      meta: { methods: state.config.attacks, compile: true },
    });

    const runIdRef = { current: "" };

    try {
      // --- Ingest ---
      updateStep("ingest", { status: "running", summary: "Uploading..." });
      const formData = new FormData();
      formData.append("pdf", files.pdf);
      if (files.answer) formData.append("answer_key", files.answer);
      const ingestRes = await api.ingest(formData);
      runIdRef.current = ingestRes.run_id;
      setRunId(ingestRes.run_id);
      updateStep("ingest", {
        status: "done",
        summary: ingestRes.detail ?? "Upload complete",
        raw: ingestRes,
      });
      pushStatus(ingestRes.detail ?? "Upload complete");
      pushLog({ ts: new Date().toISOString(), level: "info", msg: "Ingest complete", meta: ingestRes });
      toast.success("Ingest complete");

      // --- Extract ---
      updateStep("extract", { status: "running", summary: "Extracting document..." });
      const extractRes = await api.extract(ingestRes.run_id);
      const extractDetail = extractRes.detail ?? "Extraction complete";
      updateStep("extract", {
        status: "done",
        summary: extractDetail,
        outputs: [
          { label: "Document", value: extractRes.document_path },
          { label: "LaTeX", value: extractRes.latex_path },
          { label: "Questions", value: extractDetail.replace(/\D/g, "") || "--" },
        ],
        raw: extractRes,
      });
      pushStatus(extractDetail);
      pushLog({ ts: new Date().toISOString(), level: "info", msg: "Extract complete", meta: extractRes });
      addArtifact({
        stageId: "extract",
        name: extractRes.document_path?.split("/").pop() ?? "document.json",
        type: "json",
      });
      addArtifact({
        stageId: "extract",
        name: extractRes.latex_path?.split("/").pop() ?? "document.tex",
        type: "tex",
      });
      toast.success("Extract complete");

      // --- Perturb (plan) ---
      updateStep("plan", { status: "running", summary: "Generating perturbations..." });
      const perturbRes = await api.perturb(ingestRes.run_id);
      const planDetail = perturbRes.detail ?? "Perturbations ready";
      const progress = perturbRes.stats
        ? { current: perturbRes.stats.perturbations, total: perturbRes.stats.perturbations }
        : undefined;
      updateStep("plan", {
        status: "done",
        summary: planDetail,
        progress,
        raw: perturbRes,
      });
      pushStatus(planDetail);
      pushLog({ ts: new Date().toISOString(), level: "info", msg: "Perturb complete", meta: perturbRes });
      const pertPath = perturbRes.perturbation_jsons?.[0];
      if (pertPath) {
        addArtifact({
          stageId: "plan",
          name: pertPath.split("/").pop() ?? "perturbations.json",
          type: "json",
        });
      }
      toast.success("Perturbations ready");

      // --- Inject (+ compile) ---
      updateStep("inject", {
        status: "running",
        summary: "Injecting and compiling...",
      });
      const injectRes = await api.inject(
        ingestRes.run_id,
        state.config.attacks,
        true
      );
      updateStep("inject", {
        status: "done",
        summary: injectRes.detail ?? "Injection complete",
        raw: injectRes,
      });
      pushStatus(injectRes.detail ?? "Injection complete");
      pushLog({ ts: new Date().toISOString(), level: "info", msg: "Inject complete", meta: injectRes });

      const compileSummary =
        injectRes.summary?.compiled_pdfs != null
          ? `Compiled ${injectRes.summary.compiled_pdfs} PDFs`
          : injectRes.compile_pdf_effective
          ? "Compilation done"
          : "Compilation skipped";
      updateStep("compile", { status: "done", summary: compileSummary });

      injectRes.artifacts?.forEach((a) => {
        addArtifact({
          stageId: "inject",
          name: a.value?.split("/").pop() ?? a.label,
          type: inferArtifactType(a.value ?? ""),
          url: a.value,
        });
      });
      toast.success("Injection complete");

      // --- Evaluate ---
      updateStep("eval", { status: "running", summary: "Running evaluation..." });
      const evalRes = await api.evaluate(ingestRes.run_id);
      const summary = evalRes.metrics?.summary ?? evalRes.metrics ?? undefined;
      setEvaluationMetrics(
        summary && typeof summary === "object" && !Array.isArray(summary)
          ? (summary as Record<string, number | string>)
          : undefined
      );
      setEvaluationData({
        metrics: evalRes.metrics ?? {},
        sample_results: evalRes.sample_results,
      });
      updateStep("eval", {
        status: "done",
        summary: evalRes.detail ?? "Evaluation complete",
        raw: evalRes,
      });
      pushStatus(evalRes.detail ?? "Evaluation complete");
      pushLog({ ts: new Date().toISOString(), level: "info", msg: "Evaluate complete", meta: evalRes });
      addArtifact({
        stageId: "eval",
        name: evalRes.report_path?.split("/").pop() ?? "report.txt",
        type: "json",
        url: evalRes.report_path,
      });
      toast.success("Pipeline complete");
      setStatus("done");
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      pushLog({ ts: new Date().toISOString(), level: "error", msg: message, meta: err });
      toast.error(message);
      setStatus("failed");
      const stepFromError = (): StepId => {
        if (message.includes("Ingest") || message.includes("Upload")) return "ingest";
        if (message.includes("Extract")) return "extract";
        if (message.includes("Perturb")) return "plan";
        if (message.includes("Inject")) return "inject";
        if (message.includes("Evaluate")) return "eval";
        return "ingest";
      };
      updateStep(stepFromError(), { status: "failed", summary: message });
    }
  }, [
    files.pdf,
    files.answer,
    state.config,
    state.status,
    state.devMode,
    setState,
    setRunId,
    setStatus,
    setRunStartedAt,
    updateStep,
    addArtifact,
    pushStatus,
    pushLog,
    setEvaluationMetrics,
    setEvaluationData,
  ]);

  return { runPipeline };
}
