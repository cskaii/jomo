"use client";

import { useCallback, useMemo, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import {
  ArrowLeft, CalendarDays, Check, CircleDollarSign, Leaf,
  PackageOpen, Users, X,
} from "lucide-react";
import type { Garden } from "@/types/garden";
import {
  request, garden as gardenSchema, catalog, inventory, success, z,
} from "@/services/prototype";
import { Feedback, ResourceState, useAction, useResource } from "./ui";
import { gameAsset, type ShopCategory } from "./gameAssets";

const shopTabs: { id: ShopCategory | "all"; label: string }[] = [
  { id: "all", label: "All" },
  { id: "flowers", label: "Flowers" },
  { id: "trees", label: "Trees" },
  { id: "animals", label: "Animals" },
  { id: "decor", label: "Furniture" },
];

export function PersonalGarden({ garden }: { garden: Garden }) {
  const load = useCallback(async () => {
    const [details, shop, items] = await Promise.all([
      request(gardenSchema, `/gardens/${garden.id}`),
      request(catalog.array(), "/shop/items"),
      request(inventory.array(), `/gardens/${garden.id}/inventory`),
    ]);
    return { details, shop, items };
  }, [garden.id]);
  const view = useResource(load);
  const action = useAction();
  const [shopOpen, setShopOpen] = useState(false);
  const [category, setCategory] = useState<ShopCategory | "all">("all");
  const [confirming, setConfirming] = useState<z.infer<typeof catalog> | null>(null);
  const availableShop = useMemo(
    () => (view.data?.shop ?? []).filter((item) => {
      const asset = gameAsset(item.asset_key);
      return asset && (category === "all" || asset.category === category);
    }),
    [view.data?.shop, category],
  );

  if (!view.data) return (
    <section className="j-immersive-garden j-game-shell">
      <div className="j-immersive-garden-status">
        <ResourceState loading={view.loading} error={view.error} retry={view.refresh} />
      </div>
    </section>
  );

  const { details, items } = view.data;
  const placed = items.filter((item) => item.position_x != null && item.position_y != null);
  const nextPosition = (index: number) => ({ x: 20 + ((index * 17) % 62), y: 48 + ((index * 11) % 34) });
  function catalogItem(item: z.infer<typeof inventory>) {
    return item.catalog_item ?? view.data?.shop.find((entry) => entry.id === item.catalog_item_id);
  }

  return (
    <section className="j-immersive-garden j-game-shell" aria-label={details.name}>
      <header className="j-game-header">
        <Link className="j-game-brand" href="/garden?browse=1" aria-label="Browse all gardens">
          <ArrowLeft aria-hidden="true" /><span>JOMO</span>
        </Link>
        <nav className="j-game-nav" aria-label="Game navigation">
          <span className="is-active"><Leaf aria-hidden="true" /> Garden</span>
          <Link href="/activities"><CalendarDays aria-hidden="true" /> Activities</Link>
          <Link href="/friends"><Users aria-hidden="true" /> Friends</Link>
        </nav>
        <div className="j-game-actions">
          <span className="j-coin-balance" title="Coins earned from verified offline activities">
            <Image src="/game-assets/Icons/Coins/coin.png" width={30} height={30} alt="" /><strong>{details.points_balance}</strong>
          </span>
          <button className="j-store-button" onClick={() => setShopOpen(true)}>
            <Image src="/game-assets/Icons/Store/store-icon.png" width={34} height={34} alt="" /><span>Store</span>
          </button>
        </div>
      </header>

      <main className="j-game-world">
        <div className="j-game-island" aria-label={`${details.name}, with ${placed.length} placed items`}>
          <div className="j-game-soil" aria-hidden="true" />
          <div className="j-game-path" aria-hidden="true" />
          {placed.map((item) => {
            const info = catalogItem(item);
            const asset = info ? gameAsset(info.asset_key) : undefined;
            if (!info || !asset) return null;
            return (
              <div className="j-game-object" key={item.id} title={info.name} style={{
                left: `${item.position_x}%`, top: `${item.position_y}%`, width: `${88 * (asset.scale ?? 1)}px`,
              }}>
                <Image src={asset.src} width={256} height={256} alt={info.name} />
              </div>
            );
          })}
          <div className="j-game-title-card">
            <span>Your garden</span><strong>{details.name}</strong>
            <small>Level {details.growth_level} · {placed.length} placed</small>
          </div>
        </div>
      </main>

      <aside className="j-inventory-tray" aria-label="Your collection">
        <div className="j-inventory-title"><PackageOpen aria-hidden="true" /><span>Collection</span></div>
        {items.length ? items.map((item, index) => {
          const info = catalogItem(item);
          const asset = info ? gameAsset(info.asset_key) : undefined;
          if (!info || !asset) return null;
          const isPlaced = item.position_x != null && item.position_y != null;
          return (
            <button key={item.id} className={`j-inventory-item${isPlaced ? " is-placed" : ""}`}
              disabled={action.pending || isPlaced} title={isPlaced ? `${info.name} is in your garden` : `Place ${info.name}`}
              onClick={() => {
                const position = nextPosition(placed.length + index);
                void action.run(async () => {
                  await request(success, `/gardens/${garden.id}/items/${item.id}/place`, "post", {
                    position_x: position.x, position_y: position.y,
                  });
                  view.refresh();
                }, `${info.name} placed in your garden.`);
              }}>
              <Image src={asset.src} width={42} height={42} alt="" /><span>{isPlaced ? <Check aria-label="Placed" /> : "Place"}</span>
              {item.quantity > 1 && <b>{item.quantity}</b>}
            </button>
          );
        }) : <button className="j-inventory-empty" onClick={() => setShopOpen(true)}>Visit the store to fill your garden</button>}
      </aside>

      {(action.notice || action.error) && <div className="j-game-feedback"><Feedback action={action} /></div>}

      {shopOpen && (
        <div className="j-store-backdrop" role="presentation" onMouseDown={(event) => {
          if (event.target === event.currentTarget) setShopOpen(false);
        }}>
          <section className="j-game-store" role="dialog" aria-modal="true" aria-labelledby="game-store-title">
            <header>
              <div><p>GARDEN MARKET</p><h2 id="game-store-title">Bring something home</h2></div>
              <div className="j-store-header-actions">
                <span className="j-coin-balance"><Image src="/game-assets/Icons/Coins/coin.png" width={30} height={30} alt="Coins" /><strong>{details.points_balance}</strong></span>
                <button className="j-store-close" onClick={() => { setShopOpen(false); setConfirming(null); }} aria-label="Close store"><X aria-hidden="true" /></button>
              </div>
            </header>
            <div className="j-store-tabs" role="tablist" aria-label="Store categories">
              {shopTabs.map((tab) => <button key={tab.id} role="tab" aria-selected={category === tab.id} onClick={() => setCategory(tab.id)}>{tab.label}</button>)}
            </div>
            <div className="j-store-grid">
              {!availableShop.length && <p>The shop has no items in this category yet.</p>}
              {availableShop.map((item) => {
                const asset = gameAsset(item.asset_key)!;
                const canAfford = details.points_balance >= item.price_points;
                const owned = items.find((entry) => entry.catalog_item_id === item.id)?.quantity ?? 0;
                return (
                  <article className="j-store-card" key={item.id}>
                    <div className="j-store-art"><Image src={asset.src} width={80} height={80} alt={item.name} /></div>
                    <div className="j-store-card-copy"><span>{asset.category}{owned ? ` · ${owned} owned` : ""}</span><h3>{item.name}</h3><p>{item.description}</p></div>
                    <button disabled={!canAfford || action.pending} onClick={() => setConfirming(item)}>
                      <Image src="/game-assets/Icons/Coins/coin.png" width={20} height={20} alt="" />
                      {canAfford ? item.price_points : `${item.price_points} · need ${item.price_points - details.points_balance}`}
                    </button>
                  </article>
                );
              })}
            </div>
            <footer><CircleDollarSign aria-hidden="true" /><p>Once an activity reaches 5 verified minutes, earn 1 coin per eligible minute, up to 60 coins per activity.</p></footer>
            {confirming && (
              <div className="j-purchase-confirm" role="alertdialog" aria-labelledby="purchase-title">
                <Image src={gameAsset(confirming.asset_key)?.src ?? "/game-assets/Icons/Seeds/seed.png"} width={66} height={66} alt="" />
                <div><span>Confirm purchase</span><h3 id="purchase-title">{confirming.name}</h3><p>{confirming.price_points} coins will be taken from this garden.</p></div>
                <button className="secondary" onClick={() => setConfirming(null)}>Cancel</button>
                <button onClick={() => void action.run(async () => {
                  await request(success, `/gardens/${garden.id}/purchases`, "post", { catalog_item_id: confirming.id, quantity: 1 });
                  setConfirming(null); view.refresh();
                }, `${confirming.name} added to your collection.`)}>Buy now</button>
              </div>
            )}
          </section>
        </div>
      )}
    </section>
  );
}
