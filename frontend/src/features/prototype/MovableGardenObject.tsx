"use client";
import { useRef, useState } from "react";
import Image from "next/image";
import { gardenPosition, type GardenBounds, type GardenPosition } from "@/lib/gardenPlacement";

type Props = {
  name: string; src: string; width: number; x: number; y: number;
  movable: boolean; busy: boolean; onSave: (position: GardenPosition) => Promise<boolean>;
};

function bounds(button: HTMLButtonElement): GardenBounds {
  return { width: button.parentElement?.clientWidth ?? 1, height: button.parentElement?.clientHeight ?? 1,
    itemWidth: button.offsetWidth, itemHeight: button.offsetHeight };
}

export function MovableGardenObject({ name, src, width, x, y, movable, busy, onSave }: Props) {
  const [draft, setDraft] = useState<(GardenPosition & { baseX: number; baseY: number }) | null>(null);
  const drag = useRef<{ id: number; clientX: number; clientY: number; position: GardenPosition; bounds: GardenBounds } | null>(null);
  const position = draft?.baseX === x && draft.baseY === y ? draft : { x, y };
  const preview = (next: GardenPosition) => setDraft({ ...next, baseX: x, baseY: y });
  async function save(next: GardenPosition) {
    if (next.x === x && next.y === y) { setDraft(null); return; }
    if (!await onSave(next)) setDraft(null);
  }

  return <button type="button" className={`j-game-object${movable ? " j-game-object--movable" : ""}`}
    disabled={!movable || busy} aria-label={movable ? `Move ${name}` : name}
    aria-describedby={movable ? "garden-arrange-help" : undefined}
    style={{ left: `${position.x}%`, top: `${position.y}%`, width: `${width}px` }}
    onPointerDown={event => {
      if (!movable || busy || event.button !== 0) return;
      event.preventDefault();
      event.currentTarget.setPointerCapture(event.pointerId);
      event.currentTarget.focus();
      drag.current = { id: event.pointerId, clientX: event.clientX, clientY: event.clientY, position, bounds: bounds(event.currentTarget) };
    }}
    onPointerMove={event => {
      const start = drag.current;
      if (!start || start.id !== event.pointerId) return;
      preview(gardenPosition({ x: start.position.x + (event.clientX - start.clientX) / start.bounds.width * 100,
        y: start.position.y + (event.clientY - start.clientY) / start.bounds.height * 100 }, start.bounds));
    }}
    onPointerUp={event => {
      const start = drag.current;
      if (!start || start.id !== event.pointerId) return;
      const next = gardenPosition({ x: start.position.x + (event.clientX - start.clientX) / start.bounds.width * 100,
        y: start.position.y + (event.clientY - start.clientY) / start.bounds.height * 100 }, start.bounds);
      drag.current = null;
      event.currentTarget.releasePointerCapture(event.pointerId);
      preview(next);
      void save(next);
    }}
    onPointerCancel={() => { drag.current = null; setDraft(null); }}
    onLostPointerCapture={() => { drag.current = null; }}
    onKeyDown={event => {
      if (!movable || busy) return;
      const step = event.shiftKey ? 5 : 2;
      const deltas: Record<string, GardenPosition> = { ArrowLeft: { x: -step, y: 0 }, ArrowRight: { x: step, y: 0 },
        ArrowUp: { x: 0, y: -step }, ArrowDown: { x: 0, y: step } };
      if (deltas[event.key]) {
        event.preventDefault();
        const delta = deltas[event.key];
        preview(gardenPosition({ x: position.x + delta.x, y: position.y + delta.y }, bounds(event.currentTarget)));
      } else if (event.key === "Enter" || event.key === " ") {
        event.preventDefault(); void save(position);
      } else if (event.key === "Escape") {
        event.preventDefault(); drag.current = null; setDraft(null);
      }
    }}>
    <Image src={src} width={256} height={256} alt="" draggable={false} />
  </button>;
}
