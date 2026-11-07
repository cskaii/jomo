const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const ts = require("typescript");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");

function loadSource(file) {
  const compiled = { exports: {} };
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(__dirname, "../src", file), "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX },
    fileName: file,
  }).outputText, { module: compiled, exports: compiled.exports, require });
  return compiled.exports;
}
const { welcomeTitle, loadingCopy } = loadSource("lib/loadingCopy.ts");
const { LoadingScene } = loadSource("components/common/LoadingScene.tsx");

test("welcome uses each account's chosen display name, never a hardcoded person", () => {
  assert.equal(welcomeTitle(false, "Alex"), "Welcome back, Alex.");
  assert.equal(welcomeTitle(false, "  Nur Aisyah  "), "Welcome back, Nur Aisyah.");
  assert.equal(welcomeTitle(false, null), "Welcome back.");
  assert.equal(welcomeTitle(false, ""), "Welcome back.");
  assert.equal(welcomeTitle(false, "JOMO User edb3c86e"), "Welcome back, JOMO User edb3c86e.");
  assert.equal(welcomeTitle(false, " ", "user_edb3c86e"), "Welcome back, user_edb3c86e.");
  assert.equal(welcomeTitle(false, "Alex", "user_edb3c86e"), "Welcome back, Alex.");
  assert.equal(welcomeTitle(true, "Alex"), "Welcome to your little space.");
});

test("loading copy follows the destination including nested pages", () => {
  for (const [url, section] of [
    ["/garden", "Your garden"], ["/insights", "Your insights"],
    ["/privacy-guardian", "Privacy Guardian"], ["/settings", "Your preferences"],
    ["/preferences", "Your preferences"], ["/friends", "Your circle"],
    ["/friends/groups/example", "Your shared space"], ["/squads", "Your shared space"],
    ["/activities/create", "Offline moments"], ["/focus/example", "Your quiet moment"],
  ]) assert.equal(loadingCopy(url).section, section);
  assert.equal(loadingCopy("/unknown").section, "JOMO");
});

test("all scene sizes announce loading with decorative art hidden from screen readers", () => {
  for (const variant of ["page", "welcome", "inline"]) {
    const html = renderToStaticMarkup(React.createElement(LoadingScene, { variant }));
    assert.match(html, /role="status"/);
    assert.match(html, /aria-live="polite"/);
    assert.match(html, /class="j-loading-art"[^>]*aria-hidden="true"/);
    assert.ok(html.includes(`j-loading-scene--${variant}`));
    assert.ok(!html.includes("aria-valuenow"), "never invent a progress percentage");
    assert.ok(!html.includes("<img"), "loading art needs no external image request");
  }
});

test("display names render as text, including punctuation and HTML-like characters", () => {
  const html = renderToStaticMarkup(React.createElement(LoadingScene, {
    variant: "welcome", title: welcomeTitle(false, '<script>alert("name")</script>'),
  }));
  assert.ok(!html.includes("<script>"));
  assert.ok(html.includes("&lt;script&gt;"));
});
