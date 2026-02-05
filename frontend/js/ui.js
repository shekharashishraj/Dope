const stepList = document.getElementById("step-list");
const artifactList = document.getElementById("artifact-list");
const logStream = document.getElementById("log-stream");
const statusChip = document.getElementById("status-chip");

export function setStatus(text) {
  statusChip.textContent = text;
}

export function updateStepStatus(stepId, status, detail = "") {
  const stepEl = stepList.querySelector(`[data-step='${stepId}']`);
  if (!stepEl) return;
  stepEl.classList.remove("is-running", "is-done", "is-error");
  if (status === "running") stepEl.classList.add("is-running");
  if (status === "done") stepEl.classList.add("is-done");
  if (status === "error") stepEl.classList.add("is-error");
  const detailEl = stepEl.querySelector("[data-step-detail]");
  if (detailEl) {
    detailEl.textContent = detail;
  }
}

export function resetSteps() {
  document.querySelectorAll(".step").forEach((step) => {
    step.classList.remove("is-running", "is-done", "is-error");
    const detailEl = step.querySelector("[data-step-detail]");
    if (detailEl) detailEl.textContent = "";
  });
}

export function addArtifact(label, value) {
  const item = document.createElement("li");
  item.className = "artifact";
  item.innerHTML = `<strong>${label}</strong><span>${value}</span>`;
  artifactList.appendChild(item);
}

export function clearArtifacts() {
  artifactList.innerHTML = "";
}

export function appendLog(entry) {
  const item = document.createElement("div");
  const time = entry.time.toLocaleTimeString();
  item.className = `log-entry level-${entry.level}`;
  const payload = entry.data ? ` | ${JSON.stringify(entry.data)}` : "";
  item.textContent = `[${time}] ${entry.level.toUpperCase()} ${entry.message}${payload}`;
  logStream.appendChild(item);
  logStream.scrollTop = logStream.scrollHeight;
}

export function clearLogsView() {
  logStream.innerHTML = "";
}

export function setMetrics({ risk, perturbations, selectedAttack }) {
  if (risk !== undefined) {
    document.getElementById("metric-risk").textContent = risk;
  }
  if (perturbations !== undefined) {
    document.getElementById("metric-perturb").textContent = perturbations;
  }
  if (selectedAttack !== undefined) {
    document.getElementById("metric-attacks").textContent = selectedAttack;
  }
}
