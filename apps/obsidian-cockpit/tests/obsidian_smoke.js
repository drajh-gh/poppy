const Module = require("module");
const path = require("path");
const fs = require("fs");
const { EventEmitter } = require("events");

let registeredType = null;
let registeredFactory = null;
let command = null;
let ribbon = null;
let activated = null;
let revealed = false;
let spawnedBridge = null;
let healthChecks = 0;
let lastApiRequest = null;
let apiRequestCount = 0;
let apiResponseJson = {};
let eventSourceCount = 0;
const syntheticVaultPath = path.resolve("C:\\Synthetic", "AtlasDemo");
let currentVaultPath = syntheticVaultPath;
const originalReadFileSync = fs.readFileSync.bind(fs);
fs.readFileSync = function (file, ...args) {
  if (String(file).endsWith(path.join("config", "bridge.json"))) {
    return JSON.stringify({
      bind: "127.0.0.1",
      port: 7318,
      runtime: { ledger: "runtime/events.jsonl", database: "runtime/poppy-ops.sqlite3" },
      vaults: [{ key: "atlas-demo", name: "Atlas Demo", path: syntheticVaultPath }],
    });
  }
  return originalReadFileSync(file, ...args);
};

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
global.EventSource = class {
  constructor(url) { this.url = url; this.listeners = {}; eventSourceCount += 1; }
  addEventListener(name, callback) { this.listeners[name] = callback; }
  close() {}
};

function findAll(root, predicate, result = []) {
  if (predicate(root)) result.push(root);
  for (const child of root.children || []) findAll(child, predicate, result);
  return result;
}

class Plugin {
  constructor() {
    const root = path.resolve(__dirname, "..");
    this.app = {
      vault: { adapter: { getBasePath: () => currentVaultPath }, getName: () => currentVaultPath === syntheticVaultPath ? "Atlas Demo" : "Unconfigured Demo" },
      workspace: {
        getLeavesOfType: () => [],
        getLeaf: () => ({ setViewState: async (state) => { activated = state; } }),
        revealLeaf: () => { revealed = true; },
        detachLeavesOfType: () => {},
      },
    };
    this.manifest = { dir: path.join(root, "dist", "poppy-ops-cockpit") };
  }
  registerView(type, factory) { registeredType = type; registeredFactory = factory; }
  addRibbonIcon(icon, title, callback) { ribbon = { icon, title, callback }; }
  addCommand(value) { command = value; }
}

class ItemView { constructor(leaf) { this.leaf = leaf; this.app = {}; } }

const originalLoad = Module._load;
Module._load = function (request, parent, isMain) {
  if (request === "child_process") return {
    spawn: (commandName, args, options) => {
      const child = new EventEmitter();
      child.killed = false;
      child.exitCode = null;
      child.signalCode = null;
      child.kill = (signal = "SIGTERM") => {
        child.killed = true;
        child.signalCode = signal;
        child.emit("exit", null, signal);
        return true;
      };
      spawnedBridge = { commandName, args, options, child };
      return child;
    },
  };
  if (request === "obsidian") return {
    Plugin,
    ItemView,
    Notice: class {},
    requestUrl: async (options) => {
      apiRequestCount += 1;
      lastApiRequest = options;
      if (String(options.url).endsWith("/health")) {
        healthChecks += 1;
        return healthChecks === 1
          ? { status: 503, json: { state: "gray" } }
          : { status: 200, json: {
            state: "completed",
            service: "poppy-ops-bridge",
            instance_token: spawnedBridge.args[spawnedBridge.args.indexOf("--instance-token") + 1],
          } };
      }
      return { status: 200, json: apiResponseJson };
    },
  };
  return originalLoad.apply(this, arguments);
};

