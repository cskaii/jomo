const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const ts = require("typescript");

function loadModule(file) {
  const compiled = { exports: {} };
  const source = fs.readFileSync(path.join(__dirname, "../src/lib", file), "utf8");
  vm.runInNewContext(ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText, { module: compiled, exports: compiled.exports, Date });
  return compiled.exports;
}

test("quiz is eligible on first visit, then waits two hours even after navigation", () => {
  const policy = loadModule("privacyChallenge.ts");
  const now = 1_800_000_000_000;
  assert.equal(policy.quizDelay(0, now), 0);
  const savedTimestamp = String(now);
  // Recreating the module simulates a page refresh with the persisted value.
  const refreshed = loadModule("privacyChallenge.ts");
  assert.equal(refreshed.quizDelay(Number(savedTimestamp), now + 60_000), 7_140_000);
  assert.equal(refreshed.quizDelay(Number(savedTimestamp), now + 7_200_000), 0);
  assert.notEqual(policy.quizStorageKey("alice"), policy.quizStorageKey("bob"));
});

test("invalid timestamps and clock changes cannot block challenges forever", () => {
  const policy = loadModule("privacyChallenge.ts");
  assert.equal(policy.quizDelay(NaN, 1000), 0);
  assert.equal(policy.quizDelay(-1, 1000), 0);
  assert.equal(policy.quizDelay(99_999_999, 1000), 0);
});

test("automatic quizzes wait while hidden, idle, editing or busy", () => {
  const { canAutoChallenge } = loadModule("privacyChallenge.ts");
  const ready = { visible: true, active: true, editing: false, busy: false };
  assert.equal(canAutoChallenge(ready), true);
  for (const blocked of [{ visible: false }, { active: false }, { editing: true }, { busy: true }]) {
    assert.equal(canAutoChallenge({ ...ready, ...blocked }), false);
  }
});

test("returning to a resource reuses data while a fresh request runs", async () => {
  const cache = loadModule("resourceCache.ts");
  await cache.fetchResource("insights", async () => ({ minutes: 30 }), "alice");
  let resolve;
  const refresh = cache.fetchResource("insights", () => new Promise(done => { resolve = done; }), "alice");
  await Promise.resolve();
  assert.equal(cache.cachedResource("insights", "alice").minutes, 30);
  resolve({ minutes: 45 });
  await refresh;
  assert.equal(cache.cachedResource("insights", "alice").minutes, 45);
});

test("simultaneous consumers share one request", async () => {
  const cache = loadModule("resourceCache.ts");
  let calls = 0;
  const load = async () => { calls += 1; return 42; };
  await Promise.all([cache.fetchResource(load, load), cache.fetchResource(load, load)]);
  assert.equal(calls, 1);
});

test("cache isolates accounts and clears completed and pending data on logout", async () => {
  const cache = loadModule("resourceCache.ts");
  await cache.fetchResource("garden", async () => "Alice's garden", "alice");
  assert.equal(cache.cachedResource("garden", "bob"), undefined);
  let resolve;
  const pending = cache.fetchResource("profile", () => new Promise(done => { resolve = done; }), "alice");
  await Promise.resolve();
  cache.clearResourceCache();
  resolve("Alice");
  await pending;
  assert.equal(cache.cachedResource("garden", "alice"), undefined);
  assert.equal(cache.cachedResource("profile", "alice"), undefined);
});

test("failed background refresh preserves data and permits retry", async () => {
  const cache = loadModule("resourceCache.ts");
  await cache.fetchResource("garden", async () => 100);
  await assert.rejects(cache.fetchResource("garden", async () => { throw new Error("offline"); }), /offline/);
  assert.equal(cache.cachedResource("garden"), 100);
  await cache.fetchResource("garden", async () => 120);
  assert.equal(cache.cachedResource("garden"), 120);
});

test("refresh after a purchase supersedes an older request", async () => {
  const cache = loadModule("resourceCache.ts");
  let resolveOld;
  const old = cache.fetchResource("garden", () => new Promise(done => { resolveOld = done; }));
  await Promise.resolve();
  await cache.fetchResource("garden", async () => 900, "", true);
  resolveOld(1000);
  await old;
  assert.equal(cache.cachedResource("garden"), 900);
});
