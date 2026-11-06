export type ShopCategory = "flowers" | "trees" | "animals" | "decor";

type GameAsset = {
  src: string;
  category: ShopCategory;
  scale?: number;
};

export const gameAssets: Record<string, GameAsset> = {
  plant_sunflower: { src: "/game-assets/Objects/Plants/Sunflower/sunflower-stage-3.png", category: "flowers" },
  plant_daisy: { src: "/game-assets/Objects/Plants/Daisy/daisy-stage-3.png", category: "flowers" },
  plant_orchid: { src: "/game-assets/Objects/Plants/Orchid/orchid-stage-3.png", category: "flowers" },
  plant_red_rose: { src: "/game-assets/Objects/Plants/Roses/Red/redrose-stage-3.png", category: "flowers" },
  plant_pink_rose: { src: "/game-assets/Objects/Plants/Roses/Pink/pinkrose-stage-3.png", category: "flowers" },
  plant_purple_rose: { src: "/game-assets/Objects/Plants/Roses/Purple/purplerose-stage-3.png", category: "flowers" },
  plant_gold_rose: { src: "/game-assets/Objects/Plants/Roses/Gold/goldrose-stage-3.png", category: "flowers" },
  plant_red_tulip: { src: "/game-assets/Objects/Plants/Tulips/Red/redtulip-stage-3.png", category: "flowers" },
  plant_pink_tulip: { src: "/game-assets/Objects/Plants/Tulips/Pink/pinktulip-stage-3.png", category: "flowers" },
  plant_purple_tulip: { src: "/game-assets/Objects/Plants/Tulips/Purple/purpletulip-stage-3.png", category: "flowers" },
  plant_gold_tulip: { src: "/game-assets/Objects/Plants/Tulips/Gold/goldtulip-stage-3.png", category: "flowers" },
  tree_apple: { src: "/game-assets/Objects/Trees/Apple/apple-stage-3.png", category: "trees", scale: 1.35 },
  tree_coconut: { src: "/game-assets/Objects/Trees/Coconut/coconuttree-stage-3.png", category: "trees", scale: 1.35 },
  pet_bird: { src: "/game-assets/Characters/Bird/bird.png", category: "animals" },
  pet_cat: { src: "/game-assets/Characters/Cat/cat.png", category: "animals" },
  pet_chicken: { src: "/game-assets/Characters/Chicken/chicken.png", category: "animals" },
  pet_dog: { src: "/game-assets/Characters/Dog/dog.png", category: "animals" },
  pet_duck: { src: "/game-assets/Characters/Duck/duck.png", category: "animals" },
  pet_fish: { src: "/game-assets/Characters/Fish/fish.png", category: "animals" },
  pet_calico_cat: { src: "/game-assets/Characters/Cat/cat.png", category: "animals" },
  decor_bush: { src: "/game-assets/Objects/Decorations/bush.png", category: "decor" },
  decor_log: { src: "/game-assets/Objects/Decorations/log.png", category: "decor" },
  decor_mushroom: { src: "/game-assets/Objects/Decorations/mushroom.png", category: "decor" },
  decor_rock: { src: "/game-assets/Objects/Decorations/rock.png", category: "decor" },
  decor_grass_tuft: { src: "/game-assets/Objects/Decorations/grass-tuft.png", category: "decor" },
  decor_bridge: { src: "/game-assets/Objects/Bridges/bridge-horizontal.png", category: "decor", scale: 1.5 },
  decor_fence: { src: "/game-assets/Objects/Fences/fence-horizontal.png", category: "decor", scale: 1.35 },
  decor_gate: { src: "/game-assets/Objects/Fences/gate.png", category: "decor", scale: 1.35 },
  decor_cottage: { src: "/game-assets/Objects/Buildings/cottage.png", category: "decor", scale: 1.65 },
  decor_greenhouse: { src: "/game-assets/Objects/Buildings/greenhouse.png", category: "decor", scale: 1.65 },
  decor_shed: { src: "/game-assets/Objects/Buildings/shed.png", category: "decor", scale: 1.65 },
};

export function gameAsset(assetKey: string) {
  return gameAssets[assetKey];
}
