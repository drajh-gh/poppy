const Module = require("module");
const path = require("path");

let registeredType = null;
let registeredFactory = null;
let command = null;
let ribbon = null;
let activated = null;
let revealed = false;

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

class ItemView { constructor(leaf) { this.leaf = leaf; } }

const originalLoad = Module._load;
Module._load = function (request, parent, isMain) {
  if (request === "obsidian") return { Plugin, ItemView, Notice: class {}, requestUrl: async () => ({ status: 200, json: {} }) };
  return originalLoad.apply(this, arguments);
};

async function run() {
  const entry = path.resolve(__dirname, "..", "dist", "poppy-ops-cockpit", "main.js");
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
  process.stdout.write(JSON.stringify({ status: "pass", registeredType, command: command.id, ribbon: ribbon.icon, activated }) + "\n");
}

run().catch((error) => { console.error(error.stack || error); process.exit(1); });

