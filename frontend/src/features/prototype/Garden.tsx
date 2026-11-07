"use client";
import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { GardenScene } from "./GardenScene";
import Link from "next/link";
import { GardenNavigation } from "./GardenNavigation";
import { GardenCarousel } from "./GardenCarousel";
import { GroupGardenManagement } from "./Squads";
import { PersonalGarden } from "./PersonalGarden";
import Activities from "./Activities";
import { gardenHref } from "@/lib/gardenNavigation";
import { loadGardenDirectory } from "@/services/gardens";
import { selectGarden } from "@/lib/gardenNavigation";
import { loadOfflineOverview } from "@/services/offline";
import { offlineStats } from "@/lib/offline";
import {
  request,
  garden,
  catalog,
  inventory,
  ledger,
  success,
  z,
  dateTime,
  localDate,
} from "@/services/prototype";
import {
  useResource,
  useAction,
  Feedback,
  ResourceState,
  Panel,
  Empty,
  Submit,
} from "./ui";
const icons: Record<string, string> = {
  plant_sunflower: "🌻",
  plant_bonsai: "🌳",
  decor_bench: "🪑",
  pet_calico_cat: "🐈",
  decor_fountain: "⛲",
};
export default function Garden() {
  const params = useSearchParams(),
    directory = useResource(loadGardenDirectory);
  const [groupsOpen, setGroupsOpen] = useState(false);
  const activitiesRequested = params.get("activities") === "1";
  useEffect(() => {
    if (directory.data && activitiesRequested) {
      document.getElementById("garden-activities")?.scrollIntoView({ block: "start", behavior: "instant" });
    }
  }, [directory.data, activitiesRequested]);
  if (!directory.data)
    return (
      <ResourceState
        loading={directory.loading}
        error={directory.error}
        retry={directory.refresh}
      />
    );
  const { selected, missing } = selectGarden(directory.data.gardens, {
    gardenId: params.get("garden"),
    groupId: params.get("group"),
    view: params.get("view"),
  });
  const current = selected ?? (
    !missing && params.get("browse") !== "1"
      ? directory.data.gardens.find((item) => item.garden_type === "personal")
      : undefined
  );
  if (current?.garden_type === "personal" && params.get("manage") !== "1")
    return <PersonalGarden key={current.id} garden={current} />;
  return (
    <>
      {current?.garden_type === "personal" && <Link className="j-garden-back" href={gardenHref(current.id)}>Back to garden view</Link>}
      <GardenNavigation
        directory={directory.data}
        current={current}
        onRefresh={directory.refresh}
      />
      {missing ? (
        <Panel title="This garden is not available">
          <p>
            You may no longer belong to this group, or this link may be out of
            date. Choose a garden from your current list.
          </p>
          <Link className="j-button" href="/garden">
            Browse gardens
          </Link>
        </Panel>
      ) : current ? (
        <GardenView key={current.id} gardenId={current.id} />
      ) : (
        <>
          <GardenCarousel directory={directory.data} />
          <section className="j-garden-activities" id="garden-activities" aria-label="Garden activities">
            <Activities embedded />
          </section>
          <details className="j-garden-groups" open={params.get("groups") === "1"} onToggle={event => setGroupsOpen(event.currentTarget.open)}>
            <summary>Grow with a group <span>Optional · create, join or manage</span></summary>
            <section id="garden-groups">
              {(groupsOpen || params.get("groups") === "1") && <GroupGardenManagement onChanged={directory.refresh} />}
            </section>
          </details>
        </>
      )}
    </>
  );
}
function GardenView({ gardenId }: { gardenId: string }) {
  const load = useCallback(async () => {
    const [details, items, shop, history, overview] = await Promise.all([
      request(garden, `/gardens/${gardenId}`),
      request(inventory.array(), `/gardens/${gardenId}/inventory`),
      request(catalog.array(), "/shop/items"),
      request(ledger.array(), `/gardens/${gardenId}/ledger`),
      loadOfflineOverview().catch(() => null),
    ]);
    return { details, items, shop, history, overview };
  }, [gardenId]);
  const view = useResource(load, `garden-management:${gardenId}`),
    action = useAction(),
    [buy, setBuy] = useState<z.infer<typeof catalog> | null>(null);
  const [placing, setPlacing] = useState(""),
    [x, setX] = useState("50"),
    [y, setY] = useState("70");
  if (!view.data)
    return (
      <ResourceState
        loading={view.loading}
        error={view.error}
        retry={view.refresh}
      />
    );
  const { details, items, shop, history, overview } = view.data;
  const moments = overview?.records.filter((record) =>
    details.garden_type === "group"
      ? record.groupId === details.owner_group_id
      : !record.groupId,
  );
  const rhythm = moments ? offlineStats(moments, localDate()).streak : null;
  const placed = items.filter(
    (item) => item.position_x != null && item.position_y != null,
  );
  function info(item: z.infer<typeof inventory>) {
    return (
      item.catalog_item ??
      shop.find((entry) => entry.id === item.catalog_item_id)
    );
  }
  return (
    <>
      <div className="j-garden-overview">
        <section className="j-garden-frame">
          <GardenScene
            items={placed.map((item) => ({
              id: item.id,
              asset: info(item)?.asset_key ?? "seed",
              name: info(item)?.name ?? "Garden item",
              x: Math.max(8, Math.min(92, item.position_x ?? 50)),
              y: Math.max(25, Math.min(85, item.position_y ?? 70)),
            }))}
            label={
              details.name + ": " + placed.length + " placed garden objects"
            }
          />
          <div className="j-garden-caption">
            <p className="j-mono">Your garden, illustrated</p>
            <span className="j-tag">{placed.length} planted</span>
          </div>
        </section>
        <div className="j-garden-stats">
          <Panel>
            <p className="j-eyebrow">Time given to real life</p>
            <strong>
              {moments
                ? moments.reduce((sum, record) => sum + record.minutes, 0)
                : "—"}
              <small> min</small>
            </strong>
            <p>
              Recorded from completed{" "}
              {details.garden_type === "group" ? "group" : "personal"}{" "}
              activities.
            </p>
          </Panel>
          <Panel>
            <p className="j-eyebrow">A little room to grow</p>
            <strong>
              {details.points_balance}
              <small> points</small>
            </strong>
            <p>
              Level {details.growth_level} ·{" "}
              {rhythm === null
                ? "Rhythm unavailable"
                : rhythm +
                  (rhythm === 1 ? " day" : " days") +
                  " of offline moments"}
            </p>
          </Panel>
        </div>
      </div>
      <Panel title="What grows next">
        <p>
          Choose something for your patch. What you earn stays with your garden.
        </p>
        {shop.slice(0, 3).map((item) => {
          const owned = items.some(
            (entry) => entry.catalog_item_id === item.id,
          );
          return (
            <div
              key={item.id}
              className={"j-growth-row" + (owned ? " is-owned" : "")}
            >
              <span aria-hidden="true">{icons[item.asset_key] ?? "🌱"}</span>
              <div>
                <strong>{item.name}</strong>
                <p>{owned ? "Part of your garden now." : item.description}</p>
              </div>
              <span>{owned ? "OWNED" : item.price_points + " POINTS"}</span>
            </div>
          );
        })}
      </Panel>
      <Panel title="Your collection">
        {items.length ? (
          <>
            <div className="j-grid">
              {items.map((item) => (
                <div key={item.id}>
                  <span className="j-item-art" aria-hidden="true">
                    {icons[info(item)?.asset_key ?? ""] ?? "🌱"}
                  </span>
                  <h3>{info(item)?.name ?? "Garden item"}</h3>
                  <p>
                    Owned: {item.quantity} ·{" "}
                    {item.placed_at ? "Placed" : "Ready to place"}
                  </p>
                </div>
              ))}
            </div>
            <form
              className="j-form"
              onSubmit={(event) => {
                event.preventDefault();
                void action.run(async () => {
                  const input = z
                    .object({
                      id: z.string().uuid(),
                      x: z.coerce.number().min(8).max(92),
                      y: z.coerce.number().min(15).max(85),
                    })
                    .parse({ id: placing, x, y });
                  await request(
                    success,
                    `/gardens/${gardenId}/items/${input.id}/place`,
                    "post",
                    { position_x: input.x, position_y: input.y },
                  );
                  view.refresh();
                }, "Item placement saved.");
              }}
            >
              <label>
                Item to place
                <select
                  required
                  value={placing}
                  onChange={(event) => setPlacing(event.target.value)}
                >
                  <option value="">Choose an owned item</option>
                  {items.map((item) => (
                    <option key={item.id} value={item.id}>
                      {info(item)?.name ?? "Garden item"}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Horizontal position (%)
                <input
                  type="number"
                  required
                  min="8"
                  max="92"
                  value={x}
                  onChange={(event) => setX(event.target.value)}
                />
              </label>
              <label>
                Vertical position (%)
                <input
                  type="number"
                  required
                  min="15"
                  max="85"
                  value={y}
                  onChange={(event) => setY(event.target.value)}
                />
              </label>
              <Submit pending={action.pending}>Place item</Submit>
            </form>
          </>
        ) : (
          <Empty>No items owned yet. Explore the seed shop below.</Empty>
        )}
      </Panel>
      <Panel title="The little garden shop">
        <p>
          Spend points from the selected garden. Purchases are final only after
          confirmation.
        </p>
        <div className="j-grid">
          {shop.map((item) => (
            <div key={item.id}>
              <div className="j-item-art" aria-hidden="true">
                {icons[item.asset_key] ?? "🌱"}
              </div>
              <h3>{item.name}</h3>
              <p>{item.description}</p>
              <p>{item.price_points} points</p>
              <button
                className="j-button secondary"
                disabled={
                  action.pending || details.points_balance < item.price_points
                }
                onClick={() => setBuy(item)}
              >
                {details.points_balance < item.price_points
                  ? "More points needed"
                  : "Choose item"}
              </button>
            </div>
          ))}
        </div>
        {!shop.length && <Empty>The shop is empty right now.</Empty>}
        {buy && (
          <section className="j-notice" aria-label="Confirm purchase">
            <p>
              Buy one {buy.name} for {buy.price_points} points from{" "}
              {details.name}?
            </p>
            <div className="j-row">
              <button
                className="j-button"
                disabled={action.pending}
                onClick={() =>
                  void action.run(async () => {
                    await request(
                      success,
                      `/gardens/${gardenId}/purchases`,
                      "post",
                      { catalog_item_id: buy.id, quantity: 1 },
                    );
                    setBuy(null);
                    view.refresh();
                  }, "Purchase accepted. Balance, inventory and history reloaded.")
                }
              >
                Confirm purchase
              </button>
              <button
                className="j-button secondary"
                disabled={action.pending}
                onClick={() => setBuy(null)}
              >
                Cancel
              </button>
            </div>
          </section>
        )}
        <Feedback action={action} />
        <small>
          If a request times out, refresh history before buying again. The same
          purchase may otherwise be made twice.
        </small>
      </Panel>
      <Panel title="Garden history">
        {history.length ? (
          <div className="j-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>When</th>
                  <th>Moment</th>
                  <th>Points</th>
                </tr>
              </thead>
              <tbody>
                {history.map((entry) => (
                  <tr key={entry.id}>
                    <td>{dateTime(entry.created_at)}</td>
                    <td>{entry.reason}</td>
                    <td>
                      {entry.amount > 0 ? "+" : ""}
                      {entry.amount}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty>Your garden story starts with a verified reward.</Empty>
        )}
      </Panel>
      <Feedback action={action} />
    </>
  );
}
