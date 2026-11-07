const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const ts = require("typescript");
const compiled = { exports: {} };
vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(__dirname, "../src/lib/navigationTransition.ts"), "utf8"), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText, { module: compiled, exports: compiled.exports });
const { initialTransition, navigationTransition: reduce, TAB_TRANSITION_MS, WELCOME_TRANSITION_MS } = compiled.exports;

test("a restored session starts with a welcome transition on every app mount", () => {
  const first = initialTransition("/privacy-guardian?");
  assert.equal(first.active, true);
  assert.equal(first.welcomed, false);
  const completed = reduce(first, { type: "finish", route: first.route });
  assert.equal(completed.active, false);
  assert.equal(completed.welcomed, true);
  assert.equal(initialTransition(first.route).active, true);
  assert.equal(WELCOME_TRANSITION_MS, 1800);
  assert.equal(TAB_TRANSITION_MS, 900);
});

test("cached Privacy Guardian and preferences still get tab transitions", () => {
  let state = reduce(initialTransition("/insights?"), { type: "finish", route: "/insights?" });
  for (const route of ["/privacy-guardian?", "/settings?", "/garden?view=personal", "/garden?browse=1"]) {
    state = reduce(state, { type: "navigate", route });
    assert.equal(state.active, true);
    assert.equal(state.welcomed, true, "tab navigation must not repeat the full welcome");
    state = reduce(state, { type: "finish", route });
    assert.equal(state.active, false);
  }
});

test("rapid navigation ignores stale timers and handles returning to an earlier tab", () => {
  let state = reduce(initialTransition("/insights?"), { type: "finish", route: "/insights?" });
  state = reduce(state, { type: "navigate", route: "/privacy-guardian?" });
  state = reduce(state, { type: "navigate", route: "/friends?" });
  const unchanged = reduce(state, { type: "finish", route: "/privacy-guardian?" });
  assert.equal(unchanged, state);
  assert.equal(unchanged.active, true);
  state = reduce(state, { type: "finish", route: "/friends?" });
  assert.equal(reduce(state, { type: "navigate", route: "/insights?" }).active, true);
  assert.equal(reduce(state, { type: "navigate", route: "/friends?" }), state);
});
