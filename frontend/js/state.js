export const defaultSteps = [
  { id: "ingest", name: "PDF Ingestion", status: "pending", detail: "" },
  { id: "perturb", name: "Perturbation Planning", status: "pending", detail: "" },
  { id: "inject", name: "Attack Injection", status: "pending", detail: "" },
  { id: "compile", name: "Compilation", status: "pending", detail: "" },
  { id: "evaluate", name: "Evaluation", status: "pending", detail: "" },
];

export const state = {
  files: {
    pdf: null,
    answer: null,
  },
  steps: defaultSteps.map((step) => ({ ...step })),
  artifacts: [],
  metrics: {
    risk: "--",
    perturbations: "--",
    selectedAttack: "--",
  },
};

export function resetState() {
  state.files.pdf = null;
  state.files.answer = null;
  state.steps = defaultSteps.map((step) => ({ ...step }));
  state.artifacts = [];
  state.metrics = { risk: "--", perturbations: "--", selectedAttack: "--" };
}
