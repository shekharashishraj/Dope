const listeners = new Set();
const buffer = [];
const MAX_BUFFER = 400;

function emit(entry) {
  listeners.forEach((listener) => listener(entry));
}

export function onLog(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function getLogs() {
  return [...buffer];
}

export function clearLogs() {
  buffer.length = 0;
}

export function log(level, message, data = null) {
  const entry = {
    time: new Date(),
    level,
    message,
    data,
  };

  buffer.push(entry);
  if (buffer.length > MAX_BUFFER) {
    buffer.shift();
  }

  if (level === "error") {
    console.error(message, data || "");
  } else if (level === "warn") {
    console.warn(message, data || "");
  } else {
    console.log(message, data || "");
  }

  emit(entry);
}