async function run() {
  const entry = path.resolve(__dirname, "..", "dist", "poppy-ops-cockpit", "main.js");
  const source = fs.readFileSync(entry, "utf8");
  const PluginClass = require(entry);
  const plugin = new PluginClass();
  await plugin.onload();
  await plugin.ensureBridge();
  if (plugin.project.key !== "atlas-demo" || plugin.project.name !== "Atlas Demo") throw new Error("Plugin did not resolve the active vault to its project scope");
  if (plugin.bridgeApi !== "http://127.0.0.1:7318") throw new Error(`Plugin ignored its configured bridge endpoint: ${plugin.bridgeApi}`);
  if (!spawnedBridge) throw new Error("Plugin did not start its packaged bridge when health was unavailable");
  if (spawnedBridge.commandName !== (process.platform === "win32" ? "python" : "python3")) throw new Error("Plugin selected an unexpected Python command");
  if (!spawnedBridge.args[0].endsWith(path.join("dist", "poppy-ops-cockpit", "bridge", "poppy_ops_bridge.py")) || spawnedBridge.args[1] !== "serve") throw new Error("Plugin did not launch the packaged bridge entrypoint");
  if (!spawnedBridge.args.includes("--instance-token")) throw new Error("Plugin did not bind its child to a verifiable startup ownership token");
  if (!spawnedBridge.args.includes("--ledger") || !spawnedBridge.args.includes("--database") || !spawnedBridge.args.some((value) => String(value).endsWith(path.join("runtime", "events.jsonl")))) throw new Error("Plugin did not bind the bridge to the shared runtime store");
  if (!spawnedBridge.options.windowsHide || spawnedBridge.options.shell !== false || spawnedBridge.options.stdio !== "ignore") throw new Error("Packaged bridge launch is not hidden and shell-free");
  if (plugin.bridgeStatus.state !== "completed") throw new Error("Plugin did not verify bridge health after launch");
  if (registeredType !== "poppy-ops-cockpit") throw new Error(`Unexpected view type: ${registeredType}`);
  if (typeof registeredFactory !== "function") throw new Error("View factory was not registered");
  if (!command || command.id !== "open-poppy-ops-cockpit") throw new Error("Open command was not registered");
  if (!ribbon || ribbon.icon !== "activity") throw new Error("Ribbon activation was not registered");
  await plugin.activateView();
  if (!activated || activated.type !== "poppy-ops-cockpit" || activated.active !== true) throw new Error("Pane view state was not activated");
  if (!revealed) throw new Error("Pane was not revealed");

  const graph = JSON.parse(fs.readFileSync(path.resolve(__dirname, "..", "..", "..", "references", "poppy-capability-graph.json"), "utf8"));
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
  await view.api("/api/state");
  if (lastApiRequest.headers["X-Poppy-Ops-Project"] !== "atlas-demo") throw new Error("Plugin API request did not carry its project scope");
  apiResponseJson = { scope: { mode: "project", project: "beacon-demo" }, vaults: [{ key: "beacon-demo" }] };
  view.state = { scope: { mode: "project", project: "atlas-demo" } };
  await view.fetchState();
  if (view.state !== null || !String(view.error).includes("mismatched project scope")) throw new Error("Plugin accepted a mismatched bridge response scope");
  apiResponseJson = {};
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

  view.state.runs = [{ run_id: "run-1", project: "portfolio", status: "completed", updated_at: "2026-08-17T00:00:00Z", duration_ms: 10, tokens: {}, cost: { amount: null, basis: "unavailable" } }];
  const runs = view.renderRuns();
  if (!findAll(runs, (node) => node.textContent === "unavailable").length) throw new Error("Unavailable run cost is not rendered as a Gray unavailable state");
  const eurCost = PluginClass.formatCost({ amount: 12.5, currency: "EUR", basis: "exact" });
  if (!eurCost.includes("EUR") && !eurCost.includes("€")) throw new Error("Single-currency non-USD cost does not preserve its currency in the UI");
  if (eurCost.includes("$")) throw new Error("Non-USD cost was relabelled as USD in the UI");
  for (const cost of [
    { amount: NaN, currency: "USD", basis: "exact" },
    { amount: Infinity, currency: "USD", basis: "exact" },
    { amount: -1, currency: "USD", basis: "exact" },
    { amount: true, currency: "USD", basis: "exact" },
    { amount: 1, basis: "exact" },
    { amount: 1, currency: "USD", basis: "unavailable" },
  ]) {
    if (PluginClass.formatCost(cost) !== "unavailable") throw new Error(`Malformed cost did not render Gray: ${JSON.stringify(cost)}`);
  }

  const finding = { id: "finding-1", kind: "execution-failure", severity: "high", message: "Gate failed", action: "Inspect it", event_ids: ["event-1"], references: [{ type: "event", id: "event-1", run_id: "run-1", label: "Gate verified" }] };
  view.state.findings = [finding];
  view.focusedFinding = null;
  let issues = view.renderIssues();
  const inspect = findAll(issues, (node) => node.textContent === "Inspect references")[0];
  if (!inspect?.listeners?.click) throw new Error("Issue finding has no drill-through control");
  inspect.listeners.click();
  issues = view.renderIssues();
  const findingRef = findAll(issues, (node) => node.className === "poppy-finding-ref")[0];
  if (!findingRef) throw new Error("Issue drill-through did not render its structured reference");
  findingRef.listeners.click();
  if (view.page !== "runs" || view.selectedRun !== "run-1") throw new Error("Event finding reference did not focus its linked run");

  view.state.graph = graph;
  view.state.events = [];
  const topologyView = view.renderTopology();
  const renderedEdges = findAll(topologyView, (node) => node.className === "poppy-topology-edge");
  if (renderedEdges.length !== 81 || renderedEdges.some((edge) => edge.getAttribute("marker-end") !== "url(#poppy-topology-arrow)")) throw new Error("Rendered topology does not expose all directed edges");
  for (const token of ["event.approval", "event.kind", "ref.locator", "formatCost(event.cost)", "renderFindingReferences"]) {
    if (!source.includes(token)) throw new Error(`Trace or finding lineage surface missing: ${token}`);
  }

  await plugin.onunload();
  if (!spawnedBridge.child.killed) throw new Error("Plugin did not stop its owned bridge during unload");

  currentVaultPath = path.resolve("C:\\Synthetic", "UnconfiguredDemo");
  const requestsBeforeUnconfigured = apiRequestCount;
  const eventsBeforeUnconfigured = eventSourceCount;
  const unconfigured = new PluginClass();
  await unconfigured.onload();
  if (unconfigured.project.key !== null || unconfigured.project.state !== "gray" || !String(unconfigured.project.reason).includes("not configured")) throw new Error("Unmatched vault did not resolve to explicit Gray scope");
  if (apiRequestCount !== requestsBeforeUnconfigured) throw new Error("Unconfigured plugin contacted the bridge during load");
  const unconfiguredView = new PluginClass.PoppyOpsView({}, unconfigured);
  let rejected = false;
  try { await unconfiguredView.api("/api/state"); } catch (error) { rejected = String(error).includes("not configured"); }
  if (!rejected || apiRequestCount !== requestsBeforeUnconfigured) throw new Error("Unconfigured view did not reject state locally before HTTP");
  unconfiguredView.connectEvents();
  if (eventSourceCount !== eventsBeforeUnconfigured) throw new Error("Unconfigured view opened an SSE connection");
  const unavailable = unconfiguredView.renderUnavailable();
  const unavailableText = findAll(unavailable, () => true).map((node) => node.textContent).filter(Boolean).join(" | ");
  if (!unavailableText.includes("not configured for Poppy") || !unavailableText.includes("no portfolio scope")) throw new Error("Unconfigured vault did not render explicit fail-closed guidance");
  await unconfigured.onunload();

  process.stdout.write(JSON.stringify({ status: "pass", registeredType, command: command.id, ribbon: ribbon.icon, activated, bridgeStartup: { command: spawnedBridge.commandName, healthChecks, stoppedOnUnload: spawnedBridge.child.killed }, topology: { nodes: graph.nodes.length, edges: topology.edges.length, levels: topology.levels }, accessibility: { labels: labels.length, liveRegion: receipt.id }, cost: { unavailable: "gray", nonUsd: eurCost } }) + "\n");
}

run().catch((error) => { console.error(error.stack || error); process.exit(1); });
