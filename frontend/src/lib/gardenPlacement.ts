export type GardenPosition = { x: number; y: number };
export type GardenBounds = { width: number; height: number; itemWidth: number; itemHeight: number };

export function gardenPosition(point: GardenPosition, bounds: GardenBounds): GardenPosition {
  const left = Math.min(49, bounds.itemWidth / 2 / Math.max(1, bounds.width) * 100 + 1);
  const top = Math.min(71, bounds.itemHeight * .72 / Math.max(1, bounds.height) * 100 + 1);
  const bottom = Math.min(27, bounds.itemHeight * .28 / Math.max(1, bounds.height) * 100 + 1);
  const round = (value: number) => Math.round(value * 100) / 100;
  return { x: round(Math.max(left, Math.min(100 - left, point.x))),
    y: round(Math.max(top, Math.min(100 - bottom, point.y))) };
}
