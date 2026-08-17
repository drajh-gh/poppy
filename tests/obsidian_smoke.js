const Module = require("module");
const path = require("path");
const fs = require("fs");

let registeredType = null;
let registeredFactory = null;
let command = null;
let ribbon = null;
let activated = null;
let revealed = false;

class FakeElement {
  constructor(tag) {
    this.tagName = tag.toUpperCase();
    this.children = [];
    this.attributes = {};
    this.dataset = {};
    this.style = { setProperty: () => {} };
    this.className = "";
    this.textContent = "";
    this.id = "";
    this.htmlFor = "";
    this.listeners = {};
  }
  appendChild(child) { this.children.push(child); return child; }
  setAttribute(name, value) { this.attributes[name] = String(value); if (name === "id") this.id = String(value); if (name === "class") this.className = String(value); }
  getAttribute(name) { return this.attributes[name]; }
  addEventListener(name, callback) { this.listeners[name] = callback; }
  get firstChild() { return this.children[0] || null; }
  get lastChild() { return this.children[this.children.length - 1] || null; }
}

global.document = {
  createElement: (tag) => new FakeElement(tag),
  createElementNS: (_namespace, tag) => new FakeElement(tag),
};

function findAll(root, predicate, result = []) {
  if (predicate(root)) result.push(root);
  for (const child of root.children || []) findAll(child, predicate, result);
  return result;
}

class Plugin {
  constructor() {
    this.app = {
      workspace: {
        getLeavesOfType: () => [],
        getLeaf: () => ({ setViewState: async (state) => { activated = state; } }),
        revealLeaf: () => { revealed = true; },
        detachLeavesOfType: () => {},
      },
    };
  }
  registerView(type, factory) { registeredType = type; registeredFactory = factory; }
  addRibbonIcon(icon, title, callback) { ribbon = { icon, title, callback }; }
  addCommand(value) { command = value; }
}

class ItemView { constructor(leaf) { this.leaf = leaf; this.app = {}; } }

const originalLoad = Module._load;
Module._load = function (request, parent, isMain) {
  if (request === "obsidian") return { Plugin, ItemView, Notice: class {}, requestUrl: async () => ({ status: 200, json: {} }) };
  return originalLoad.apply(this, arguments);
};

async function run() {
  const entry = path.resolve(__dirname, "..", "dist", "poppy-ops-cockpit", "main.js");
  const source = fs.readFileSync(entry, "utf8");
  const PluginClass = require(entry);
  const plugin = new PluginClass();
  await plugin.onload();
  if (registeredType !== "poppy-ops-cockpit") throw new Error(`Unexpected view type: ${registeredType}`);
  if (typeof registeredFactory !== "function") throw new Error("View factory was not registered");
  if (!command || command.id !== "open-poppy-ops-cockpit") throw new Error("Open command was not registered");
  if (!ribbon || ribbon.icon !== "activity") throw new Error("Ribbon activation was not registered");
  await plugin.activateView();
  if (!activated || activated.type !== "poppy-ops-cockpit" || activated.active !== true) throw new Error("Pane view state was not activated");
  if (!revealed) throw new Error("Pane was not revealed");

  const graph = JSON.parse(fs.readFileSync(path.resolve(__dirname, "..", "config", "poppy-capability-graph.json"), "utf8"));
  const topology = PluginClass.computeTopology(graph.nodes, graph.edges);
  if (graph.nodes.length !== 37 || graph.edges.length !== 81 || topology.edges.length !== 81) throw new Error("The full 37-node/81-edge topology was not preserved");
  const outgoing = new Map();
  const incoming = new Map();
  for (const edge of topology.edges) {
    outgoing.set(edge.from, (outgoing.get(edge.from) || 0) + 1);
    incoming.set(edge.to, (incoming.get(edge.to) || 0) + 1);
  }
  if (![...outgoing.values()].some((count) => count > 1) || ![...incoming.values()].some((count) => count > 1)) throw new Error("Topology does not expose branches and joins");

  const view = new PluginClass.PoppyOpsView({}, plugin);
  view.state = { codex: { connection_state: "disconnected", interface_state: "supported" } };
  const dock = view.renderDock();
  const labels = findAll(dock, (node) => node.tagName === "LABEL");
  const textarea = findAll(dock, (node) => node.tagName === "TEXTAREA")[0];
  const input = findAll(dock, (node) => node.tagName === "INPUT")[0];
  const receipt = findAll(dock, (node) => node.id === "poppy-dock-receipt")[0];
  if (!textarea || labels[0].htmlFor !== textarea.id) throw new Error("Dock draft label is not associated with its textarea");
  if (!input || labels[1].htmlFor !== input.id) throw new Error("Dock thread label is not associated with its input");
  if (!receipt || receipt.getAttribute("role") !== "status" || receipt.getAttribute("aria-live") !== "polite") throw new Error("Dock receipt is not a polite live status region");

  view.state.events = [{ event_id: "event-1", run_id: "run-1", timestamp: "2026-08-17T00:00:00Z", status: "completed", kind: "verification.completed", approval: "authorized", message: "Gate verified", duration_ms: 10, tokens: {}, cost: { amount: null, basis: "unavailable" }, evidence: [{ source: "manifest", locator: "evidence/manifest.json", authority: "approved", state: "completed" }] }];
  const runDetail = view.renderRunDetail("run-1");
  const detailText = findAll(runDetail, () => true).map((node) => node.textContent).filter(Boolean).join(" | ");
  for (const text of ["verification.completed", "approval: authorized", "manifest — evidence/manifest.json", "cost unavailable"]) {
    if (!detailText.includes(text)) throw new Error(`Run detail lineage missing: ${text}`);
  }

  const finding = { id: "finding-1", kind: "execution-failure", severity: "high", message: "Gate failed", action: "Inspect it", event_ids: ["event-1"], references: [{ type: "event", id: "event-1", run_id: "run-1", label: "Gate verified" }] };
  view.state.findings = [finding];
  view.focusedFinding = finding.id;
  const issues = view.renderIssues();
  if (findAll(issues, (node) => node.className === "poppy-finding-ref").length !== 1) throw new Error("Issue drill-through did not render its structured reference");

  view.state.graph = graph;
  view.state.events = [];
  const topologyView = view.renderTopology();
  const renderedEdges = findAll(topologyView, (node) => node.className === "poppy-topology-edge");
  if (renderedEdges.length !== 81 || renderedEdges.some((edge) => edge.getAttribute("marker-end") !== "url(#poppy-topology-arrow)")) throw new Error("Rendered topology does not expose all directed edges");
  for (const token of ["event.approval", "event.kind", "ref.locator", "formatCost(event.cost)", "renderFindingReferences"]) {
    if (!source.includes(token)) throw new Error(`Trace or finding lineage surface missing: ${token}`);
  }

  process.stdout.write(JSON.stringify({ status: "pass", registeredType, command: command.id, ribbon: ribbon.icon, activated, topology: { nodes: graph.nodes.length, edges: topology.edges.length, levels: topology.levels }, accessibility: { labels: labels.length, liveRegion: receipt.id } }) + "\n");
}

run().catch((error) => { console.error(error.stack || error); process.exit(1); });
