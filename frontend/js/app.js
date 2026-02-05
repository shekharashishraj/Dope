import { config } from "./config.js";
import { log, onLog, clearLogs, getLogs } from "./logger.js";
import { resetState, state } from "./state.js";
import { clearArtifacts, clearLogsView, resetSteps, setMetrics, setStatus, updateStepStatus, addArtifact, appendLog } from "./ui.js";
import { runLivePipeline } from "./pipeline.js";

const pdfInput = document.getElementById("pdf-input");
const answerInput = document.getElementById("answer-input");
const pdfMeta = document.getElementById("pdf-meta");
const answerMeta = document.getElementById("answer-meta");
const runBtn = document.getElementById("run-btn");
const resetBtn = document.getElementById("reset-btn");
const copyLogBtn = document.getElementById("copy-log");
const compileToggle = document.getElementById("compile-toggle");

function getSelectedMethods() {
  const selections = Array.from(document.querySelectorAll(".method-chip input:checked")).map(
    (input) => input.value
  );
  if (selections.length === 0) {
    log("warn", "No attack methods selected; defaulting to dual_layer");
    return ["dual_layer"];
  }
  return selections;
}

function updateFileMeta(input, metaEl, type) {
  if (input.files && input.files[0]) {
    const file = input.files[0];
    metaEl.textContent = `${file.name} (${Math.round(file.size / 1024)} KB)`;
    state.files[type] = file;
    log("info", `${type} uploaded`, { name: file.name, size: file.size });
  } else {
    metaEl.textContent = "No file selected";
    state.files[type] = null;
  }
}

pdfInput.addEventListener("change", () => updateFileMeta(pdfInput, pdfMeta, "pdf"));
answerInput.addEventListener("change", () => updateFileMeta(answerInput, answerMeta, "answer"));

onLog((entry) => appendLog(entry));

function resetUI() {
  resetState();
  clearArtifacts();
  clearLogs();
  clearLogsView();
  resetSteps();
  setMetrics({ risk: "--", perturbations: "--", selectedAttack: "--" });
  setStatus("Idle");
  pdfMeta.textContent = "No file selected";
  answerMeta.textContent = "No file selected";
  pdfInput.value = "";
  answerInput.value = "";
  if (compileToggle) {
    compileToggle.checked = true;
  }
}

async function runPipeline() {
  resetSteps();
  clearArtifacts();
  clearLogsView();
  getLogs().forEach((entry) => appendLog(entry));

  const methods = getSelectedMethods();
  const compilePdf = compileToggle ? compileToggle.checked : true;

  if (!state.files.pdf) {
    log("warn", "No PDF selected; upload a PDF to run the pipeline");
  }

  await runLivePipeline(state.files, config, methods, compilePdf);
}

runBtn.addEventListener("click", () => {
  runPipeline().catch((error) => {
    log("error", "Pipeline crashed", { error: error.message });
    updateStepStatus("ingest", "error", "Unhandled error" );
    setStatus("Error");
  });
});

resetBtn.addEventListener("click", resetUI);

copyLogBtn.addEventListener("click", async () => {
  const lines = getLogs().map((entry) => {
    const time = entry.time.toLocaleTimeString();
    const payload = entry.data ? ` | ${JSON.stringify(entry.data)}` : "";
    return `[${time}] ${entry.level.toUpperCase()} ${entry.message}${payload}`;
  });
  try {
    await navigator.clipboard.writeText(lines.join("\n"));
    log("info", "Logs copied to clipboard");
  } catch (error) {
    log("error", "Failed to copy logs", { error: error.message });
  }
});

setStatus("Idle");
addArtifact("Configured Output", "output_attacked_pdfs/<timestamp>/..." );
