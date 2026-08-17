const { Plugin, ItemView, Notice, requestUrl } = require("obsidian");

const VIEW_TYPE = "poppy-ops-cockpit";
const API = "http://127.0.0.1:7317";
const NAV = [
  ["overview", "Overview", "portfolio"],
  ["execution", "Live run", "route"],
  ["runs", "Runs", "history"],
  ["evidence", "Evidence", "scan-search"],
  ["vaults", "Vaults", "archive"],
  ["operations", "Core ops", "list-checks"],
  ["capabilities", "Capabilities", "workflow"],
  ["issues", "Optimize", "wrench"],
  ["dock", "Poppy dock", "messages-square"],
];

const STATE_LABELS = {
  completed: "verified",
  current: "in motion",
  waiting: "waiting",
  blocked: "blocked",
  pending: "queued",
  failed: "failed",
  gray: "gray",
  supported: "supported",
  connected: "connected",
  disconnected: "disconnected",
};

function h(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

function append(parent, ...children) {
  for (const child of children.flat()) if (child) parent.appendChild(child);
  return parent;
}

function clear(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function stateBadge(state, label) {
  const normalized = ["completed", "current", "waiting", "blocked", "pending", "failed", "gray"].includes(state) ? state : "gray";
  const badge = h("span", `poppy-state is-${normalized}`);
  append(badge, h("span", "poppy-state__lamp"), h("span", "", label || STATE_LABELS[state] || state || "gray"));
  return badge;
}

function formatDuration(ms) {
  if (ms === null || ms === undefined) return "—";
  if (ms < 1000) return `${ms} ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(ms < 10000 ? 1 : 0)} s`;
  return `${Math.floor(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`;
}

function formatTokens(tokens = {}) {
  const total = ["input", "cached", "reasoning", "output"].reduce((sum, key) => sum + Number(tokens[key] || 0), 0);
  return new Intl.NumberFormat().format(total);
}

function formatCost(cost = {}) {
  const basis = typeof cost.basis === "string" ? cost.basis : "unavailable";
  const currency = typeof cost.currency === "string" ? cost.currency.trim().toUpperCase() : "";
  const amount = typeof cost.amount === "boolean" ? NaN : Number(cost.amount);
  if (!["exact", "estimated", "shadow-price"].includes(basis)
      || !/^[A-Z]{3}$/.test(currency)
      || cost.amount === null
      || cost.amount === undefined
      || !Number.isFinite(amount)
      || amount < 0) return "unavailable";
  try {
    const digits = amount < 0.01 ? 4 : 2;
    const formatted = new Intl.NumberFormat(undefined, {
      style: "currency",
      currency,
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    }).format(amount);
    return `${formatted} · ${basis}`;
  } catch (_error) {
    return "unavailable";
  }
}

function formatTime(value) {
  if (!value) return "Unknown time";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function eyebrow(text) {
  return h("div", "poppy-eyebrow", text);
}

function emptyState(title, detail) {
  const node = h("div", "poppy-empty");
  append(node, h("div", "poppy-empty__mark", "∅"), h("h3", "", title), h("p", "", detail));
  return node;
}

function sectionTitle(kicker, title, note) {
  const node = h("header", "poppy-section-title");
  append(node, eyebrow(kicker), h("h2", "", title));
  if (note) append(node, h("p", "", note));
  return node;
}

function metric(label, value, note, state) {
  const node = h("div", "poppy-metric");
  append(node, h("span", "poppy-metric__label", label), h("strong", "poppy-metric__value", value), h("span", "poppy-metric__note", note || ""));
  if (state) node.dataset.state = state;
  return node;
}

function semanticState(value) {
  return ["completed", "current", "waiting", "blocked", "pending", "failed", "gray"].includes(value) ? value : "gray";
}

function computeTopology(nodes = [], edges = []) {
  const ids = new Set(nodes.map((node) => node.id));
  const validEdges = edges.filter((edge) => ids.has(edge.from) && ids.has(edge.to));
  const incoming = new Map(nodes.map((node) => [node.id, 0]));
  const outgoing = new Map(nodes.map((node) => [node.id, []]));
  for (const edge of validEdges) {
    incoming.set(edge.to, (incoming.get(edge.to) || 0) + 1);
    outgoing.get(edge.from).push(edge.to);
  }
  const level = new Map(nodes.map((node) => [node.id, 0]));
  const queue = nodes.filter((node) => incoming.get(node.id) === 0).map((node) => node.id);
  const visited = new Set();
  while (queue.length) {
    const id = queue.shift();
    if (visited.has(id)) continue;
    visited.add(id);
    for (const target of outgoing.get(id) || []) {
      level.set(target, Math.max(level.get(target) || 0, (level.get(id) || 0) + 1));
      incoming.set(target, incoming.get(target) - 1);
      if (incoming.get(target) === 0) queue.push(target);
    }
  }
  const buckets = new Map();
  for (const node of nodes) {
    const value = level.get(node.id) || 0;
    if (!buckets.has(value)) buckets.set(value, []);
    buckets.get(value).push(node.id);
  }
  const maxLevel = Math.max(0, ...buckets.keys());
  const maxRows = Math.max(1, ...[...buckets.values()].map((items) => items.length));
  const positions = new Map();
  for (const [column, items] of buckets) {
    const offset = (maxRows - items.length) * 38;
    items.forEach((id, row) => positions.set(id, { x: 38 + column * 176, y: 36 + offset + row * 76, level: column }));
  }
  return { positions, edges: validEdges, width: Math.max(760, 150 + maxLevel * 176), height: Math.max(240, 72 + maxRows * 76), levels: maxLevel + 1 };
}

class PoppyOpsView extends ItemView {
  constructor(leaf, plugin) {
    super(leaf);
    this.plugin = plugin;
    this.page = "overview";
    this.state = null;
    this.loading = false;
    this.error = null;
    this.selectedRun = null;
    this.eventSource = null;
    this.pollTimer = null;
  }

  getViewType() { return VIEW_TYPE; }
  getDisplayText() { return "Poppy Ops Cockpit"; }
  getIcon() { return "activity"; }

  async onOpen() {
    this.containerEl.addClass("poppy-ops-view");
    this.renderShell();
    await this.fetchState();
    this.connectEvents();
    this.pollTimer = window.setInterval(() => this.fetchState(true), 30000);
    this.registerEvent(this.app.vault.on("modify", () => this.scheduleVaultRefresh()));
    this.registerEvent(this.app.vault.on("create", () => this.scheduleVaultRefresh()));
    this.registerEvent(this.app.vault.on("delete", () => this.scheduleVaultRefresh()));
  }

  async onClose() {
    if (this.eventSource) this.eventSource.close();
    if (this.pollTimer) window.clearInterval(this.pollTimer);
    if (this.refreshTimer) window.clearTimeout(this.refreshTimer);
  }

  scheduleVaultRefresh() {
    if (this.refreshTimer) window.clearTimeout(this.refreshTimer);
    this.refreshTimer = window.setTimeout(() => this.refreshVaults(false), 700);
  }

  renderShell() {
    clear(this.contentEl);
    this.shell = h("div", "poppy-shell");
    this.rail = h("aside", "poppy-command-rail");
    this.stage = h("main", "poppy-stage");
    this.body = h("div", "poppy-stage__body");

    const brand = h("div", "poppy-brand");
    append(brand, h("div", "poppy-brand__sigil", "P"), h("div", "poppy-brand__words"));
    append(brand.lastChild, h("strong", "", "Poppy"), h("span", "", "Ops cockpit"));
    this.rail.appendChild(brand);

    const nav = h("nav", "poppy-nav");
    nav.setAttribute("aria-label", "Cockpit views");
    for (const [id, label] of NAV) {
      const button = h("button", "poppy-nav__item");
      button.type = "button";
      button.dataset.page = id;
      button.title = label;
      button.setAttribute("aria-label", label);
      append(button, h("span", "poppy-nav__glyph", label.slice(0, 1)), h("span", "poppy-nav__label", label));
      button.addEventListener("click", () => { this.page = id; this.render(); });
      nav.appendChild(button);
    }
    this.rail.appendChild(nav);

    this.connection = h("div", "poppy-connection");
    this.connection.setAttribute("role", "status");
    this.connection.setAttribute("aria-live", "polite");
    this.connection.setAttribute("aria-atomic", "true");
    this.rail.appendChild(this.connection);

    this.header = h("header", "poppy-stage__header");
    const heading = h("div", "poppy-stage__heading");
    append(heading, eyebrow("Private instrument panel"), h("h1", "", "Project operations, exposed"));
    this.headerActions = h("div", "poppy-stage__actions");
    const refresh = h("button", "poppy-button poppy-button--quiet", "Refresh index");
    refresh.type = "button";
    refresh.addEventListener("click", () => this.refreshVaults(true));
    const reload = h("button", "poppy-button poppy-button--quiet", "Reload view");
    reload.type = "button";
    reload.addEventListener("click", () => this.fetchState());
    append(this.headerActions, refresh, reload);
    append(this.header, heading, this.headerActions);
    append(this.stage, this.header, this.body);
    append(this.shell, this.rail, this.stage);
    this.contentEl.appendChild(this.shell);
    this.render();
  }

  async api(path, options = {}) {
    const response = await requestUrl({
      url: `${API}${path}`,
      method: options.method || "GET",
      headers: { "X-Poppy-Ops-Client": "obsidian-plugin", "Content-Type": "application/json" },
      body: options.body ? JSON.stringify(options.body) : undefined,
      throw: false,
    });
    if (response.status >= 400) throw new Error(response.json?.error || `Bridge returned ${response.status}`);
    return response.json;
  }

  async fetchState(silent = false) {
    if (this.loading) return;
    this.loading = true;
    if (!silent) { this.error = null; this.render(); }
    try {
      this.state = await this.api("/api/state");
      this.error = null;
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
    } finally {
      this.loading = false;
      this.render();
    }
  }

  async refreshVaults(notify) {
    try {
      await this.api("/api/refresh", { method: "POST", body: { scope: "configured-vaults", mode: "read-only-index" } });
      await this.fetchState(true);
      if (notify) new Notice("Poppy refreshed the local read-only vault index.");
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
      this.render();
    }
  }

  connectEvents() {
    if (typeof EventSource === "undefined") return;
    try {
      this.eventSource = new EventSource(`${API}/events`);
      this.eventSource.addEventListener("poppy", () => this.fetchState(true));
      this.eventSource.onerror = () => this.updateConnection();
    } catch (_) {
      this.eventSource = null;
    }
  }

  updateConnection() {
    if (!this.connection) return;
    clear(this.connection);
    const bridgeState = this.state?.service?.state || "gray";
    append(this.connection, stateBadge(this.error ? "gray" : bridgeState, this.error ? "bridge offline" : "localhost"));
    const time = h("span", "", this.state?.captured_at ? formatTime(this.state.captured_at) : "No snapshot");
    this.connection.appendChild(time);
  }

  render() {
    if (!this.body) return;
    for (const button of this.rail.querySelectorAll("[data-page]")) {
      const active = button.dataset.page === this.page;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-current", active ? "page" : "false");
    }
    this.updateConnection();
    clear(this.body);
    this.body.setAttribute("aria-busy", this.loading ? "true" : "false");
    if (this.loading && !this.state) {
      append(this.body, h("div", "poppy-loading", "Reading the instruments…"));
      return;
    }
    if (this.error && !this.state) {
      append(this.body, this.renderOffline());
      return;
    }
    const renderer = {
      overview: () => this.renderOverview(), execution: () => this.renderExecution(), runs: () => this.renderRuns(),
      evidence: () => this.renderEvidence(), vaults: () => this.renderVaults(), operations: () => this.renderOperations(), capabilities: () => this.renderCapabilities(),
      issues: () => this.renderIssues(), dock: () => this.renderDock(),
    }[this.page];
    append(this.body, renderer ? renderer() : this.renderOverview());
    if (this.error) {
      const warning = h("div", "poppy-inline-warning");
      warning.setAttribute("role", "status");
      warning.setAttribute("aria-live", "polite");
      append(warning, stateBadge("gray"), h("span", "", this.error));
      this.body.prepend(warning);
    }
  }

  renderOffline() {
    const node = h("section", "poppy-offline");
    append(node, stateBadge("gray", "bridge unavailable"), h("h2", "", "The cockpit has no live instrument feed"), h("p", "", "Start the localhost bridge from the repository. Missing telemetry remains Gray; the cockpit will not infer a healthy state."));
    const code = h("code", "", "python bridge/poppy_ops_bridge.py serve");
    const retry = h("button", "poppy-button", "Try again");
    retry.addEventListener("click", () => this.fetchState());
    append(node, code, retry);
    return node;
  }

  renderOverview() {
    const root = h("section", "poppy-page poppy-page--overview");
    const vaults = this.state?.vaults || [];
    const runs = this.state?.runs || [];
    const active = runs.filter((run) => ["current", "waiting", "blocked", "failed"].includes(run.status));
    const gray = vaults.filter((vault) => vault.state === "gray");
    const current = (this.state?.events || []).find((event) => event.status === "current") || (this.state?.events || [])[0];
    append(root, sectionTitle("Portfolio control", "One desk, two vaults", "The cockpit reads canonical project memory in place and keeps unavailable evidence Gray."));

    const pulse = h("div", "poppy-overview-pulse");
    const statement = h("div", "poppy-overview-pulse__statement");
    append(statement, eyebrow(current ? "Now moving" : "No active event"), h("strong", "", current?.message || "No live run has reported a current step."), current ? stateBadge(current.status) : stateBadge("gray"));
    const metrics = h("div", "poppy-metrics");
    append(metrics,
      metric("Vault coverage", `${vaults.length - gray.length}/${vaults.length || 2}`, gray.length ? `${gray.length} Gray` : "both indexed", gray.length ? "gray" : "completed"),
      metric("Runs in view", String(runs.length), `${active.length} need attention`, active.length ? "current" : "completed"),
      metric("Capability map", String(this.state?.graph?.nodes?.length || 0), this.state?.graph?.state === "completed" ? "source-backed" : "unavailable", this.state?.graph?.state),
      metric("Optimization", String(this.state?.findings?.length || 0), "deterministic findings", this.state?.findings?.some((item) => item.severity === "high") ? "failed" : "completed")
    );
    append(pulse, statement, metrics);
    root.appendChild(pulse);

    const split = h("div", "poppy-split");
    const attention = h("section", "poppy-ledger");
    append(attention, sectionTitle("Attention", "What needs a decision"));
    const attentionItems = [];
    for (const run of active.slice(0, 5)) attentionItems.push({ state: run.status, title: run.run_id, note: `${run.project} · ${formatTime(run.updated_at)}` });
    for (const vault of gray) attentionItems.push({ state: "gray", title: `${vault.name} evidence coverage`, note: vault.reason });
    if (!attentionItems.length) attention.appendChild(emptyState("Nothing is escalated", "All visible runs and vault snapshots are outside blocked, failed, and Gray states."));
    for (const item of attentionItems) {
      const row = h("button", "poppy-ledger-row");
      row.type = "button";
      append(row, stateBadge(item.state), h("strong", "", item.title), h("span", "", item.note));
      row.addEventListener("click", () => { this.page = item.title.startsWith("run") ? "runs" : "vaults"; this.render(); });
      attention.appendChild(row);
    }

    const projects = h("section", "poppy-project-lines");
    append(projects, sectionTitle("Project lines", "Canonical memory at a glance"));
    for (const vault of vaults) {
      const line = h("article", "poppy-project-line");
      const header = h("div", "poppy-project-line__header");
      append(header, h("div", "", `${vault.name} / ${vault.project?.stage || "unknown stage"}`), stateBadge(vault.state));
      append(line, header, h("h3", "", vault.project?.next_milestone || "No verified milestone"));
      const details = h("div", "poppy-project-line__details");
      append(details, h("span", "", `${vault.sources?.length || 0} configured sources`), h("span", "", `${vault.records?.base_count || 0} operational Bases`), h("span", "", `${vault.contradictions?.length || 0} preserved tensions`));
      line.appendChild(details);
      projects.appendChild(line);
    }
    append(split, attention, projects);
    root.appendChild(split);
    root.appendChild(this.renderCodexBoundary());
    return root;
  }

  renderCodexBoundary() {
    const codex = this.state?.codex || {};
    const node = h("section", "poppy-boundary");
    const status = codex.interface_state === "supported" ? (codex.connection_state === "connected" ? "completed" : "waiting") : "gray";
    append(node, stateBadge(status), h("div", ""));
    append(node.lastChild, h("strong", "", "Codex App Server"), h("span", "", `${codex.version || "version unavailable"} · ${codex.connection_state || "disconnected"}`));
    const rule = h("span", "poppy-boundary__rule", "Turn submission is disabled; task preparation uses an official read-only thread surface.");
    node.appendChild(rule);
    return node;
  }

  statusByCapability() {
    const result = new Map();
    for (const event of [...(this.state?.events || [])].reverse()) {
      if (event.capability) result.set(event.capability, event);
    }
    return result;
  }

  renderExecution() {
    const root = h("section", "poppy-page poppy-page--execution");
    append(root, sectionTitle("Execution trace", "Poppy's capability rail", "The rail is sourced from the installed capability graph; observed events illuminate nodes in place."));
    root.appendChild(this.renderTopology());
    const layout = h("div", "poppy-execution-layout");
    const rail = h("div", "poppy-execution-rail");
    const statusMap = this.statusByCapability();
    const nodes = this.state?.graph?.nodes || [];
    if (!nodes.length) rail.appendChild(emptyState("Capability graph is Gray", this.state?.graph?.reason || "No graph source was available."));
    for (const [index, node] of nodes.entries()) {
      const event = statusMap.get(node.id) || [...(this.state?.events || [])].find((item) => item.skill === node.handler);
      const state = semanticState(event?.status || "pending");
      const item = h("article", `poppy-execution-node is-${state}`);
      item.dataset.node = node.id;
      const marker = h("div", "poppy-execution-node__marker", String(index + 1).padStart(2, "0"));
      const content = h("div", "poppy-execution-node__content");
      const top = h("div", "poppy-execution-node__top");
      append(top, h("strong", "", node.id), stateBadge(state));
      append(content, top, h("p", "", event?.message || `${node.handler} · ${node.execution}`));
      const facts = h("div", "poppy-execution-node__facts");
      append(facts, h("span", "", node.kind), h("span", "", node.handler), h("span", "", formatDuration(event?.duration_ms)));
      content.appendChild(facts);
      append(item, marker, content);
      rail.appendChild(item);
    }

    const trace = h("aside", "poppy-trace-desk");
    append(trace, eyebrow("Observed trace"), h("h3", "", "Recent nested activity"));
    const recent = (this.state?.events || []).slice(0, 20);
    const ids = new Map(recent.map((event) => [event.event_id, event]));
    for (const event of recent) {
      const depth = event.parent_id && ids.has(event.parent_id) ? 1 : 0;
      const row = h("div", "poppy-trace-row");
      row.style.setProperty("--trace-depth", depth);
      append(row, stateBadge(event.status), h("div", ""));
      append(row.lastChild, h("strong", "", event.message), h("span", "", `${event.worker || event.skill || "Poppy"} · ${formatTime(event.timestamp)}`));
      trace.appendChild(row);
    }
    if (!recent.length) trace.appendChild(emptyState("No recorded activity", "Start an instrumented run or replay a fixture ledger."));
    append(layout, rail, trace);
    root.appendChild(layout);
    return root;
  }

  renderTopology() {
    const section = h("section", "poppy-topology");
    const head = h("div", "poppy-topology__head");
    const graph = this.state?.graph || { nodes: [], edges: [] };
    append(head, h("div", ""), h("span", "poppy-mono", `${graph.nodes?.length || 0} nodes / ${graph.edges?.length || 0} edges`));
    append(head.firstChild, eyebrow("Control-flow topology"), h("h3", "", "Branches, joins, and authority gates"));
    section.appendChild(head);
    if (!graph.nodes?.length) return append(section, emptyState("Topology is Gray", graph.reason || "No graph was loaded.")), section;
    const topology = computeTopology(graph.nodes, graph.edges || []);
    const viewport = h("div", "poppy-topology__viewport");
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", `0 0 ${topology.width} ${topology.height}`);
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", `Poppy capability topology with ${graph.nodes.length} nodes, ${topology.edges.length} directed edges, and ${topology.levels} control-flow levels`);
    const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
    const marker = document.createElementNS("http://www.w3.org/2000/svg", "marker");
    marker.setAttribute("id", "poppy-topology-arrow");
    marker.setAttribute("viewBox", "0 0 6 6");
    marker.setAttribute("refX", "5"); marker.setAttribute("refY", "3");
    marker.setAttribute("markerWidth", "5"); marker.setAttribute("markerHeight", "5");
    marker.setAttribute("orient", "auto-start-reverse");
    const arrow = document.createElementNS("http://www.w3.org/2000/svg", "path");
    arrow.setAttribute("d", "M 0 0 L 6 3 L 0 6 z");
    arrow.setAttribute("class", "poppy-topology-arrow");
    marker.appendChild(arrow); defs.appendChild(marker); svg.appendChild(defs);
    const statusMap = this.statusByCapability();
    for (const edge of topology.edges) {
      const source = topology.positions.get(edge.from);
      const target = topology.positions.get(edge.to);
      if (!source || !target) continue;
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      const startX = source.x + 116;
      const startY = source.y + 16;
      const endX = target.x;
      const endY = target.y + 16;
      const bend = Math.max(28, Math.abs(endX - startX) * .44);
      path.setAttribute("d", `M ${startX} ${startY} C ${startX + bend} ${startY}, ${endX - bend} ${endY}, ${endX} ${endY}`);
      path.setAttribute("class", "poppy-topology-edge");
      path.setAttribute("marker-end", "url(#poppy-topology-arrow)");
      path.dataset.from = edge.from;
      path.dataset.to = edge.to;
      svg.appendChild(path);
    }
    for (const node of graph.nodes) {
      const position = topology.positions.get(node.id);
      if (!position) continue;
      const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
      const state = semanticState(statusMap.get(node.id)?.status || "pending");
      group.setAttribute("class", `poppy-topology-node is-${state}`);
      group.setAttribute("transform", `translate(${position.x} ${position.y})`);
      group.setAttribute("role", "group");
      group.setAttribute("aria-label", `${node.id}, ${state}, handled by ${node.handler}`);
      const box = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      box.setAttribute("width", "116"); box.setAttribute("height", "34"); box.setAttribute("rx", "2");
      const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
      label.setAttribute("x", "9"); label.setAttribute("y", "21"); label.textContent = node.id;
      append(group, box, label);
      svg.appendChild(group);
    }
    viewport.appendChild(svg);
    section.appendChild(viewport);
    return section;
  }

  renderRuns() {
    const root = h("section", "poppy-page");
    append(root, sectionTitle("Run history", "Time, tokens, cost basis", "Dollar figures distinguish exact, estimated, shadow price, and unavailable bases."));
    const runs = this.state?.runs || [];
    if (!runs.length) return append(root, emptyState("No runs recorded", "Replay a ledger or connect a supported event source.")), root;
    const table = h("div", "poppy-run-table");
    const head = h("div", "poppy-run-row poppy-run-row--head");
    for (const label of ["State", "Run", "Project", "Updated", "Elapsed", "Tokens", "Cost"]) head.appendChild(h("span", "", label));
    table.appendChild(head);
    for (const run of runs) {
      const row = h("button", "poppy-run-row");
      row.type = "button";
      const cost = run.cost?.basis === "unavailable" ? stateBadge("gray", "unavailable") : h("span", "poppy-mono", formatCost(run.cost));
      append(row, stateBadge(run.status), h("strong", "", run.run_id), h("span", "", run.project), h("span", "", formatTime(run.updated_at)), h("span", "poppy-mono", formatDuration(run.duration_ms)), h("span", "poppy-mono", formatTokens(run.tokens)), cost);
      row.addEventListener("click", () => { this.selectedRun = this.selectedRun === run.run_id ? null : run.run_id; this.render(); });
      table.appendChild(row);
      if (this.selectedRun === run.run_id) table.appendChild(this.renderRunDetail(run.run_id));
    }
    root.appendChild(table);
    return root;
  }

  renderRunDetail(runId) {
    const detail = h("div", "poppy-run-detail");
    const events = (this.state?.events || []).filter((event) => event.run_id === runId).reverse();
    for (const event of events) {
      const row = h("div", "poppy-run-event");
      const eventCost = event.cost?.basis === "unavailable" ? stateBadge("gray", "cost unavailable") : h("span", "poppy-mono", formatCost(event.cost));
      append(row, h("time", "poppy-mono", formatTime(event.timestamp)), stateBadge(event.status), h("div", ""), h("span", "poppy-mono", formatDuration(event.duration_ms)), h("span", "poppy-mono", formatTokens(event.tokens)), eventCost);
      const verification = /verification|assurance|qa/i.test(event.kind) ? "verification event" : "execution event";
      append(row.children[2], h("strong", "", event.message), h("span", "", [event.kind, verification, `approval: ${event.approval || "unresolved"}`, event.capability, event.skill, event.tool, event.worker].filter(Boolean).join(" · ")));
      if (event.evidence?.length) {
        const evidence = h("ul", "poppy-run-event__evidence");
        for (const ref of event.evidence) evidence.appendChild(h("li", "", `${ref.source} — ${ref.locator || "unlinked locator"} · ${ref.authority || "unresolved authority"} · ${ref.state || "gray"}`));
        row.children[2].appendChild(evidence);
      }
      detail.appendChild(row);
    }
    return detail;
  }

  renderEvidence() {
    const root = h("section", "poppy-page");
    append(root, sectionTitle("Evidence desk", "Sources keep their edges", "Authority, freshness, contradiction, and unavailable coverage remain visible on every claim."));
    const groups = [];
    for (const event of this.state?.events || []) for (const item of event.evidence || []) groups.push({ ...item, event });
    if (!groups.length) return append(root, emptyState("No linked evidence", "Unlinked events remain visible in the run trace, but they cannot support favorable evidence claims.")), root;
    const filters = h("div", "poppy-evidence-summary");
    append(
      filters,
      metric("Evidence links", String(groups.length), `${new Set(groups.map((item) => item.source)).size} sources`, "completed"),
      metric("Contradictions", String(groups.filter((item) => item.contradiction).length), "preserved, not flattened", groups.some((item) => item.contradiction) ? "waiting" : "completed"),
      metric("Gray links", String(groups.filter((item) => item.state === "gray").length), "cannot support Green", groups.some((item) => item.state === "gray") ? "gray" : "completed")
    );
    root.appendChild(filters);
    const desk = h("div", "poppy-evidence-desk");
    for (const item of groups) {
      const card = h("article", "poppy-evidence-card");
      const top = h("div", "poppy-evidence-card__top");
      append(top, stateBadge(item.state), h("strong", "", item.source), item.contradiction ? stateBadge("waiting", "contradiction") : null);
      append(card, top, h("p", "", item.locator || "No durable locator supplied"));
      const terms = h("dl", "poppy-terms");
      for (const [term, value] of [["Authority", item.authority], ["Freshness", item.freshness], ["Supports", item.event.message]]) {
        append(terms, h("dt", "", term), h("dd", "", value || "unresolved"));
      }
      card.appendChild(terms);
      desk.appendChild(card);
    }
    root.appendChild(desk);
    return root;
  }

  renderVaults() {
    const root = h("section", "poppy-page");
    append(root, sectionTitle("Compiled memory", "Vault integration and refresh", "Refresh re-indexes local files only. It never rewrites canonical notes or contacts a provider."));
    for (const vault of this.state?.vaults || []) {
      const section = h("article", "poppy-vault");
      const head = h("header", "poppy-vault__head");
      append(head, h("div", ""), stateBadge(vault.state));
      append(head.firstChild, eyebrow(vault.project?.key || vault.key), h("h2", "", vault.name), h("p", "", vault.path));
      section.appendChild(head);
      const strip = h("div", "poppy-vault__strip");
      append(strip,
        metric("Stage", vault.project?.stage || "unknown", vault.project?.sensitivity || "unknown sensitivity", vault.state),
        metric("Sources", String(vault.sources?.length || 0), "configured adapters", "completed"),
        metric("Operational views", String(vault.records?.base_count || 0), "Obsidian Bases", "completed"),
        metric("Known tensions", String(vault.contradictions?.length || 0), "preserved", vault.contradictions?.length ? "waiting" : "completed")
      );
      section.appendChild(strip);
      const columns = h("div", "poppy-vault__columns");
      const freshness = h("div", "poppy-subledger");
      append(freshness, h("h3", "", "Freshness"));
      for (const [name, item] of Object.entries(vault.freshness || {})) {
        const row = h("div", "poppy-subledger__row");
        append(row, stateBadge(item.state), h("strong", "", name), h("span", "", item.reason), h("time", "poppy-mono", item.modified_at ? formatTime(item.modified_at) : "never"));
        freshness.appendChild(row);
      }
      const sources = h("div", "poppy-subledger");
      append(sources, h("h3", "", "Configured sources"));
      for (const item of vault.sources || []) {
        const row = h("div", "poppy-subledger__row");
        append(row, stateBadge(item.state), h("strong", "", item.name), h("span", "", item.mode || "configured"), h("span", "", item.authority_for?.join(", ") || "supporting evidence"));
        sources.appendChild(row);
      }
      append(columns, freshness, sources);
      section.appendChild(columns);
      if (vault.contradictions?.length) {
        const tensions = h("details", "poppy-tensions");
        append(tensions, h("summary", "", `${vault.contradictions.length} preserved contradiction or known risk`));
        const list = h("ul", "");
        for (const item of vault.contradictions) list.appendChild(h("li", "", item));
        tensions.appendChild(list);
        section.appendChild(tensions);
      }
      root.appendChild(section);
    }
    return root;
  }

  renderOperations() {
    const root = h("section", "poppy-page");
    append(root, sectionTitle("Core operations", "Health, actions, records, authority", "This view uses compiled project memory. Connector identities without a live receipt remain Gray even when configured."));
    for (const vault of this.state?.vaults || []) {
      const project = h("article", "poppy-ops-project");
      const signal = vault.health || { state: "gray", label: "Gray", headline: "Assessment unavailable" };
      const head = h("header", "poppy-ops-project__head");
      append(head, stateBadge(signal.state, signal.label), h("div", ""), h("time", "poppy-mono", signal.valid_as_of || "no valid-as-of"));
      append(head.children[1], eyebrow(vault.project?.key || vault.key), h("h2", "", signal.headline));
      project.appendChild(head);
      const decisionLine = h("div", "poppy-decision-line");
      append(decisionLine, h("span", "", "Next milestone"), h("strong", "", vault.project?.next_milestone || "No verified milestone"));
      project.appendChild(decisionLine);
      const metrics = h("div", "poppy-metrics poppy-metrics--ops");
      const counts = vault.records?.operational_counts || {};
      append(metrics,
        metric("Next actions", String(signal.next_action_count || 0), `review after ${signal.review_after || "unknown"}`, signal.state),
        metric("Health records", String(counts.health || 0), "compiled snapshots", counts.health ? "completed" : "gray"),
        metric("Decisions", String(counts.decisions || 0), "durable records", counts.decisions ? "completed" : "gray"),
        metric("RAID", String(counts.raid || counts.risks || 0), "durable records", (counts.raid || counts.risks) ? "completed" : "gray")
      );
      project.appendChild(metrics);
      const recordTable = h("div", "poppy-record-table");
      const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
      for (const [name, count] of entries) {
        const row = h("div", "poppy-record-row");
        append(row, h("strong", "", name.replace(/-/g, " ")), h("span", "poppy-mono", String(count)), stateBadge(count ? "completed" : "gray"));
        recordTable.appendChild(row);
      }
      if (!entries.length) recordTable.appendChild(emptyState("Operational record inventory is Gray", "No recognized PM record directories were found."));
      project.appendChild(recordTable);
      const authority = h("details", "poppy-authority-map");
      append(authority, h("summary", "", "Inspect authority map"));
      const terms = h("dl", "poppy-terms");
      for (const [claim, owner] of Object.entries(vault.authority || {})) append(terms, h("dt", "", claim), h("dd", "", typeof owner === "string" ? owner : JSON.stringify(owner)));
      authority.appendChild(terms);
      project.appendChild(authority);
      root.appendChild(project);
    }
    return root;
  }

  renderCapabilities() {
    const root = h("section", "poppy-page");
    const graph = this.state?.graph || {};
    append(root, sectionTitle("System anatomy", "Capabilities, handlers, instructions", `Graph ${graph.graph_id || "unavailable"} · ${graph.digest ? graph.digest.slice(0, 12) : "no digest"}`));
    if (!graph.nodes?.length) return append(root, emptyState("Capability source unavailable", graph.reason || "The installed graph could not be read.")), root;
    const groups = new Map();
    for (const node of graph.nodes) {
      if (!groups.has(node.kind)) groups.set(node.kind, []);
      groups.get(node.kind).push(node);
    }
    const matrix = h("div", "poppy-capability-matrix");
    for (const [kind, nodes] of groups) {
      const group = h("section", "poppy-capability-group");
      append(group, eyebrow(`${nodes.length} ${kind}`), h("h3", "", kind.replace(/-/g, " ")));
      for (const node of nodes) {
        const row = h("div", "poppy-capability-row");
        append(row, h("strong", "", node.id), h("span", "", node.handler), h("span", "", node.execution), h("span", "poppy-capability-row__io", `${node.inputs?.length || 0} in / ${node.outputs?.length || 0} out`));
        group.appendChild(row);
      }
      matrix.appendChild(group);
    }
    root.appendChild(matrix);
    const boundary = h("div", "poppy-instruction-boundary");
    append(boundary, stateBadge("completed", "visible boundary"), h("p", "", "This view exposes configured skill handlers, graph topology, repository AGENTS.md, evidence, approvals, and recorded rationale. Hidden chain-of-thought and private system instructions are deliberately outside the product boundary."));
    root.appendChild(boundary);
    return root;
  }

  renderIssues() {
    const root = h("section", "poppy-page");
    append(root, sectionTitle("Maintenance lens", "Deterministic optimization findings", "Rules identify repeated calls, duration regressions, execution failures, stale vaults, and preserved contradictions. Every finding links back to events or source state."));
    const findings = this.state?.findings || [];
    if (!findings.length) return append(root, emptyState("No deterministic issue found", "This does not mean the system is optimal; it means no configured rule fired on visible evidence.")), root;
    const list = h("div", "poppy-findings");
    for (const item of findings) {
      const state = item.severity === "high" ? "failed" : item.severity === "medium" ? "waiting" : "gray";
      const row = h("article", "poppy-finding");
      append(row, stateBadge(state, item.severity), h("div", ""), h("span", "poppy-mono", `${item.event_ids?.length || 0} refs`));
      append(row.children[1], eyebrow(item.kind), h("strong", "", item.message), h("p", "poppy-finding__action", item.action || "Inspect the linked evidence."));
      const inspect = h("button", "poppy-button poppy-button--quiet", this.focusedFinding === item.id ? "Hide references" : "Inspect references");
      inspect.type = "button";
      inspect.setAttribute("aria-expanded", this.focusedFinding === item.id ? "true" : "false");
      inspect.addEventListener("click", () => { this.focusedFinding = this.focusedFinding === item.id ? null : item.id; this.render(); });
      row.children[1].appendChild(inspect);
      list.appendChild(row);
      if (this.focusedFinding === item.id) list.appendChild(this.renderFindingReferences(item));
    }
    root.appendChild(list);
    return root;
  }

  renderFindingReferences(item) {
    const panel = h("div", "poppy-finding-refs");
    panel.setAttribute("role", "region");
    panel.setAttribute("aria-label", `References for ${item.kind}`);
    for (const ref of item.references || []) {
      const button = h("button", "poppy-finding-ref");
      button.type = "button";
      append(button, stateBadge(ref.state || (ref.type === "event" ? "completed" : "gray"), ref.type), h("strong", "", ref.label || ref.id), h("span", "poppy-mono", ref.locator || ref.run_id || ref.id));
      button.addEventListener("click", () => {
        if (ref.type === "event") { this.selectedRun = ref.run_id; this.page = "runs"; }
        else { this.page = "vaults"; }
        this.render();
      });
      panel.appendChild(button);
    }
    if (!(item.references || []).length) panel.appendChild(emptyState("Reference lineage is Gray", "This finding cannot be acted on until a source or event reference is recorded."));
    return panel;
  }

  renderDock() {
    const root = h("section", "poppy-page poppy-page--dock");
    append(root, sectionTitle("Supported task boundary", "Prepare a dashboard-owned Codex task", "The dock creates or resumes a read-only App Server thread. It stores your prompt as a draft but does not submit a turn, preventing an unreviewed tool or external-system action."));
    const layout = h("div", "poppy-dock");
    const form = h("form", "poppy-dock__form");
    const label = h("label", "", "What should Poppy examine?");
    const textarea = h("textarea", "poppy-dock__input");
    textarea.id = "poppy-dock-draft";
    label.htmlFor = textarea.id;
    textarea.rows = 8;
    textarea.placeholder = "Review the latest operational evidence, identify the highest-leverage maintenance issue, and explain the source basis.";
    const threadLabel = h("label", "", "Existing dashboard-owned thread ID (optional)");
    const thread = h("input", "poppy-dock__thread");
    thread.id = "poppy-dock-thread";
    threadLabel.htmlFor = thread.id;
    thread.type = "text";
    thread.placeholder = "Leave blank to prepare a new task";
    const actions = h("div", "poppy-dock__actions");
    const prepare = h("button", "poppy-button", "Prepare read-only task");
    prepare.type = "submit";
    const copy = h("button", "poppy-button poppy-button--quiet", "Copy draft");
    copy.type = "button";
    copy.addEventListener("click", async () => { await navigator.clipboard.writeText(textarea.value); new Notice("Poppy task draft copied."); });
    append(actions, prepare, copy);
    append(form, label, textarea, threadLabel, thread, actions);
    const receipt = h("div", "poppy-dock__receipt");
    receipt.id = "poppy-dock-receipt";
    receipt.setAttribute("role", "status");
    receipt.setAttribute("aria-live", "polite");
    receipt.setAttribute("aria-atomic", "true");
    prepare.setAttribute("aria-describedby", receipt.id);
    append(receipt, stateBadge(this.state?.codex?.connection_state === "connected" ? "completed" : "waiting"), h("h3", "", "Execution remains approval-aware"), h("p", "", "Preparing a thread is a local Codex state change through the official App Server. The draft stays local and is not sent to a model."));
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      prepare.disabled = true;
      prepare.textContent = "Preparing…";
      try {
        const result = await this.api("/api/dock", { method: "POST", body: { draft: textarea.value, thread_id: thread.value.trim() || undefined } });
        clear(receipt);
        append(receipt, stateBadge("waiting", "thread ready"), h("h3", "", result.thread_id || "Thread prepared"), h("p", "", result.next_action || "Continue in Codex."));
        thread.value = result.thread_id || thread.value;
        await this.fetchState(true);
      } catch (error) {
        clear(receipt);
        append(receipt, stateBadge("gray"), h("h3", "", "Task preparation is unavailable"), h("p", "", error instanceof Error ? error.message : String(error)));
      } finally {
        prepare.disabled = false;
        prepare.textContent = "Prepare read-only task";
      }
    });
    append(layout, form, receipt);
    root.appendChild(layout);
    root.appendChild(this.renderCodexBoundary());
    return root;
  }
}

module.exports = class PoppyOpsCockpitPlugin extends Plugin {
  async onload() {
    this.registerView(VIEW_TYPE, (leaf) => new PoppyOpsView(leaf, this));
    this.addRibbonIcon("activity", "Open Poppy Ops Cockpit", () => this.activateView());
    this.addCommand({ id: "open-poppy-ops-cockpit", name: "Open operations cockpit", callback: () => this.activateView() });
  }

  async onunload() {
    this.app.workspace.detachLeavesOfType(VIEW_TYPE);
  }

  async activateView() {
    const existing = this.app.workspace.getLeavesOfType(VIEW_TYPE);
    const leaf = existing[0] || this.app.workspace.getLeaf("tab");
    if (!existing.length) await leaf.setViewState({ type: VIEW_TYPE, active: true });
    this.app.workspace.revealLeaf(leaf);
  }
};

module.exports.VIEW_TYPE = VIEW_TYPE;
module.exports.PoppyOpsView = PoppyOpsView;
module.exports.computeTopology = computeTopology;
module.exports.formatCost = formatCost;
