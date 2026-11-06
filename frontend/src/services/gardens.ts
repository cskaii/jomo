import { request, garden, group, catalog } from "./prototype";

export async function loadGardenDirectory() {
  const [gardens, groups, items] = await Promise.all([
    request(garden.array(), "/gardens"),
    request(group.array(), "/groups").catch(() => null),
    request(catalog.array(), "/shop/items").catch(() => null),
  ]);
  const groupNames: Record<string, string> = {};
  for (const entry of groups ?? []) groupNames[entry.id] = entry.name;
  return {
    gardens,
    groupNames,
    catalog: items ?? [],
    catalogAvailable: items !== null,
  };
}

export type GardenDirectory = Awaited<ReturnType<typeof loadGardenDirectory>>;
