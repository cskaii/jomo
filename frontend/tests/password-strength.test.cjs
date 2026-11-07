const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const Module = require("node:module");
const { pathToFileURL } = require("node:url");
const ts = require("typescript");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");

function load(relative) {
  const filename = path.resolve(__dirname, "../src", relative);
  const compiled = new Module(filename, module);
  compiled.filename = filename;
  compiled.paths = Module._nodeModulePaths(path.dirname(filename));
  compiled._compile(ts.transpileModule(fs.readFileSync(filename, "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022,
      jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true, resolveJsonModule: true },
    fileName: filename,
  }).outputText.replaceAll("import.meta.url", JSON.stringify(pathToFileURL(filename).href)), filename);
  return compiled.exports;
}

const { assessPassword } = load("lib/passwordStrength.ts");
const { NewPasswordField } = load("features/prototype/NewPasswordField.tsx");
const vectors = require("../../backend/tests/password-policy-vectors.json");
for (const item of vectors) test(`password strength: ${item.name}`, () => {
  assert.equal(assessPassword(item.password, item.email).accepted, item.accepted);
});

test("meter starts empty and never echoes the entered secret", () => {
  assert.equal(assessPassword("").accepted, false);
  const password = "violet orbit lantern meadow";
  const html = renderToStaticMarkup(React.createElement(NewPasswordField, {
    value: password, onChange() {}, assessment: assessPassword(password),
  }));
  assert.match(html, /<meter/);
  assert.match(html, /aria-label="Estimated password strength"/);
  assert.match(html, /aria-live="polite"/);
  assert.match(html, /autocomplete="new-password"/i);
  assert.match(html, /type="password"/);
  // The actual input must contain its controlled value; the surrounding text must not.
  assert.equal(html.replace(/<input[^>]*>/g, "").includes(password), false);
});

test("an unmatched surrogate is not mistaken for a strong Unicode password", () => {
  assert.equal(assessPassword("violet orbit lantern\ud800").accepted, false);
});
