const Module = require("module");
const path = require("path");
const fs = require("fs");
const { EventEmitter } = require("events");

const vaults = [
  { key: "atlas-demo", name: "Atlas Demo", path: path.resolve("C:\\Synthetic", "AtlasDemo") },
  { key: "beacon-demo", name: "Beacon Demo", path: path.resolve("C:\\Synthetic", "BeaconDemo") },
];
const pluginRoot = path.resolve(__dirname, "..", "dist", "poppy-ops-cockpit");
let nextVault = 0;
let serviceToken = null;
let healthFailures = 0;
let spawnMode = "normal";
let spawnCount = 0;
const children = [];
const eventSources = [];

const originalReadFileSync = fs.readFileSync.bind(fs);
fs.readFileSync = function (file, ...args) {
  if (String(file).endsWith(path.join("config", "bridge.json"))) {
    return JSON.stringify({
      bind: "127.0.0.1",
      port: 7318,
      runtime: { ledger: "runtime/events.jsonl", database: "runtime/poppy-ops.sqlite3" },
      vaults,
    });
  }
  return originalReadFileSync(file, ...args);
};

class Plugin {
  constructor() {
    const vault = vaults[nextVault % vaults.length];
    nextVault += 1;
    this.app = {
      vault: { adapter: { getBasePath: () => vault.path }, getName: () => vault.name },
      workspace: {
        detachLeavesOfType: () => {},
        getLeavesOfType: () => [],
        getLeaf: () => ({ setViewState: async () => {} }),
        revealLeaf: () => {},
      },
    };
    this.manifest = { dir: pluginRoot };
  }
  registerView() {}
  addRibbonIcon() {}
  addCommand() {}
}

class ItemView { constructor() { this.app = {}; } }

global.EventSource = class {
  constructor(url) {
    this.url = url;
    this.listeners = {};
    this.closed = false;
    eventSources.push(this);
  }
  addEventListener(name, callback) { this.listeners[name] = callback; }
  close() { this.closed = true; }
};

function instanceToken(args) {
  return args[args.indexOf("--instance-token") + 1];
}

function runningChildren() {
  return children.filter((child) => child.exitCode === null && child.signalCode === null);
}

const originalLoad = Module._load;
Module._load = function (request, parent, isMain) {
  if (request === "child_process") return {
    spawn: (_command, args) => {
      const child = new EventEmitter();
      child.exitCode = null;
      child.signalCode = null;
      child.token = instanceToken(args);
      child.kill = (signal = "SIGTERM") => {
        if (child.exitCode !== null || child.signalCode !== null) return false;
        child.signalCode = signal;
        if (serviceToken === child.token) serviceToken = null;
        child.emit("exit", null, signal);
        return true;
      };
      children.push(child);
      spawnCount += 1;
      if (spawnMode === "normal") {
        setTimeout(() => {
          if (!serviceToken && child.exitCode === null && child.signalCode === null) serviceToken = child.token;
        }, 5);
      }
      return child;
    },
  };
  if (request === "obsidian") return {
    Plugin,
    ItemView,
    Notice: class {},
    requestUrl: async (options) => {
      if (String(options.url).endsWith("/health")) {
        if (healthFailures > 0) {
          healthFailures -= 1;
          return { status: 503, json: { state: "gray" } };
        }
        return serviceToken
          ? { status: 200, json: { state: "completed", service: "poppy-ops-bridge", instance_token: serviceToken } }
          : { status: 503, json: { state: "gray" } };
      }
      const project = options.headers?.["X-Poppy-Ops-Project"];
      return { status: 200, json: { scope: { mode: "project", project }, vaults: [{ key: project }], runs: [], events: [] } };
    },
  };
  return originalLoad.apply(this, arguments);
};

