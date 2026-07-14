"use strict";

async function api(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) throw new Error(`${path} -> ${response.status}`);
  return response.json();
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function badge(verdict) {
  return el("span", `badge ${verdict}`, verdict);
}

function card(label, value) {
  const node = el("div", "card");
  node.appendChild(el("div", "value", String(value)));
  node.appendChild(el("div", "label", label));
  return node;
}

function renderDetail(result) {
  const detail = document.getElementById("detail");
  detail.innerHTML = "";
  const head = el("div");
  head.appendChild(badge(result.verdict));
  head.append(` ${result.title} — ${result.method}, ${result.states_explored} states explored`);
  if (result.exhaustive && result.verdict === "verified") head.append(" (exhaustive proof)");
  detail.appendChild(head);
  detail.appendChild(el("p", "hint", result.claim));

  if (!result.counterexample) return;
  const counter = result.counterexample;
  detail.appendChild(el("p", "mono", counter.summary));
  if (counter.kind === "trace") {
    const trace = el("div", "trace");
    for (const step of counter.steps) {
      const row = el("div", "step");
      row.appendChild(el("span", "idx", String(step.index)));
      row.appendChild(el("span", "action", step.action));
      row.appendChild(el("span", "mono", JSON.stringify(step.state)));
      trace.appendChild(row);
    }
    detail.appendChild(trace);
  } else {
    detail.appendChild(el("p", "mono", JSON.stringify(counter.assignment)));
  }
}

async function loadSummary() {
  const summary = await api("/verify");
  const cards = document.getElementById("summary");
  cards.innerHTML = "";
  cards.appendChild(card("Obligations", summary.obligations));
  cards.appendChild(card("Proven", summary.verified));
  cards.appendChild(card("Refuted", summary.refuted));
  cards.appendChild(card("States explored", summary.total_states_explored));
  const verdicts = {};
  for (const r of summary.results) verdicts[r.id] = r.verdict;
  return verdicts;
}

async function loadObligations(verdicts) {
  const data = await api("/obligations");
  const list = document.getElementById("obligations");
  list.innerHTML = "";
  for (const obligation of data.obligations) {
    const item = el("button", "obligation");
    item.type = "button";
    const left = el("div");
    left.appendChild(el("div", "title", obligation.title));
    left.appendChild(el("div", "claim", obligation.claim));
    item.appendChild(left);
    if (verdicts[obligation.id]) item.appendChild(badge(verdicts[obligation.id]));
    item.addEventListener("click", async () => {
      renderDetail(await api(`/obligations/${obligation.id}/verify`, { method: "POST" }));
    });
    list.appendChild(item);
  }
  document.getElementById("meta").textContent = `${data.obligations.length} obligations`;
}

async function main() {
  const verdicts = await loadSummary();
  await loadObligations(verdicts);
}

main().catch((error) => {
  document.getElementById("subtitle").textContent = `Failed to load: ${error.message}`;
});
