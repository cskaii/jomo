const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm'), ts = require('typescript');
function load(file, globals = {}, dependencies = {}) {
  const module = { exports: {} };
  const source = ts.transpileModule(fs.readFileSync(path.join(__dirname, '../src/services', file + '.ts'), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }
  }).outputText;
  vm.runInNewContext(source, { module, exports: module.exports, process: { env: {} }, Error, Date, AbortSignal, setTimeout,
    require: name => dependencies[name] ?? require(name), ...globals });
  return module.exports;
}
function auth(fetch) {
  const storage = new Map([['jomo_auth_token', 'a.b.c'], ['jomo_refresh_token', 'refresh'], ['jomo_token_expires_at', '0']]);
  const events = [];
  const api = load('authSession', { fetch, localStorage: { getItem: key => storage.get(key) ?? null, setItem: (k,v) => storage.set(k,v), removeItem: key => storage.delete(key) },
    window: { dispatchEvent: event => events.push(event.type) }, Event: class { constructor(type) { this.type = type; } } },
    { '@/lib/resourceCache': { clearResourceCache() {} }, './backendConnection': { waitForBackend: async () => {} } });
  return { api, storage, events };
}
test('temporary refresh outage preserves credentials and does not announce logout', async () => {
  const { api, storage, events } = auth(async () => ({ ok: false, status: 503 }));
  await assert.rejects(api.accessToken(), /temporarily unavailable/);
  assert.equal(storage.get('jomo_refresh_token'), 'refresh'); assert.equal(events.length, 0);
});
test('network failure during refresh preserves session', async () => {
  const { api, storage } = auth(async () => { throw new Error('offline'); });
  await assert.rejects(api.accessToken(), /offline/); assert.equal(storage.get('jomo_auth_token'), 'a.b.c');
});
test('confirmed invalid refresh signs out', async () => {
  const { api, storage, events } = auth(async () => ({ ok: false, status: 401 }));
  await assert.rejects(api.accessToken()); assert.equal(storage.size, 0); assert.deepEqual(events, ['jomo:session-expired']);
});
test('refresh response cannot resurrect an account after logout', async () => {
  let release;
  const { api, storage } = auth(() => new Promise(resolve => { release = resolve; }));
  const result = api.accessToken(); await new Promise(resolve => setImmediate(resolve));
  api.clearSession(); release({ ok: true, json: async () => ({ data: { access_token: 'new.token.value', refresh_token: 'new', expires_in: 3600, token_type: 'bearer' } }) });
  await assert.rejects(result, /session changed/); assert.equal(storage.size, 0);
});
function client(refresh) {
  let reject, retries = 0, clears = 0, wakes = 0;
  const instance = { interceptors: { request: { use() {} }, response: { use(_ok, fail) { reject = fail; } } }, request: async () => { retries++; return 'retried'; } };
  load('apiClient', { window: { dispatchEvent() {} } }, {
    axios: { default: { create: () => instance } }, './authSession': { accessToken: refresh, clearSession() { clears++; } },
    './backendConnection': { waitForBackend: async () => { wakes++; } }
  });
  return { reject, stats: () => ({ retries, clears, wakes }) };
}
test('401 plus temporary refresh failure does not clear the saved login', async () => {
  const c = client(async () => { throw new Error('temporary refresh failure'); });
  await assert.rejects(c.reject({ response: { status: 401 }, config: { url: '/users/me', method: 'get', headers: {} } }), /temporary/);
  assert.equal(c.stats().clears, 0);
});
test('a timed-out GET wakes the backend and retries once', async () => {
  const c = client();
  assert.equal(await c.reject({ config: { url: '/activities', method: 'get' } }), 'retried');
  assert.deepEqual(c.stats(), { wakes: 1, retries: 1, clears: 0 });
});
test('a timed-out purchase is never replayed automatically', async () => {
  const c = client();
  await assert.rejects(c.reject({ config: { url: '/gardens/test/purchases', method: 'post' } }));
  assert.deepEqual(c.stats(), { wakes: 0, retries: 0, clears: 0 });
});
test('simultaneous wake-ups share one public probe and clear connection state', async () => {
  let release, calls = 0;
  const api = load('backendConnection', { fetch: () => { calls++; return new Promise(resolve => { release = resolve; }); } });
  const first = api.waitForBackend(), second = api.waitForBackend(); assert.equal(first, second);
  assert.equal(api.connectionSnapshot(), true);
  release({ ok: true, headers: { get: () => 'application/json' } }); await first;
  assert.equal(calls, 1); assert.equal(api.connectionSnapshot(), false);
});
test('wake-up retries stop at the deadline and release the overlay', async () => {
  let now = 0;
  const api = load('backendConnection', { Date: { now: () => now }, fetch: async () => ({ ok: false }),
    setTimeout: fn => { now += 30000; fn(); } });
  await assert.rejects(api.waitForBackend(), /taking longer/); assert.equal(api.connectionSnapshot(), false);
});