async function settle(ms = 300) {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

async function loadPair(PluginClass) {
  const first = new PluginClass();
  const second = new PluginClass();
  await Promise.all([first.onload(), second.onload()]);
  await Promise.all([first.ensureBridge(), second.ensureBridge()]);
  return [first, second];
}

async function run() {
  const entry = path.join(pluginRoot, "main.js");
  const PluginClass = require(entry);

  const [atlas, beacon] = await loadPair(PluginClass);
  if (spawnCount !== 2) throw new Error(`Concurrent startup spawned ${spawnCount} children instead of two bounded contenders`);
  if (runningChildren().length !== 1 || !serviceToken) throw new Error("Concurrent startup did not converge to one owned child/service");
  if (![atlas.bridgeStatus.detail, beacon.bridgeStatus.detail].includes("shared localhost bridge won startup")) throw new Error("Losing vault did not record shared-bridge ownership");

  const view = new PluginClass.PoppyOpsView({}, beacon);
  view.connectEvents();
  const source = eventSources[eventSources.length - 1];
  if (!source.url.startsWith("http://127.0.0.1:7318/")) throw new Error(`SSE ignored the configured bridge endpoint: ${source.url}`);
  for (let index = 0; index < 4; index += 1) {
    await view.fetchState(true);
    source.onerror();
  }
  await Promise.all([beacon.ensureBridge(), beacon.ensureBridge(), beacon.ensureBridge()]);
  if (spawnCount !== 2 || runningChildren().length !== 1) throw new Error("Polling or SSE reconnect created an extra bridge child");

  const owner = atlas.bridgeProcess ? atlas : beacon;
  const peer = owner === atlas ? beacon : atlas;
  const originalOwnerChild = owner.bridgeProcess;
  const beforeTransient = spawnCount;
  healthFailures = 1;
  await owner.ensureBridge();
  if (spawnCount !== beforeTransient + 1) throw new Error("Transient owner health failure did not exercise one bounded contender");
  if (owner.bridgeProcess !== originalOwnerChild || owner.bridgeProcessToken !== serviceToken) throw new Error("Losing contender cleared or replaced the healthy owner handle");
  if (owner.bridgeStartupChildren.size !== 0 || runningChildren().length !== 1) throw new Error("Transient-health contender did not exit cleanly");
  if (owner.bridgeStatus.detail !== "owned localhost bridge recovered") throw new Error(`Owner recovery was not recorded: ${owner.bridgeStatus.detail}`);
  await owner.onunload();
  if (runningChildren().length !== 0 || serviceToken) throw new Error("Owner unload left its bridge child running");
  source.onerror();
  const beforePeerRecovery = spawnCount;
  await peer.ensureBridge();
  if (runningChildren().length !== 1 || !serviceToken || spawnCount !== beforePeerRecovery + 1) throw new Error("Remaining vault did not recover exactly one bridge after owner reload");
  await peer.onunload();
  view.onClose();
  if (runningChildren().length !== 0 || serviceToken) throw new Error("Peer unload left a recovered bridge child running");

  const beforeReload = spawnCount;
  const [reloadedAtlas, reloadedBeacon] = await loadPair(PluginClass);
  if (spawnCount !== beforeReload + 2 || runningChildren().length !== 1) throw new Error("Simultaneous two-vault reload did not converge to one bridge child");
  await Promise.all([reloadedAtlas.onunload(), reloadedBeacon.onunload()]);
  if (runningChildren().length !== 0 || serviceToken) throw new Error("Simultaneous two-vault shutdown left an orphan child");

  spawnMode = "offline";
  const timedOut = new PluginClass();
  await timedOut.onload();
  timedOut.bridgeStartupAttempts = 2;
  timedOut.bridgeStartupDelayMs = 1;
  await timedOut.ensureBridge();
  if (!String(timedOut.bridgeStatus.detail).includes("timed out")) throw new Error("Offline startup did not report a bounded timeout");
  if (runningChildren().length !== 0) throw new Error("Timed-out startup child survived cleanup");
  await timedOut.onunload();

  process.stdout.write(JSON.stringify({
    status: "pass",
    concurrent_startup: { contenders: 2, survivors: 1 },
    repeated_poll_sse_spawn_delta: 0,
    transient_health_contender: { owner_handle_preserved: true, unload_survivors: 0 },
    reload_cycles: 2,
    timeout_child_survivors: 0,
    final_owned_survivors: runningChildren().length,
  }) + "\n");
}

run().catch((error) => { console.error(error.stack || error); process.exit(1); });
