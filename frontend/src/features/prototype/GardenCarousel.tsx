"use client";
import { useCallback, useEffect, useId, useRef, useState } from "react";
import Link from "next/link";
import {
  ChevronLeft,
  ChevronRight,
  ArrowRight,
  Sprout,
  Users,
  Leaf,
} from "lucide-react";
import type { Garden } from "@/types/garden";
import type { GardenDirectory } from "@/services/gardens";
import { gardenHref } from "@/lib/gardenNavigation";
import { request, inventory } from "@/services/prototype";
import { useResource } from "./ui";
import { GardenScene } from "./GardenScene";

export function GardenCarousel({ directory }: { directory: GardenDirectory }) {
  const groups = directory.gardens;
  const track = useRef<HTMLDivElement>(null),
    carouselId = useId();
  const [arrows, setArrows] = useState({ left: false, right: false });
  useEffect(() => {
    const element = track.current;
    if (!element) return;
    const update = () =>
      setArrows({
        left: element.scrollLeft > 1,
        right:
          element.scrollLeft + element.clientWidth < element.scrollWidth - 2,
      });
    const frame = requestAnimationFrame(update);
    const observer = new ResizeObserver(update);
    observer.observe(element);
    element.addEventListener("scroll", update, { passive: true });
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      element.removeEventListener("scroll", update);
    };
  }, [groups.length]);
  function move(direction: number) {
    const element = track.current;
    if (element)
      element.scrollBy({
        left: direction * element.clientWidth,
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
          ? "instant"
          : "smooth",
      });
  }
  if (!groups.length)
    return (
      <section className="j-panel j-garden-directory-empty">
        <span className="j-soft-icon">
          <Sprout aria-hidden="true" />
        </span>
        <h2>Your garden is taking root.</h2>
        <p>
          Your gardens will appear here when available.
          <br />
          Its shared garden will appear in this space.
        </p>
        <Link className="j-button" href="/garden?groups=1#garden-groups">
          Explore group gardens
          <ArrowRight aria-hidden="true" />
        </Link>
      </section>
    );
  return (
    <section className="j-garden-directory" aria-label="Your gardens">
      <div className="j-spread">
        <h2>Choose a garden</h2>
        <span className="j-mono">
          {groups.length} {groups.length === 1 ? "garden" : "gardens"}
        </span>
      </div>
      <div className="j-garden-carousel-shell">
        <button
          className="j-carousel-arrow j-carousel-previous"
          aria-label="Previous gardens"
          aria-controls={carouselId}
          disabled={!arrows.left}
          onClick={() => move(-1)}
        >
          <ChevronLeft aria-hidden="true" />
        </button>
        <div
          ref={track}
          id={carouselId}
          className="j-garden-carousel"
          role="group"
          aria-roledescription="carousel"
          aria-label="Garden previews"
          tabIndex={0}
          onKeyDown={(event) => {
            if (event.target !== event.currentTarget) return;
            if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
              event.preventDefault();
              move(event.key === "ArrowLeft" ? -1 : 1);
            }
          }}
        >
          {groups.map((item, index) => (
            <GardenPreviewCard
              key={item.id}
              item={item}
              directory={directory}
              position={index + 1}
              total={groups.length}
            />
          ))}
        </div>
        <button
          className="j-carousel-arrow j-carousel-next"
          aria-label="Next gardens"
          aria-controls={carouselId}
          disabled={!arrows.right}
          onClick={() => move(1)}
        >
          <ChevronRight aria-hidden="true" />
        </button>
      </div>
      <p className="j-garden-carousel-hint">
        A little world in every card. Swipe or use the arrows to wander.
      </p>
      {!directory.catalogAvailable && (
        <p className="j-panel-footnote">
          Some plant names could not load. Open a garden to retry its details.
        </p>
      )}
    </section>
  );
}

function GardenPreviewCard({
  item,
  directory,
  position,
  total,
}: {
  item: Garden;
  directory: GardenDirectory;
  position: number;
  total: number;
}) {
  const load = useCallback(
    () => request(inventory.array(), `/gardens/${item.id}/inventory`),
    [item.id],
  );
  const view = useResource(load);
  const personal = item.garden_type === "personal";
  const groupName = personal ? item.name : directory.groupNames[item.owner_group_id ?? ""] ?? item.name;
  const objects = (view.data ?? [])
    .filter((entry) => entry.position_x != null && entry.position_y != null)
    .map((entry) => {
      const info =
        entry.catalog_item ??
        directory.catalog.find((value) => value.id === entry.catalog_item_id);
      return {
        id: entry.id,
        asset: info?.asset_key ?? "seed",
        name: info?.name ?? "Garden item",
        x: Math.max(8, Math.min(92, entry.position_x ?? 50)),
        y: Math.max(25, Math.min(85, entry.position_y ?? 70)),
      };
    });
  return (
    <article
      className="j-garden-preview-card"
      role="group"
      aria-roledescription="slide"
      aria-label={`${position} of ${total}: ${groupName}`}
    >
      <Link
        className="j-garden-preview-link"
        href={gardenHref(item.id)}
        aria-label={`Open ${groupName} garden`}
      >
        <div className="j-garden-preview-scene">
          <GardenScene
            items={objects}
            label={`${groupName} garden illustration`}
          />
          <span className="j-garden-preview-tag">
            {personal ? <Leaf aria-hidden="true" /> : <Users aria-hidden="true" />}
            {personal ? "Personal garden" : "Shared garden"}
          </span>
          {view.loading && (
            <span className="j-garden-preview-status" role="status">
              Loading your preview…
            </span>
          )}
          {view.error && (
            <span className="j-garden-preview-status">
              Preview unavailable · open to retry
            </span>
          )}
        </div>
        <div className="j-garden-preview-body">
          <p className="j-eyebrow">{personal ? "A LITTLE PATCH OF YOUR OWN" : "A LITTLE PATCH OF TOGETHER"}</p>
          <h3>{groupName}</h3>
          <p>{personal ? "Just yours, at your own pace." : item.name}</p>
          <div className="j-garden-preview-bottom">
            <span>
              {view.data
                ? `${objects.length} planted · level ${item.growth_level}`
                : personal ? "Your personal space" : "Your shared space"}
            </span>
            <span className="j-garden-preview-enter">
              Step inside
              <ArrowRight aria-hidden="true" />
            </span>
          </div>
        </div>
      </Link>
      {view.error && (
        <button className="j-garden-preview-retry" onClick={view.refresh}>
          Retry preview
        </button>
      )}
    </article>
  );
}
