const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

const {
  ACTIVATION_STATE_FILE,
  ENVIRONMENTS,
  activateEnvironment,
  collectRuntimeFiles,
  findCaseInsensitiveCollision,
  resolveActivationTarget,
  supportedEnvironments,
} = require("../lib/activation");

const ROOT = path.resolve(__dirname, "..");
const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, "skill.manifest.json"), "utf8"));
const hostEntries = manifest["宿主适配入口"] || {};

// 技能运行时内容的唯一位置（Agent Skills 标准布局）。
const SKILL_ENTRY = ["skills", "testcase-generator", "SKILL.md"];

function repoPath(relative) {
  return path.join(ROOT, ...relative.split("/"));
}

// --- manifest ↔ activation registry ----------------------------------------

test("manifest host entries and the activation registry expose the same environments", () => {
  const registry = supportedEnvironments().sort();
  const declared = Object.keys(hostEntries).sort();

  assert.deepEqual(
    declared,
    registry,
    "skill.manifest.json 的 宿主适配入口 与 lib/activation.js 的 ENVIRONMENTS 必须一一对应",
  );
});

test("every declared host adapter entry file exists on disk", () => {
  for (const [environment, relative] of Object.entries(hostEntries)) {
    assert.ok(
      fs.existsSync(repoPath(relative)),
      `${environment}: 适配入口文件缺失 -> ${relative}`,
    );
  }
});

test("every environment has an adapter directory named after it", () => {
  for (const environment of supportedEnvironments()) {
    assert.ok(
      fs.statSync(path.join(ROOT, "adapters", environment)).isDirectory(),
      `adapters/${environment}/ 目录缺失`,
    );
  }
});

// --- registry ↔ on-disk adapter --------------------------------------------

test("each environment's declared entry points at its own adapter file", () => {
  for (const environment of supportedEnvironments()) {
    const declared = hostEntries[environment];
    assert.ok(declared, `${environment} 未在 manifest 中声明适配入口`);
    assert.ok(
      declared.startsWith(`adapters/${environment}/`),
      `${environment}: 适配入口 ${declared} 不在 adapters/${environment}/ 下`,
    );
  }
});

test("hosts with a dedicated entry file declare that exact file", () => {
  for (const environment of supportedEnvironments()) {
    const entry = ENVIRONMENTS[environment].entry;
    if (!entry) {
      continue;
    }
    const normalized = entry.source.split(path.sep).join("/");
    assert.equal(
      hostEntries[environment],
      normalized,
      `${environment}: manifest 入口与 activation entry.source 不一致`,
    );
  }
});

test("hosts without a dedicated entry file fall back to the canonical SKILL.md", () => {
  for (const environment of supportedEnvironments()) {
    if (ENVIRONMENTS[environment].entry) {
      continue;
    }
    assert.equal(
      hostEntries[environment],
      `adapters/${environment}/SKILL.md`,
      `${environment}: 无专用入口文件时，适配入口应指向 adapters/${environment}/SKILL.md`,
    );
  }
});

// --- end-to-end activation -------------------------------------------------

test("activating each environment writes its host entry file", () => {
  for (const environment of supportedEnvironments()) {
    const cwd = fs.mkdtempSync(path.join(os.tmpdir(), `test-generator-${environment}-`));

    const result = activateEnvironment({
      cwd,
      env: environment,
      packageRoot: ROOT,
    });

    assert.equal(result.environment, environment);
    assert.ok(result.copied > 0, `${environment}: 没有复制任何运行时文件`);

    const entryTarget = ENVIRONMENTS[environment].entry?.target;
    if (entryTarget) {
      assert.ok(
        fs.existsSync(path.join(result.target, entryTarget)),
        `${environment}: 宿主入口 ${entryTarget} 未写入`,
      );
    }

    // 无论哪个宿主，技能入口都必须落地 —— 它是所有降级路径的锚点。
    assert.ok(
      fs.existsSync(path.join(result.target, ...SKILL_ENTRY)),
      `${environment}: 运行时缺少技能入口 ${SKILL_ENTRY.join("/")}`,
    );
  }
});

