type ResourceKey = string | (() => Promise<unknown>);
type Entry = { data?: unknown; pending?: Promise<unknown> };
const sessions = new Map<string, Map<ResourceKey, Entry>>();
let generation = 0;

// Only retained in this tab's memory. Never persist private API responses.
export function clearResourceCache() {
  generation += 1;
  sessions.clear();
}

export function cachedResource<T>(key: ResourceKey, owner = ""): T | undefined {
  return sessions.get(owner)?.get(key)?.data as T | undefined;
}

export function fetchResource<T>(key: ResourceKey, load: () => Promise<T>, owner = "", force = false): Promise<T> {
  let entries = sessions.get(owner);
  if (!entries) { entries = new Map(); sessions.set(owner, entries); }
  const existing = entries.get(key);
  if (existing?.pending && !force) return existing.pending as Promise<T>;
  const version = generation;
  const entry: Entry = existing ?? {};
  const pending = Promise.resolve().then(load).then((data) => {
    if (version === generation && entry.pending === pending) entry.data = data;
    return data;
  }).finally(() => {
    if (entry.pending === pending) entry.pending = undefined;
  });
  entry.pending = pending;
  entries.set(key, entry);
  return pending;
}
