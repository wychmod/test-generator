const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const SKILL_NAME = "testcase-generator";

// 宿主注册表。仅登记「有宿主官方文档佐证」的技能目录路径 —— 第三方 CLI
// 的汇总清单（如 Vercel add-skill 的 25 个 agent）只用于交叉核对，不作为依据。
//
// 绝大多数现代宿主已直接遵循 Agent Skills 标准布局（`<dir>/skills/<name>/SKILL.md`），
// 因此本技能无需格式转换即可被发现。少数宿主仍使用「单一规则文件」约定
// （Cursor 的 `.cursorrules`、Windsurf 的 `.windsurfrules`），它们通过 `entry` 声明。
const ENVIRONMENTS = {
  amp: {
    // Amp（Sourcegraph）官方：`.agents/skills/` ↔ `~/.config/agents/skills/`
    localPath: [".agents", "skills", SKILL_NAME],
    globalPath: [path.join(".config", "agents"), "skills", SKILL_NAME],
  },
  antigravity: {
    // Google Antigravity 官方：`.agent/skills/` ↔ `~/.gemini/antigravity/skills/`
    localPath: [".agent", "skills", SKILL_NAME],
    globalPath: [path.join(".gemini", "antigravity"), "skills", SKILL_NAME],
  },
  claude: {
    localPath: [".claude", "skills", SKILL_NAME],
    globalPath: [".claude", "skills", SKILL_NAME],
  },
  clawdbot: {
    // Clawdbot：技能直接放在仓库根的 `skills/`；用户级 `~/.clawdbot/skills/`
    localPath: ["skills", SKILL_NAME],
    globalPath: [".clawdbot", "skills", SKILL_NAME],
  },
  cline: {
    // Cline 官方（3.48.0 起）：`.cline/skills/` ↔ `~/.cline/skills/`
    localPath: [".cline", "skills", SKILL_NAME],
    globalPath: [".cline", "skills", SKILL_NAME],
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
  commandcode: {
    // Command Code 官方（commandcode.ai/docs/skills）：
    // 项目 `.commandcode/skills/` ↔ 用户 `~/.commandcode/skills/`
    localPath: [".commandcode", "skills", SKILL_NAME],
    globalPath: [".commandcode", "skills", SKILL_NAME],
  },
  cursor: {
    localPath: [".cursor", "rules"],
    globalPath: [".cursor", "rules"],
    entry: {
      source: path.join("adapters", "cursor", "cursorrules.md"),
      target: "cursorrules",
    },
  },
  droid: {
    // Factory Droid 官方：`.factory/skills/` ↔ `~/.factory/skills/`
    localPath: [".factory", "skills", SKILL_NAME],
    globalPath: [".factory", "skills", SKILL_NAME],
  },
  gemini: {
    // Gemini CLI 官方：`.gemini/skills/` ↔ `~/.gemini/skills/`
    localPath: [".gemini", "skills", SKILL_NAME],
    globalPath: [".gemini", "skills", SKILL_NAME],
  },
  githubcopilot: {
    // GitHub Copilot 官方：`.github/skills/` ↔ `~/.copilot/skills/`
    localPath: [path.join(".github"), "skills", SKILL_NAME],
    globalPath: [".copilot", "skills", SKILL_NAME],
  },
  goose: {
    // Goose（Block）官方：`.goose/skills/` ↔ `~/.config/goose/skills/`
    localPath: [".goose", "skills", SKILL_NAME],
    globalPath: [path.join(".config", "goose"), "skills", SKILL_NAME],
  },
  kilocode: {
    // Kilo Code 官方（kilo.ai/docs）：`.kilocode/skills/`
    localPath: [".kilocode", "skills", SKILL_NAME],
    globalPath: [".kilocode", "skills", SKILL_NAME],
  },
  kiro: {
    // Kiro 官方（kiro.dev/docs/skills）：`.kiro/skills/` ↔ `~/.kiro/skills/`
    localPath: [".kiro", "skills", SKILL_NAME],
    globalPath: [".kiro", "skills", SKILL_NAME],
  },
  mcpjam: {
    // MCPJam 官方：`.mcpjam/skills/` ↔ `~/.mcpjam/skills/`
    localPath: [".mcpjam", "skills", SKILL_NAME],
    globalPath: [".mcpjam", "skills", SKILL_NAME],
  },
  openclaw: {
    // 注意：本地目标不能是仓库根的 `skills/` —— 那已经是 canonical 技能树
    // （Agent Skills 标准布局），再往里写就等于用镜像覆盖源文件本身。
    localPath: [".openclaw", "skills", SKILL_NAME],
    globalPath: [".openclaw", "skills", SKILL_NAME],
    entry: {
      source: path.join("adapters", "openclaw", "skill.md"),
      target: "skill.md",
    },
  },
  opencode: {
    // OpenCode 遵循 Agent Skills 标准布局：`.opencode/skills/<name>/SKILL.md`。
    // 它同时支持 `plugin/` 与 `skills/` 两种扩展位，此处用后者（与本技能布局一致）。
    localPath: [".opencode", "skills", SKILL_NAME],
    globalPath: [path.join(".config", "opencode"), "skills", SKILL_NAME],
  },
  openhands: {
    // OpenHands 官方：`.openhands/skills/` ↔ `~/.openhands/skills/`
    localPath: [".openhands", "skills", SKILL_NAME],
    globalPath: [".openhands", "skills", SKILL_NAME],
  },
  pi: {
    // Pi 官方：`.pi/skills/` ↔ `~/.pi/agent/skills/`
    localPath: [".pi", "skills", SKILL_NAME],
    globalPath: [path.join(".pi", "agent"), "skills", SKILL_NAME],
  },
  qoder: {
    localPath: [".qoder", "skills", SKILL_NAME],
    globalPath: [".qoder", "skills", SKILL_NAME],
  },
  qwen: {
    // Qwen Code 官方：`.qwen/skills/` ↔ `~/.qwen/skills/`
    localPath: [".qwen", "skills", SKILL_NAME],
    globalPath: [".qwen", "skills", SKILL_NAME],
  },
  roo: {
    // Roo Code 官方（docs.roocode.com）：`.roo/skills/` ↔ `~/.roo/skills/`
    localPath: [".roo", "skills", SKILL_NAME],
    globalPath: [".roo", "skills", SKILL_NAME],
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
  zencoder: {
    // Zencoder 官方：`.zencoder/skills/` ↔ `~/.zencoder/skills/`
    localPath: [".zencoder", "skills", SKILL_NAME],
    globalPath: [".zencoder", "skills", SKILL_NAME],
  },
};

const ENV_ALIASES = {
  agent: "codex",
  agents: "codex",
  "claude-code": "claude",
  "command-code": "commandcode",
  copilot: "githubcopilot",
  "gemini-cli": "gemini",
  "github-copilot": "githubcopilot",
  "kilo-code": "kilocode",
  "kiro-cli": "kiro",
  "open-claw": "openclaw",
  "open-code": "opencode",
  "open-hands": "openhands",
  "qwen-code": "qwen",
  "roo-code": "roo",
  sst: "opencode",
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

// manifest 字段名常量 —— 与 devtools/manifest.py 的 FIELD_* 保持同名同义。
// JS 侧与 Python 侧读取同一个 JSON，字段名必须只在这里各声明一次，
// 避免"改了 manifest 键名、只更新了一半消费者"的静默漂移。
const MANIFEST_FIELDS = {
  version: "版本",
  entry: "入口文件",
  runtimeFiles: "运行时文件",
  hostEntries: "宿主适配入口",
  excludes: "分发排除",
  npmEntry: "Node.js安装入口",
  npmEnvironments: "支持环境",
};

function readManifest(packageRoot) {
  const manifestPath = path.join(packageRoot, "skill.manifest.json");
  if (!fs.existsSync(manifestPath)) {
    throw new Error(`Missing manifest: ${manifestPath}`);
  }
  const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  if (manifest === null || typeof manifest !== "object" || Array.isArray(manifest)) {
    throw new Error(`Manifest root must be a JSON object: ${manifestPath}`);
  }
  return manifest;
}

/** 运行时文件白名单（manifest 的「运行时文件」字段）。 */
function runtimeEntries(manifest) {
  return manifest[MANIFEST_FIELDS.runtimeFiles] || [];
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
  // LICENSE 与 DISTRIBUTION.md / manifest 同属"随包分发但不属于技能运行时内容"，
  // 因此在这里追加，而不写进 manifest 的"运行时文件"。
  const entries = [
    ...runtimeEntries(manifest),
    "DISTRIBUTION.md",
    "LICENSE",
    "skill.manifest.json",
  ];
  const files = new Set();

  for (const entry of entries) {
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

// 激活状态文件：记录上一次写入的文件清单。
// 只用于清理「我们自己写过、但本次不再需要」的文件 —— 绝不触碰用户自己的内容。
const ACTIVATION_STATE_FILE = ".activated-files.json";

function readActivationState(targetRoot) {
  const statePath = path.join(targetRoot, ACTIVATION_STATE_FILE);
  if (!fs.existsSync(statePath)) {
    return [];
  }
  try {
    const parsed = JSON.parse(fs.readFileSync(statePath, "utf8"));
    return Array.isArray(parsed.files) ? parsed.files : [];
  } catch {
    return [];
  }
}

function writeActivationState(targetRoot, files) {
  const statePath = path.join(targetRoot, ACTIVATION_STATE_FILE);
  fs.writeFileSync(statePath, `${JSON.stringify({ files }, null, 2)}\n`, "utf8");
}

function pruneStaleFiles(targetRoot, previouslyActivated, expectedFiles) {
  const expected = new Set(expectedFiles);
  const removed = [];

  for (const relativePath of previouslyActivated) {
    if (expected.has(relativePath)) {
      continue;
    }
    const absolutePath = path.join(targetRoot, relativePath);
    if (fs.existsSync(absolutePath)) {
      fs.rmSync(absolutePath, { force: true });
      removed.push(relativePath);
    }
  }

  return removed;
}

function collectFiles(directory, base = directory) {
  if (!fs.existsSync(directory)) {
    return [];
  }
  const found = [];
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const absolutePath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      found.push(...collectFiles(absolutePath, base));
    } else if (entry.isFile()) {
      found.push(path.relative(base, absolutePath).split(path.sep).join("/"));
    }
  }
  return found;
}

/**
 * 把「完全属于本 Skill 的目录」对齐到期望文件集合：删除任何不再需要的条目。
 *
 * 为什么需要这一层：仅靠状态文件只能清理"本工具以前写过"的文件，
 * 无法处理从更早版本（尚无状态文件）升级而来的残留 —— 而那正是所有
 * 现存用户升级时的处境。旧版布局留在宿主目录里的顶层 `SKILL.md` 会让
 * 宿主加载到过期内容，属于必须消除的漂移。
 *
 * 只在目录归属明确时才调用；共享目录（`.cursor/rules`、`.windsurf/rules`）
 * 或用户通过 `--target` 指定的目录绝不使用。
 */
function alignOwnedDirectory(targetRoot, expectedFiles) {
  const expected = new Set([...expectedFiles, ACTIVATION_STATE_FILE]);
  const removed = [];

  for (const relativePath of collectFiles(targetRoot)) {
    if (expected.has(relativePath)) {
      continue;
    }
    fs.rmSync(path.join(targetRoot, relativePath), { force: true });
    removed.push(relativePath);
  }

  if (removed.length > 0) {
    removeEmptyDirectories(targetRoot);
  }

  return removed;
}

/**
 * 目标目录是否完全归本 Skill 所有。
 *
 * 以「激活路径的末段是否就是技能目录名」判定：`.claude/skills/testcase-generator`
 * 归我们所有，`.cursor/rules` 是用户共享目录，不是。
 * `--target` 由用户指定，归属无法断言，一律保守处理。
 */
function ownsTargetDirectory(environment, options = {}) {
  if (options.target) {
    return false;
  }
  const segments = ENVIRONMENTS[environment].localPath;
  return segments[segments.length - 1] === SKILL_NAME;
}

function removeEmptyDirectories(directory, keepRoot = true) {
  if (!fs.existsSync(directory)) {
    return;
  }
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    if (entry.isDirectory()) {
      removeEmptyDirectories(path.join(directory, entry.name), false);
    }
  }
  if (!keepRoot && fs.readdirSync(directory).length === 0) {
    fs.rmdirSync(directory);
  }
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

  let pruned = [];

  if (!options.dryRun) {
    fs.mkdirSync(target, { recursive: true });

    // 先清理上一次激活写入、而本次已不再需要的文件。
    // 只删状态文件里记录过的路径，因此不会影响用户放在同一目录下的自有内容
    // （`.cursor/rules` 与 `.windsurf/rules` 是共享目录，这点尤其重要）。
    pruned = pruneStaleFiles(target, readActivationState(target), files);
    if (pruned.length > 0) {
      removeEmptyDirectories(target);
    }

    // 归属明确的目录再做一次声明式对齐，消除「状态文件存在之前」遗留的旧内容
    // —— 这是从 <2.3.0 升级时的主要漂移来源。
    if (ownsTargetDirectory(environment, options)) {
      const aligned = alignOwnedDirectory(target, files);
      pruned = [...pruned, ...aligned];
    }

    for (const file of files) {
      copyRuntimeFile(packageRoot, target, file);
    }
    writeActivationState(target, files);
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
    pruned,
    target,
  };
}

function supportedEnvironments() {
  return Object.keys(ENVIRONMENTS);
}

module.exports = {
  ACTIVATION_STATE_FILE,
  ENVIRONMENTS,
  MANIFEST_FIELDS,
  SKILL_NAME,
  activateEnvironment,
  alignOwnedDirectory,
  collectRuntimeFiles,
  findCaseInsensitiveCollision,
  normalizeEnvironment,
  ownsTargetDirectory,
  pruneStaleFiles,
  readActivationState,
  readManifest,
  resolveActivationTarget,
  runtimeEntries,
  supportedEnvironments,
};