// --- case-insensitive filesystem safety ------------------------------------

test("the standard layout exposes no host entry that collides by case", () => {
  const runtimeFiles = collectRuntimeFiles(ROOT);

  // 技能入口迁到 skills/testcase-generator/SKILL.md 之后，顶层不再有
  // SKILL.md，因此 OpenClaw 的 skill.md 不会再与它同路 —— 这正好说明
  // 采用标准布局顺带消除了当初那个大小写冲突。
  for (const environment of supportedEnvironments()) {
    const entryTarget = ENVIRONMENTS[environment].entry?.target;
    assert.equal(
      findCaseInsensitiveCollision(entryTarget, runtimeFiles),
      null,
      `${environment}: 入口 ${entryTarget} 不应与任何顶层运行时文件冲突`,
    );
  }
});

test("case-insensitive collision detection still guards the primitive", () => {
  // 真实布局已无冲突，因此用合成清单覆盖检测逻辑本身，确保守卫不会失效。
  assert.equal(findCaseInsensitiveCollision("skill.md", ["SKILL.md"]), "SKILL.md");
  assert.equal(findCaseInsensitiveCollision("SKILL.md", ["SKILL.md"]), null);
  assert.equal(findCaseInsensitiveCollision("cursorrules", ["SKILL.md"]), null);
  // 嵌套路径不参与判定：只有顶层文件才可能与宿主入口同路
  assert.equal(findCaseInsensitiveCollision("skill.md", ["skills/testcase-generator/SKILL.md"]), null);
});

test("activating openclaw writes its entry without touching the skill tree", () => {
  const cwd = fs.mkdtempSync(path.join(os.tmpdir(), "test-generator-openclaw-"));
  const result = activateEnvironment({ cwd, env: "openclaw", packageRoot: ROOT });

  // 标准布局下不再冲突，入口应正常写入
  assert.equal(result.entry, "skill.md");
  assert.equal(result.entryCollision, null);
  assert.ok(fs.existsSync(path.join(result.target, "skill.md")));

  // 不变式（当初加冲突保护就是为了守住它）：技能入口内容必须完好，
  // 不能被适配器覆盖。用 \r?\n 兼容 Windows 的 CRLF 检出。
  const canonical = fs.readFileSync(path.join(result.target, ...SKILL_ENTRY), "utf8");
  assert.match(canonical, /^---\r?\nname: testcase-generator\r?\n/);
  assert.match(canonical, new RegExp(`^version: ${manifest["版本"]}\\r?$`, "m"));
  assert.doesNotMatch(canonical, /OpenClaw Skill Adapter/);
});

test("hosts whose entry name does not collide still get their entry file", () => {
  const expectations = { codex: "AGENTS.md", cursor: "cursorrules", windsurf: "windsurfrules" };

  for (const [environment, entryName] of Object.entries(expectations)) {
    const cwd = fs.mkdtempSync(path.join(os.tmpdir(), `test-generator-${environment}-entry-`));
    const result = activateEnvironment({ cwd, env: environment, packageRoot: ROOT });

    assert.equal(result.entry, entryName, `${environment} 入口文件名不符`);
    assert.equal(result.entryCollision, null, `${environment} 不应报告冲突`);
    assert.ok(fs.existsSync(path.join(result.target, entryName)));
  }
});

// --- stale file pruning ----------------------------------------------------

test("re-activation prunes files it previously wrote but no longer needs", () => {
  const cwd = fs.mkdtempSync(path.join(os.tmpdir(), "test-generator-prune-"));
  const first = activateEnvironment({ cwd, env: "claude", packageRoot: ROOT });

  // 模拟旧版本布局留在宿主目录里的文件（例如迁移前的顶层 SKILL.md）
  const stale = "legacy-top-level-SKILL.md";
  fs.writeFileSync(path.join(first.target, stale), "old content", "utf8");
  const statePath = path.join(first.target, ACTIVATION_STATE_FILE);
  const state = JSON.parse(fs.readFileSync(statePath, "utf8"));
  state.files.push(stale);
  fs.writeFileSync(statePath, JSON.stringify(state, null, 2), "utf8");

  const second = activateEnvironment({ cwd, env: "claude", packageRoot: ROOT });

  assert.deepEqual(second.pruned, [stale]);
  assert.equal(
    fs.existsSync(path.join(first.target, stale)),
    false,
    "上次激活写过的陈旧文件必须被清理，否则宿主可能加载到旧内容",
  );
});

