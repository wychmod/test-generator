const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

const {
  ENVIRONMENTS,
  activateEnvironment,
  collectRuntimeFiles,
  findCaseInsensitiveCollision,
  supportedEnvironments,
} = require("../lib/activation");

const ROOT = path.resolve(__dirname, "..");
const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, "skill.manifest.json"), "utf8"));
const hostEntries = manifest["宿主适配入口"] || {};

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

    // 无论哪个宿主，根 SKILL.md 都必须落地 —— 它是所有降级路径的锚点。
    assert.ok(
      fs.existsSync(path.join(result.target, "SKILL.md")),
      `${environment}: 运行时缺少根 SKILL.md`,
    );
  }
});

// --- case-insensitive filesystem safety ------------------------------------

test("a host entry that only differs by case from a runtime file is detected as a collision", () => {
  const runtimeFiles = collectRuntimeFiles(ROOT);

  // OpenClaw's documented entry is `skill.md` while the canonical runtime file
  // is `SKILL.md` — the same path on Windows / macOS.
  assert.equal(findCaseInsensitiveCollision("skill.md", runtimeFiles), "SKILL.md");
  assert.equal(findCaseInsensitiveCollision("SKILL.md", runtimeFiles), null);
  assert.equal(findCaseInsensitiveCollision("cursorrules", runtimeFiles), null);
  assert.equal(findCaseInsensitiveCollision("AGENTS.md", runtimeFiles), null);
  assert.equal(findCaseInsensitiveCollision("windsurfrules", runtimeFiles), null);
});

test("activating openclaw keeps the canonical SKILL.md instead of clobbering it", () => {
  const cwd = fs.mkdtempSync(path.join(os.tmpdir(), "test-generator-openclaw-"));
  const result = activateEnvironment({ cwd, env: "openclaw", packageRoot: ROOT });

  assert.equal(result.entry, null, "openclaw 入口不应被写入");
  assert.ok(result.entryCollision, "应报告大小写冲突");
  assert.equal(result.entryCollision.target, "skill.md");
  assert.equal(result.entryCollision.conflict, "SKILL.md");

  // canonical 入口必须仍是 SKILL.md 的内容，而不是被适配器覆盖
  // （用 \r?\n 兼容 Windows 的 CRLF 检出）
  const canonical = fs.readFileSync(path.join(result.target, "SKILL.md"), "utf8");
  assert.match(canonical, /^---\r?\nname: testcase-generator\r?\n/);
  assert.match(canonical, new RegExp(`^version: ${manifest["版本"]}\\r?$`, "m"));
  assert.doesNotMatch(canonical, /OpenClaw Skill Adapter/);

  // 适配器本身仍随运行时文件下发，能力没有丢失
  assert.ok(
    fs.existsSync(path.join(result.target, "adapters", "openclaw", "skill.md")),
    "adapters/openclaw/skill.md 应随运行时文件下发",
  );
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
