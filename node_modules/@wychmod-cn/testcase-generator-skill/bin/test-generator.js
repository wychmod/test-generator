#!/usr/bin/env node

const path = require("node:path");

const {
  activateEnvironment,
  supportedEnvironments,
} = require("../lib/activation");

const PACKAGE_ROOT = path.resolve(__dirname, "..");

function printHelp() {
  const environments = supportedEnvironments().join(", ");
  console.log(`test-generator

Usage:
  test-generator activate <environment> [-g] [--target <path>] [--dry-run]
  test-generator environments

Options:
  -g, --global  Activate into the user-level host directory

Environments:
  ${environments}
`);
}

function parseActivateArgs(args) {
  const parsed = {
    dryRun: false,
    global: false,
    target: null,
  };
  const positional = [];

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--global" || arg === "-g") {
      parsed.global = true;
    } else if (arg === "--dry-run") {
      parsed.dryRun = true;
    } else if (arg === "--target") {
      index += 1;
      if (!args[index]) {
        throw new Error("--target requires a path");
      }
      parsed.target = args[index];
    } else if (arg.startsWith("--target=")) {
      parsed.target = arg.slice("--target=".length);
    } else if (arg === "--help" || arg === "-h") {
      parsed.help = true;
    } else if (arg.startsWith("-")) {
      throw new Error(`Unknown option: ${arg}`);
    } else {
      positional.push(arg);
    }
  }

  parsed.env = positional[0];
  if (!parsed.help && !parsed.env) {
    throw new Error("activate requires an environment");
  }
  return parsed;
}

function run(argv = process.argv.slice(2)) {
  const [command, ...args] = argv;

  if (!command || command === "--help" || command === "-h") {
    printHelp();
    return 0;
  }

  if (command === "environments") {
    console.log(supportedEnvironments().join("\n"));
    return 0;
  }

  if (command === "activate") {
    const options = parseActivateArgs(args);
    if (options.help) {
      printHelp();
      return 0;
    }

    const result = activateEnvironment({
      cwd: process.cwd(),
      dryRun: options.dryRun,
      env: options.env,
      global: options.global,
      packageRoot: PACKAGE_ROOT,
      target: options.target,
    });

    const action = options.dryRun ? "Would activate" : "Activated";
    console.log(`${action} ${result.environment} skill at ${result.target}`);
    console.log(`Runtime files: ${result.copied}`);
    if (result.entry) {
      console.log(`Host entry: ${result.entry}`);
    }
    return 0;
  }

  throw new Error(`Unknown command: ${command}`);
}

if (require.main === module) {
  try {
    process.exitCode = run();
  } catch (error) {
    console.error(error.message);
    console.error("Run 'test-generator --help' for usage.");
    process.exitCode = 1;
  }
}

module.exports = {
  parseActivateArgs,
  run,
};
