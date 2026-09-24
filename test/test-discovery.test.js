const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const ROOT = path.resolve(__dirname, "..");
const pkg = JSON.parse(fs.readFileSync(path.join(ROOT, "package.json"), "utf8"));

function testFilesOnDisk() {
  return fs
    .readdirSync(path.join(ROOT, "test"))
    .filter((name) => name.endsWith(".test.js"))
    .sort();
}

function testFilesDeclaredInScript() {
  const afterFlag = pkg.scripts.test.replace(/^node\s+--test\s+/, "");
  return afterFlag
    .split(/\s+/)
    .map((arg) => arg.replace(/^"|"$/g, ""))
    .filter((arg) => arg.endsWith(".test.js"))
    .map((arg) => path.basename(arg))
    .sort();
}

// 这个文件的存在本身就有意义：`npm test` 采用**显式文件列表**而不是 glob，
// 因此新增测试文件时必须同步更新 package.json，否则会静默漏跑。
test("npm test declares every *.test.js file on disk", () => {
  assert.deepEqual(
    testFilesDeclaredInScript(),
    testFilesOnDisk(),
    "package.json 的 test 脚本与 test/*.test.js 不一致 —— 新增/删除测试文件后请更新该脚本",
  );
});

// 回归守卫：`node --test` 的 glob 参数支持是 Node v21 才加入的
// （见 Node 21 发布公告 "Support for globs in the Node.js test runner"）。
// CI 跑 Node 20，一旦有人把命令改回 glob 形式，这里会立刻拦下。
test("npm test does not rely on glob expansion", () => {
  assert.doesNotMatch(
    pkg.scripts.test,
    /[*?[\]]/,
    "npm test 不能使用 glob：Node < 21 不支持 `--test` 的 glob 参数，CI 会直接报模块找不到",
  );
});

test("npm test targets only test files under test/", () => {
  for (const file of testFilesDeclaredInScript()) {
    assert.ok(
      fs.existsSync(path.join(ROOT, "test", file)),
      `声明的测试文件不存在：test/${file}`,
    );
  }
});