test("pruning never touches files the user placed in a shared target directory", () => {
  // `.cursor/rules` / `.windsurf/rules` 是用户共享目录，清理必须只针对自己写过的文件
  const cwd = fs.mkdtempSync(path.join(os.tmpdir(), "test-generator-shared-"));
  const result = activateEnvironment({ cwd, env: "cursor", packageRoot: ROOT });

  const userRule = path.join(result.target, "my-own-team-rules.mdc");
  fs.writeFileSync(userRule, "user content", "utf8");

  activateEnvironment({ cwd, env: "cursor", packageRoot: ROOT });

  assert.ok(fs.existsSync(userRule), "用户自有规则文件必须保留");
});

test("activation realigns an owned directory, removing older layout leftovers", () => {
  // 模拟 <2.3.0 升级：旧布局的顶层 SKILL.md / prompts/ 等残留在宿主目录里
  const cwd = fs.mkdtempSync(path.join(os.tmpdir(), "test-generator-realign-"));
  const target = resolveActivationTarget("claude", { cwd });
  fs.mkdirSync(path.join(target, "prompts"), { recursive: true });
  fs.writeFileSync(path.join(target, "SKILL.md"), "---\nversion: 2.2.0\n---\n", "utf8");
  fs.writeFileSync(path.join(target, "prompts", "phase0.md"), "old content", "utf8");

  const result = activateEnvironment({ cwd, env: "claude", packageRoot: ROOT });

  assert.ok(result.pruned.includes("SKILL.md"), "陈旧顶层 SKILL.md 必须被清理");
  assert.ok(result.pruned.includes("prompts/phase0.md"), "陈旧 prompts/ 必须被清理");
  assert.equal(fs.existsSync(path.join(target, "SKILL.md")), false);
  assert.equal(fs.existsSync(path.join(target, "prompts")), false);
  assert.ok(fs.existsSync(path.join(target, ...SKILL_ENTRY)), "新技能入口必须在位");
});

test("a user-specified target directory is never realigned", () => {
  const cwd = fs.mkdtempSync(path.join(os.tmpdir(), "test-generator-custom-"));
  const custom = path.join(cwd, "custom-dir");
  fs.mkdirSync(custom, { recursive: true });
  const keep = path.join(custom, "keep-me.txt");
  fs.writeFileSync(keep, "user content", "utf8");

  activateEnvironment({ cwd, env: "claude", packageRoot: ROOT, target: custom });

  assert.ok(fs.existsSync(keep), "--target 指定的目录归属不明，不得被对齐清理");
});

test("repeated activation is idempotent", () => {
  const cwd = fs.mkdtempSync(path.join(os.tmpdir(), "test-generator-idempotent-"));

  const first = activateEnvironment({ cwd, env: "codebuddy", packageRoot: ROOT });
  const second = activateEnvironment({ cwd, env: "codebuddy", packageRoot: ROOT });

  assert.deepEqual(second.pruned, [], "内容未变时不应清理任何文件");
  assert.equal(second.copied, first.copied);
  assert.equal(fs.existsSync(path.join(second.target, ...SKILL_ENTRY)), true);
});

test("activation never copies development-only assets into a host directory", () => {
  const cwd = fs.mkdtempSync(path.join(os.tmpdir(), "test-generator-excludes-"));
  const result = activateEnvironment({ cwd, env: "claude", packageRoot: ROOT });

  for (const forbidden of ["devtools", "test", ".harness", "node_modules", "bin"]) {
    assert.equal(
      fs.existsSync(path.join(result.target, forbidden)),
      false,
      `${forbidden}/ 不应进入宿主目录`,
    );
  }
});
