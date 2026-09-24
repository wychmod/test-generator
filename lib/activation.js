const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const SKILL_NAME = "testcase-generator";

const ENVIRONMENTS = {
  claude: {
    localPath: [".claude", "skills", SKILL_NAME],
    globalPath: [".claude", "skills", SKILL_NAME],
  },
  codebuddy: {
    localPath: [".codebuddy", "skills", SKILL_NAME],
    globalPath: [".codebuddy", "skills", SKILL_NAME],
  },
  codex: {
    localPath: [".agents", "skills", SKILL_NAME],
    globalPath: [".codex", "skills", SKILL_NAME],
    entry: {
      source: path.join("adapters", "codex", "AGENTS.md"),
      target: "AGENTS.md",
    },
  },
  cursor: {
    localPath: [".cursor", "rules"],
    globalPath: [".cursor", "rules"],
    entry: {
      source: path.join("adapters", "cursor", "cursorrules.md"),
      target: "cursorrules",
    },
  },
  openclaw: {
    localPath: ["skills", SKILL_NAME],
    globalPath: [".openclaw", "skills", SKILL_NAME],
    entry: {
      source: path.join("adapters", "openclaw", "skill.md"),
      target: "skill.md",
    },
  },
  qoder: {
    localPath: [".qoder", "skills", SKILL_NAME],
    globalPath: [".qoder", "skills", SKILL_NAME],
  },
  trae: {
    localPath: [".trae", "skills", SKILL_NAME],
    globalPath: [".trae", "skills", SKILL_NAME],
  },
  windsurf: {
    localPath: [".windsurf", "rules"],
    globalPath: [".windsurf", "rules"],
    entry: {
      source: path.join("adapters", "windsurf", "windsurfrules.md"),
      target: "windsurfrules",
    },
  },
};

const ENV_ALIASES = {
  agent: "codex",
  agents: "codex",
  "claude-code": "claude",
  "open-claw": "openclaw",
};

function normalizeEnvironment(env) {
  const normalized = String(env || "").trim().toLowerCase();
  return ENV_ALIASES[normalized] || normalized;
}

function assertSupportedEnvironment(env) {
  const normalized = normalizeEnvironment(env);
  if (!Object.hasOwn(ENVIRONMENTS, normalized)) {
    const names = Object.keys(ENVIRONMENTS).join(", ");
    throw new Error(`Unsupported environment '${env}'. Supported environments: ${names}`);
  }
  return normalized;
}

function readManifest(packageRoot) {
  const manifestPath = path.join(packageRoot, "skill.manifest.json");
  if (!fs.existsSync(manifestPath)) {
    throw new Error(`Missing manifest: ${manifestPath}`);
  }
  return JSON.parse(fs.readFileSync(manifestPath, "utf8"));
}

function walkFiles(directory) {
  if (!fs.existsSync(directory)) {
    return [];
  }

  const files = [];
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const absolutePath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...walkFiles(absolutePath));
    } else if (entry.isFile()) {
      files.push(absolutePath);
    }
  }
  return files;
}

function normalizeArchivePath(filePath) {
  return filePath.split(path.sep).join("/");
}

function collectRuntimeFiles(packageRoot) {
  const manifest = readManifest(packageRoot);
  const runtimeEntries = [
    ...(manifest["运行时文件"] || []),
    "DISTRIBUTION.md",
    "skill.manifest.json",
  ];
  const files = new Set();

  for (const entry of runtimeEntries) {
    if (entry.endsWith("/**")) {
      const directory = path.join(packageRoot, entry.slice(0, -3));
      for (const absolutePath of walkFiles(directory)) {
        files.add(normalizeArchivePath(path.relative(packageRoot, absolutePath)));
      }
      continue;
    }

    const absolutePath = path.join(packageRoot, entry);
    if (!fs.existsSync(absolutePath)) {
      continue;
    }
    const stat = fs.statSync(absolutePath);
    if (stat.isDirectory()) {
      for (const child of walkFiles(absolutePath)) {
        files.add(normalizeArchivePath(path.relative(packageRoot, child)));
      }
    } else if (stat.isFile()) {
      files.add(normalizeArchivePath(entry));
    }
  }

  return [...files].sort();
}

function resolveActivationTarget(env, options = {}) {
  const environment = assertSupportedEnvironment(env);
  if (options.target) {
    return path.resolve(String(options.target));
  }

  const config = ENVIRONMENTS[environment];
  const base = options.global ? os.homedir() : path.resolve(options.cwd || process.cwd());
  const segments = options.global ? config.globalPath : config.localPath;
  return path.join(base, ...segments);
}

function copyRuntimeFile(packageRoot, targetRoot, relativePath) {
  const source = path.join(packageRoot, relativePath);
  const target = path.join(targetRoot, relativePath);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.copyFileSync(source, target);
}

function findCaseInsensitiveCollision(entryTarget, runtimeFiles) {
  if (!entryTarget) {
    return null;
  }

  const lowered = entryTarget.toLowerCase();
  for (const file of runtimeFiles) {
    // Only top-level runtime files can collide with a host entry file.
    if (file.includes("/")) {
      continue;
    }
    // Same name, same case -> this is the entry itself, not a collision.
    if (file === entryTarget) {
      continue;
    }
    if (file.toLowerCase() === lowered) {
      return file;
    }
  }
  return null;
}

function writeHostEntry(environment, packageRoot, targetRoot, runtimeFiles = []) {
  const entry = ENVIRONMENTS[environment].entry;
  if (!entry) {
    return { target: null, collision: null };
  }

  const source = path.join(packageRoot, entry.source);
  if (!fs.existsSync(source)) {
    return { target: null, collision: null };
  }

  // Windows and macOS collapse `skill.md` and `SKILL.md` onto the same file.
  // Copying the host entry would then silently destroy the canonical SKILL.md
  // that was just written, so keep the canonical file and report the clash
  // instead of overwriting it.
  const conflict = findCaseInsensitiveCollision(entry.target, runtimeFiles);
  if (conflict) {
    return { target: null, collision: { target: entry.target, conflict } };
  }

  const target = path.join(targetRoot, entry.target);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.copyFileSync(source, target);
  return { target: entry.target, collision: null };
}

function activateEnvironment(options) {
  const environment = assertSupportedEnvironment(options.env);
  const packageRoot = path.resolve(options.packageRoot || path.join(__dirname, ".."));
  const target = resolveActivationTarget(environment, options);
  const files = collectRuntimeFiles(packageRoot);

  if (!options.dryRun) {
    fs.mkdirSync(target, { recursive: true });
    for (const file of files) {
      copyRuntimeFile(packageRoot, target, file);
    }
  }

  let entry = null;
  let entryCollision = null;

  if (options.dryRun) {
    entry = ENVIRONMENTS[environment].entry?.target || null;
  } else {
    const written = writeHostEntry(environment, packageRoot, target, files);
    entry = written.target;
    entryCollision = written.collision;
  }

  return {
    copied: files.length,
    entry,
    entryCollision,
    environment,
    target,
  };
}

function supportedEnvironments() {
  return Object.keys(ENVIRONMENTS);
}

module.exports = {
  ENVIRONMENTS,
  SKILL_NAME,
  activateEnvironment,
  collectRuntimeFiles,
  findCaseInsensitiveCollision,
  normalizeEnvironment,
  resolveActivationTarget,
  supportedEnvironments,
};
