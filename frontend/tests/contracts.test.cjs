const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const ts = require("typescript");

// Exercise the real boundary module without needing a running API or database.
function boundary(body) {
  const source = fs.readFileSync(
    path.join(__dirname, "../src/services/prototype.ts"),
    "utf8",
  );
  const output = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
    },
  }).outputText;
  const compiledModule = { exports: {} };
  vm.runInNewContext(output, {
    module: compiledModule,
    exports: compiledModule.exports,
    Date,
    Error,
    require: (name) =>
      name === "@/services/apiClient"
        ? { apiClient: { request: async () => ({ data: body }) } }
        : require(name),
  });
  return compiledModule.exports;
}

test("rejects a success-shaped response without its request envelope", async () => {
  const api = boundary({ success: true });
  await assert.rejects(
    api.request(api.success, "/groups/example/leave", "post"),
    /envelope/,
  );
});

test("does not turn a negative server receipt into a successful action", async () => {
  const api = boundary({
    data: { success: false, message: "Not accepted" },
    request_id: "test",
  });
  await assert.rejects(
    api.request(api.success, "/groups/example/leave", "post"),
    /Unexpected server response/,
  );
});

test("accepts an explicit positive server receipt", async () => {
  const api = boundary({
    data: { success: true, message: "Accepted" },
    request_id: "test",
  });
  const receipt = await api.request(
    api.success,
    "/groups/example/leave",
    "post",
  );
  assert.equal(receipt.success, true);
});

test("rejects malformed screening results instead of rendering unverified findings", async () => {
  const api = boundary({
    data: { status: "completed", redacted_text: "hello" },
    request_id: "test",
  });
  await assert.rejects(
    api.request(api.screening, "/ai/privacy/text", "post"),
    /Unexpected server response/,
  );
});

test("does not infer a safety verdict from an empty detection list", async () => {
  const api = boundary({
    data: {
      status: "completed",
      has_potential_pii: false,
      has_harmful_content_indicators: false,
      redacted_text: "hello",
      detections: [],
      limitations: ["Screening can miss personal information."],
    },
    request_id: "test",
  });
  const result = await api.request(api.screening, "/ai/privacy/text", "post");
  assert.equal(result.has_potential_pii, false);
  assert.equal(result.limitations.length, 1);
  assert.equal(Object.hasOwn(result, "safe"), false);
});

test("normalizes existing naive UTC timestamps without shifting explicit offsets", () => {
  const api = boundary({});
  assert.equal(api.utc("2026-11-06T03:00:00"), "2026-11-06T03:00:00Z");
  assert.equal(
    api.utc("2026-11-06T11:00:00+08:00"),
    "2026-11-06T11:00:00+08:00",
  );
  assert.equal(
    Date.parse(api.utc("2026-11-06T03:00:00")),
    Date.parse("2026-11-06T11:00:00+08:00"),
  );
});
