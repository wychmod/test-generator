const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

const { run } = require("../bin/test-generator");
const {
  ENVIRONMENTS,
  activateEnvironment,
  collectRuntimeFiles,
  resolveActivationTarget,
  supportedEnvironments,
} = require("../lib/activation");

function makeFixtureRoot() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "test-generator-root-"));
  const files = {
    "SKILL.md": "# Canonical skill\n",
    "README.md": "# README\n",
    "HOST_COMPATIBILITY.md": "# Hosts\n",
    "DISTRIBUTION.md": "# Distribution\n",
    "adapters/codex/AGENTS.md": "# Codex adapter\n",
    "adapters/openclaw/skill.md": "# OpenClaw adapter\n",
    "config/example-config.json": "{}\n",
    "prompts/phase0_input_preprocessing_prompt.md": "# Phase 0\n",
    "resources/quality_checklist.md": "# Quality\n",
    "templates/testcase_template.md": "# Template\n",
    "scripts/prd_reader.py": "print('reader')\n",
    "devtools/package_skill.py": "print('packager')\n",
    "testcase-generator.zip": "zip-content",
  };

  for (const [relativePath, content] of Object.entries(files)) {
    const absolutePath = path.join(root, relativePath);
    fs.mkdirSync(path.dirname(absolutePath), { recursive: true });
    fs.writeFileSync(absolutePath, content);
  }

  fs.writeFileSync(
    path.join(root, "skill.manifest.json"),
    JSON.stringify(
      {
        "运行时文件": [
          "SKILL.md",
          "README.md",
          "HOST_COMPATIBILITY.md",
          "adapters/**",
          "config/**",
          "prompts/**",
          "resources/**",
          "templates/**",
          "scripts/prd_reader.py",
        ],
      },
      null,
      2,
    ),
  );

  return root;
}

function captureLogs(callback) {
  const originalLog = console.log;
  const lines = [];
  console.log = (message) => lines.push(String(message));

  try {
    callback();
  } finally {
    console.log = originalLog;
  }

  return lines.join("\n");
}

function withWorkingDirectory(cwd, callback) {
  const originalCwd = process.cwd();
  process.chdir(cwd);

  try {
    return callback();
  } finally {
    process.chdir(originalCwd);
  }
}

test("resolveActivationTarget uses project-local host directories by default", () => {
  const cwd = fs.mkdtempSync(path.join(os.tmpdir(), "test-generator-cwd-"));

  assert.equal(
    resolveActivationTarget("claude", { cwd }),
    path.join(cwd, ".claude", "skills", "testcase-generator"),
  );
  assert.equal(
    resolveActivationTarget("codex", { cwd }),
    path.join(cwd, ".agents", "skills", "testcase-generator"),
  );
});

test("collectRuntimeFiles includes manifest runtime files and excludes generated artifacts", () => {
  const root = makeFixtureRoot();
  const files = collectRuntimeFiles(root).sort();

  assert.ok(files.includes("SKILL.md"));
  assert.ok(files.includes("DISTRIBUTION.md"));
  assert.ok(files.includes("adapters/codex/AGENTS.md"));
  assert.ok(files.includes("scripts/prd_reader.py"));
  assert.ok(!files.includes("devtools/package_skill.py"));
  assert.ok(!files.includes("testcase-generator.zip"));
});

test("activateEnvironment copies runtime assets and writes host-specific entry files", () => {
  const root = makeFixtureRoot();
  const cwd = fs.mkdtempSync(path.join(os.tmpdir(), "test-generator-target-"));

  const result = activateEnvironment({
    cwd,
    env: "codex",
    packageRoot: root,
  });

  assert.equal(result.environment, "codex");
  assert.equal(result.target, path.join(cwd, ".agents", "skills", "testcase-generator"));
  assert.equal(
    fs.readFileSync(path.join(result.target, "SKILL.md"), "utf8"),
    "# Canonical skill\n",
  );
  assert.equal(
    fs.readFileSync(path.join(result.target, "AGENTS.md"), "utf8"),
    "# Codex adapter\n",
  );
  assert.equal(
    fs.existsSync(path.join(result.target, "devtools", "package_skill.py")),
    false,
  );
});

test("CLI help advertises -g as the primary global activation flag", () => {
  const output = captureLogs(() => {
    assert.equal(run(["--help"]), 0);
  });

  assert.match(output, /activate <environment\|all> \[-g\]/);
  assert.match(output, /Use 'all' to activate every supported environment/);
});

test("CLI activate all dry-run reports every supported environment", () => {
  const output = captureLogs(() => {
    assert.equal(run(["activate", "all", "--dry-run"]), 0);
  });

  for (const environment of supportedEnvironments()) {
    assert.match(output, new RegExp(`Would activate ${environment} skill at `));
  }
});

test("CLI activate all creates each project-local host directory", () => {
  const cwd = fs.mkdtempSync(path.join(os.tmpdir(), "test-generator-all-target-"));

  withWorkingDirectory(cwd, () => {
    captureLogs(() => {
      assert.equal(run(["activate", "all"]), 0);
    });
  });

  for (const environment of supportedEnvironments()) {
    const target = resolveActivationTarget(environment, { cwd });
    assert.equal(fs.existsSync(path.join(target, "DISTRIBUTION.md")), true);

    const entryTarget = ENVIRONMENTS[environment].entry?.target;
    if (entryTarget) {
      assert.equal(fs.existsSync(path.join(target, entryTarget)), true);
    }
  }
});

test("CLI activate all rejects exact --target paths", () => {
  assert.throws(
    () => run(["activate", "all", "--target", "custom-target"]),
    /--target cannot be used with activate all/,
  );
});
