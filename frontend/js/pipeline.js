import { log } from "./logger.js";
import { addArtifact, setMetrics, setStatus, updateStepStatus } from "./ui.js";

const ALL_ATTACK_METHODS_COUNT = 5;

const formatRisk = (detectionRate) => {
  if (typeof detectionRate !== "number") return "--";
  if (detectionRate >= 70) return "High";
  if (detectionRate >= 40) return "Medium";
  return "Low";
};

async function postForm(url, formData) {
  const response = await fetch(url, { method: "POST", body: formData });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`HTTP ${response.status}: ${text}`);
  }
  return response.json();
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`HTTP ${response.status}: ${text}`);
  }
  return response.json();
}

export async function runLivePipeline(files, config, methods = [], compilePdf = true) {
  setStatus("Running pipeline");
  log("info", "Starting live pipeline", { endpoint: config?.endpoint || "", methods });

  if (!config?.endpoint) {
    log("error", "Backend endpoint not configured", { hint: "Set endpoint in js/config.js" });
    updateStepStatus("ingest", "error", "No backend endpoint configured");
    setStatus("Error");
    return;
  }

  try {
    const formData = new FormData();
    if (files.pdf) formData.append("pdf", files.pdf);
    if (files.answer) formData.append("answer_key", files.answer);

    updateStepStatus("ingest", "running", "Uploading PDF and answer key");
    const ingestPayload = await postForm(`${config.endpoint}/ingest`, formData);
    log("info", "Ingest complete", ingestPayload);
    updateStepStatus("ingest", "done", ingestPayload.detail || "Upload complete");

    updateStepStatus("extract", "running", "Extracting document and building LaTeX");
    const extractPayload = await postJson(`${config.endpoint}/extract`, {
      run_id: ingestPayload.run_id,
    });
    log("info", "Extract complete", extractPayload);
    updateStepStatus("extract", "done", extractPayload.detail || "Extraction complete");
    if (extractPayload.document_path) addArtifact("Document", extractPayload.document_path);
    if (extractPayload.latex_path) addArtifact("LaTeX", extractPayload.latex_path);

    updateStepStatus("perturb", "running", "Resolving perturbation plan");
    const perturbPayload = await postJson(`${config.endpoint}/perturb`, {
      run_id: ingestPayload.run_id,
    });
    log("info", "Perturbation ready", perturbPayload);
    updateStepStatus("perturb", "done", perturbPayload.detail || "Perturbations loaded");
    addArtifact("Perturbations", perturbPayload.perturbation_jsons?.[0] || "perturbations.json");

    const compilingLabel = compilePdf ? "Injecting attacks and compiling PDFs" : "Injecting attacks (compilation disabled)";
    updateStepStatus("inject", "running", compilingLabel);
    const injectPayload = await postJson(`${config.endpoint}/inject`, {
      run_id: ingestPayload.run_id,
      methods,
      compile_pdf: !!compilePdf,
    });
    log("info", "Injection complete", injectPayload.summary || {});
    updateStepStatus("inject", "done", injectPayload.detail || "Injection complete");

    const summary = injectPayload.summary || {};
    if (summary.compiled_pdfs > 0) {
      updateStepStatus("compile", "done", `Compiled ${summary.compiled_pdfs} PDFs`);
    } else if (injectPayload.compile_pdf_effective === false) {
      const reason =
        injectPayload.compile_pdf_requested === false
          ? "Compilation disabled in UI; only LaTeX generated"
          : "Compilation disabled by server configuration; only LaTeX generated";
      updateStepStatus("compile", "done", reason);
    } else if ((summary.failed_compilation_methods || []).length > 0) {
      const failed = summary.failed_compilation_methods.join(", ");
      updateStepStatus("compile", "error", `Compilation failed for: ${failed}`);
    } else if ((summary.skipped_compilation_methods || []).length > 0) {
      const skipped = summary.skipped_compilation_methods.join(", ");
      updateStepStatus("compile", "error", `No PDFs compiled (skipped for: ${skipped})`);
    } else {
      updateStepStatus("compile", "error", "No PDFs compiled");
    }

    (injectPayload.artifacts || []).forEach((artifact) => {
      addArtifact(artifact.label, artifact.value);
    });

    updateStepStatus("evaluate", "running", "Running detector checks");
    const evalPayload = await postJson(`${config.endpoint}/evaluate`, {
      run_id: ingestPayload.run_id,
    });
    log("info", "Evaluation complete", evalPayload.metrics || {});
    updateStepStatus("evaluate", "done", evalPayload.detail || "Evaluation complete");
    addArtifact("Evaluation Report", evalPayload.report_path || "detection_report.txt");

    const risk = formatRisk(evalPayload.metrics?.detection_rate);
    const selectedAttack =
      methods.length === ALL_ATTACK_METHODS_COUNT ? "All" : String(methods.length);
    setMetrics({
      risk,
      perturbations: perturbPayload.stats?.perturbations ?? "--",
      selectedAttack,
    });

    setStatus("Complete");
  } catch (error) {
    log("error", "Live pipeline failed", { error: error.message });
    const stepFromError = (msg) => {
      if (msg.includes("ingest") || msg.includes("Upload")) return "ingest";
      if (msg.includes("extract") || msg.includes("Extract")) return "extract";
      if (msg.includes("perturb")) return "perturb";
      if (msg.includes("inject")) return "inject";
      if (msg.includes("evaluate")) return "evaluate";
      return "ingest";
    };
    const step = stepFromError(error.message);
    updateStepStatus(step, "error", error.message || "Request failed");
    setStatus("Error");
  }
}
