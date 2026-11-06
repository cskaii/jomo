import type { Garden } from "@/types/garden";

export function gardenHref(gardenId: string) {
  return `/garden?garden=${encodeURIComponent(gardenId)}`;
}

/** Resolve only from the server's accessible directory, never an arbitrary ID. */
export function selectGarden<T extends Pick<Garden, "id" | "garden_type" | "owner_group_id">>(
  gardens: T[],
  query: { gardenId: string | null; groupId: string | null; view: string | null },
) {
  const requested = Boolean(query.gardenId || query.groupId || query.view === "personal");
  const selected = query.gardenId
    ? gardens.find((item) => item.id === query.gardenId)
    : query.groupId
      ? gardens.find((item) => item.garden_type === "group" && item.owner_group_id === query.groupId)
      : query.view === "personal"
        ? gardens.find((item) => item.garden_type === "personal")
        : undefined;
  return { selected, missing: requested && !selected };
}
