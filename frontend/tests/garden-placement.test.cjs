const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const ts = require("typescript");
const compiled = { exports: {} };
vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(__dirname, "../src/lib/gardenPlacement.ts"), "utf8"), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText, { module: compiled, exports: compiled.exports });
const { gardenPosition } = compiled.exports;

test("garden movement retains normal positions and rounds to stored precision", () => {
  const point = gardenPosition({ x: 43.12345, y: 60.988 }, { width: 1000, height: 600, itemWidth: 100, itemHeight: 100 });
  assert.equal(point.x, 43.12);
  assert.equal(point.y, 60.99);
});

test("dragging outside a mobile garden keeps the whole item within its edges", () => {
  const bounds = { width: 320, height: 460, itemWidth: 140, itemHeight: 140 };
  for (const point of [{ x: -100, y: -100 }, { x: 200, y: 200 }]) {
    const clamped = gardenPosition(point, bounds);
    assert.ok(clamped.x / 100 * bounds.width - bounds.itemWidth / 2 >= -0.1);
    assert.ok(clamped.x / 100 * bounds.width + bounds.itemWidth / 2 <= bounds.width + 0.1);
    assert.ok(clamped.y / 100 * bounds.height - bounds.itemHeight * .72 >= -0.1);
    assert.ok(clamped.y / 100 * bounds.height + bounds.itemHeight * .28 <= bounds.height + 0.1);
  }
});
