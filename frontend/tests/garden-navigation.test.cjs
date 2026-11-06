const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const ts = require("typescript");
const compiledModule = { exports: {} };
vm.runInNewContext(
  ts.transpileModule(
    fs.readFileSync(
      path.join(__dirname, "../src/lib/gardenNavigation.ts"),
      "utf8",
    ),
    {
      compilerOptions: {
        module: ts.ModuleKind.CommonJS,
        target: ts.ScriptTarget.ES2022,
      },
    },
  ).outputText,
  {
    module: compiledModule,
    exports: compiledModule.exports,
    encodeURIComponent,
  },
);
const { selectGarden, gardenHref } = compiledModule.exports;
const personal = {
  id: "personal",
  garden_type: "personal",
  owner_group_id: null,
};
const first = {
  id: "garden-a",
  garden_type: "group",
  owner_group_id: "group-a",
};
const second = {
  id: "garden-b",
  garden_type: "group",
  owner_group_id: "group-b",
};
const directory = [personal, first, second];
const query = (values = {}) => ({
  gardenId: null,
  groupId: null,
  view: null,
  ...values,
});

test("Garden tab opens the directory instead of silently choosing the personal garden", () => {
  const result = selectGarden(directory, query());
  assert.equal(result.selected, undefined);
  assert.equal(result.missing, false);
});

test("carousel and drawer selections resolve the exact accessible garden", () => {
  assert.equal(
    selectGarden(directory, query({ gardenId: second.id })).selected,
    second,
  );
});

test("existing shared-garden group links still resolve correctly", () => {
  assert.equal(
    selectGarden(directory, query({ groupId: "group-a" })).selected,
    first,
  );
});

test("an unavailable garden or former group cannot fall back to a different balance", () => {
  for (const values of [
    { gardenId: "not-accessible" },
    { groupId: "former-group" },
  ]) {
    const result = selectGarden(directory, query(values));
    assert.equal(result.selected, undefined);
    assert.equal(result.missing, true);
  }
});

test("personal garden remains explicitly accessible and never substitutes a group", () => {
  assert.equal(
    selectGarden(directory, query({ view: "personal" })).selected,
    personal,
  );
  assert.equal(
    selectGarden([first], query({ view: "personal" })).missing,
    true,
  );
});

test("canonical garden selection takes priority over stale group parameters", () => {
  assert.equal(
    selectGarden(directory, query({ gardenId: second.id, groupId: "group-a" }))
      .selected,
    second,
  );
  assert.equal(gardenHref("garden-a"), "/garden?garden=garden-a");
});
