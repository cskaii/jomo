"use client";
import { useCallback } from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { request, garden, inventory, catalog } from "@/services/prototype";
import { useResource, ResourceState } from "./ui";
import { GardenScene } from "./GardenScene";

export function SharedGardenPreview({ groupId }: { groupId: string }) {
  const load = useCallback(async () => {
    const gardens = await request(garden.array(), "/gardens");
    const shared = gardens.find((item) => item.owner_group_id === groupId);
    if (!shared) throw new Error("This shared garden is not available yet.");
    const [items, shop] = await Promise.all([
      request(inventory.array(), `/gardens/${shared.id}/inventory`),
      request(catalog.array(), "/shop/items"),
    ]);
    return { shared, items, shop };
  }, [groupId]);
  const view = useResource(load);
  if (!view.data)
    return (
      <ResourceState
        loading={view.loading}
        error={view.error}
        retry={view.refresh}
      />
    );
  const { shared, items, shop } = view.data;
  const sceneItems = items
    .filter((item) => item.position_x != null && item.position_y != null)
    .map((item) => {
      const entry =
        item.catalog_item ??
        shop.find((value) => value.id === item.catalog_item_id);
      return {
        id: item.id,
        asset: entry?.asset_key ?? "seed",
        name: entry?.name ?? "Garden item",
        x: Math.max(8, Math.min(92, item.position_x ?? 50)),
        y: Math.max(25, Math.min(85, item.position_y ?? 70)),
      };
    });
  return (
    <section className="j-garden-frame">
      <GardenScene
        items={sceneItems}
        label={`${shared.name}: ${sceneItems.length} planted objects`}
      />
      <div className="j-panel" style={{ margin: 0 }}>
        <div className="j-spread">
          <h2>The shared garden</h2>
          <span className="j-tag">{shared.points_balance} points</span>
        </div>
        <p>
          Everything your group earns together has a home here. Your shared
          garden keeps what you earned.
        </p>
        <div className="j-growth-row">
          <span className="j-soft-icon">
            <ArrowRight aria-hidden="true" />
          </span>
          <div>
            <strong>Grow something together</strong>
            <p>
              {sceneItems.length
                ? `${sceneItems.length} planted objects · level ${shared.growth_level}`
                : "A little space for your first shared plant."}
            </p>
          </div>
        </div>
        <br />
        <Link className="j-button" href={`/garden?group=${groupId}`}>
          Open the shared garden <ArrowRight aria-hidden="true" />
        </Link>
      </div>
    </section>
  );
}
