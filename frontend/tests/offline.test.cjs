const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const ts = require("typescript");
const compiledModule = { exports: {} };
const source = fs.readFileSync(
  path.join(__dirname, "../src/lib/offline.ts"),
  "utf8",
);
vm.runInNewContext(
  ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
    },
  }).outputText,
  { module: compiledModule, exports: compiledModule.exports, Date },
);
const { participationRecords, offlineStats } = compiledModule.exports;

test("a plan or active timer does not count as completed offline time", () => {
  const items = [
    { id: "plan", title: "Long walk", duration_minutes: 90, category: "walk" },
  ];
  for (const status of ["joined", "active", "awaiting_proof", "left"]) {
    assert.equal(
      participationRecords(
        items,
        [
          [
            {
              user_id: "me",
              status,
              eligible_minutes: 90,
              completed_at: "2026-11-06T12:00:00Z",
            },
          ],
        ],
        "me",
      ).length,
      0,
    );
  }
});

test("only the current user's recorded eligible minutes contribute", () => {
  const items = [
    { id: "plan", title: "Long walk", duration_minutes: 90, category: "walk" },
  ];
  const participants = [
    [
      {
        user_id: "someone-else",
        status: "completed",
        eligible_minutes: 90,
        completed_at: "2026-11-06T12:00:00Z",
      },
      {
        user_id: "me",
        status: "completed",
        eligible_minutes: 25,
        completed_at: "2026-11-06T12:00:00Z",
      },
    ],
  ];
  const records = participationRecords(items, participants, "me");
  assert.equal(records.length, 1);
  assert.equal(records[0].minutes, 25);
});

test("missing or invalid completion timestamps do not invent a dated log entry", () => {
  const items = [{ id: "plan", title: "Read", category: "reading" }];
  assert.equal(
    participationRecords(
      items,
      [
        [
          {
            user_id: "me",
            status: "completed",
            eligible_minutes: 20,
            completed_at: "invalid",
          },
        ],
      ],
      "me",
    ).length,
    0,
  );
});

test("seven-day totals exclude old/future records and include days without activity", () => {
  const result = offlineStats(
    [
      { date: "2026-10-30", minutes: 100 },
      { date: "2026-11-04", minutes: 20 },
      { date: "2026-11-06", minutes: 30 },
      { date: "2026-11-07", minutes: 500 },
    ],
    "2026-11-06",
  );
  assert.equal(result.days.length, 7);
  assert.equal(result.todayMinutes, 30);
  assert.equal(result.weekMinutes, 50);
  assert.equal(result.weekCount, 2);
  assert.equal(result.days[0].minutes, 0);
  assert.equal(result.streak, 1);
});

test("a rhythm can continue from yesterday without pressuring a user to log today", () => {
  const result = offlineStats(
    [
      { date: "2026-11-04", minutes: 20 },
      { date: "2026-11-05", minutes: 30 },
    ],
    "2026-11-06",
  );
  assert.equal(result.streak, 2);
  assert.equal(result.todayMinutes, 0);
});
