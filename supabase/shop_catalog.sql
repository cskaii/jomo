-- JOMO garden shop: links the 30 existing art assets to purchasable items.

-- Run in Supabase SQL Editor. Repeatable: existing items and prices are preserved.

-- No users, balances, inventory, activities, quests or permissions are changed.

BEGIN;

LOCK TABLE public.garden_catalog_items IN SHARE ROW EXCLUSIVE MODE;

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT '016d9242ec955704a2c2a64324c0d717', 'Sunflower', 'A bright golden flower for a sunny corner.', 'seed', 25, 'plant_sunflower', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'plant_sunflower');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT 'e3be112970fc5f0fb10afe38252e5c6f', 'Daisy', 'A cheerful white garden daisy.', 'seed', 25, 'plant_daisy', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'plant_daisy');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT '00108ff84e9157419917d85f9c661588', 'Orchid', 'A delicate purple orchid in full bloom.', 'plant', 45, 'plant_orchid', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'plant_orchid');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT '32c88ae1a59f5e228cce0d25852e92f8', 'Red Rose', 'A classic red rose bush.', 'seed', 35, 'plant_red_rose', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'plant_red_rose');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT '93c7dd872226530081cd7db48204597e', 'Pink Rose', 'A soft pink rose bush.', 'seed', 35, 'plant_pink_rose', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'plant_pink_rose');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT '4fcd3bf4e6805ac482fa4c1ba5fe7059', 'Purple Rose', 'A dreamy purple rose bush.', 'seed', 40, 'plant_purple_rose', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'plant_purple_rose');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT 'f15ba082a7ae5a0085f50e5401461c82', 'Golden Rose', 'A rare rose with golden petals.', 'plant', 60, 'plant_gold_rose', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'plant_gold_rose');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT 'cc711b9266215fad98f6736bcd5a846d', 'Red Tulip', 'A bold red spring tulip.', 'seed', 30, 'plant_red_tulip', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'plant_red_tulip');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT 'd24ae0b413a65ff9ae62baa5d52ece10', 'Pink Tulip', 'A warm pink spring tulip.', 'seed', 30, 'plant_pink_tulip', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'plant_pink_tulip');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT '24dbfd93f4d95bd3a3c47a1924173fd4', 'Purple Tulip', 'A violet tulip for a calm patch.', 'seed', 35, 'plant_purple_tulip', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'plant_purple_tulip');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT '8cfa5358f5815767a41e01ff10792a4a', 'Golden Tulip', 'A rare golden tulip.', 'plant', 55, 'plant_gold_tulip', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'plant_gold_tulip');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT '99152af686585d658291542682088586', 'Apple Tree', 'A full apple tree that anchors the garden.', 'plant', 110, 'tree_apple', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'tree_apple');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT 'e6f6e5c9e2f557b482eb59c28bb28b68', 'Coconut Tree', 'A tropical coconut tree for the island edge.', 'plant', 120, 'tree_coconut', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'tree_coconut');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT '7e566690a90f5ab3965dc1edb973b893', 'Blue Bird', 'A tiny blue garden visitor.', 'pet', 75, 'pet_bird', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'pet_bird');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT '1a2502d2a80f587d82f32bc6b5a74e28', 'Garden Cat', 'A friendly cat who enjoys the warm grass.', 'pet', 100, 'pet_calico_cat', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'pet_calico_cat');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT '83c73703d7b750e2972e3028a7450f21', 'Chicken', 'A curious chicken for your garden flock.', 'pet', 85, 'pet_chicken', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'pet_chicken');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT '65a34451f7c55c71b197342a17635b3b', 'Puppy', 'A playful puppy to keep you company.', 'pet', 110, 'pet_dog', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'pet_dog');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT 'f0c3fcc955615d79acd8494847f900b8', 'Duck', 'A bright little duck for the waterside.', 'pet', 90, 'pet_duck', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'pet_duck');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT 'cbca8495751c560b8a6a35811b802c2f', 'Goldfish', 'A lively orange fish for the pond.', 'pet', 70, 'pet_fish', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'pet_fish');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT '07aaddee725b5b17babf2832b8db6699', 'Leafy Bush', 'A round green bush for filling quiet corners.', 'decoration', 30, 'decor_bush', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'decor_bush');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT '8dcd927e864256d09a87414cb072db18', 'Mossy Log', 'A fallen log with a little moss.', 'decoration', 35, 'decor_log', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'decor_log');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT '105120e1f24a5aa5b29f73aa38501548', 'Purple Mushroom', 'A whimsical purple mushroom.', 'decoration', 25, 'decor_mushroom', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'decor_mushroom');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT '7f797b94203c5e07aecb0adaa762eece', 'Garden Rock', 'A smooth stone for a natural border.', 'decoration', 20, 'decor_rock', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'decor_rock');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT '7986dd561704586787044cd619eeceb1', 'Grass Tuft', 'A small tuft of wild grass.', 'decoration', 15, 'decor_grass_tuft', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'decor_grass_tuft');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT '67f9cbe19d1c57658f45bcf633004506', 'Wooden Bridge', 'A broad wooden bridge for crossing water.', 'decoration', 90, 'decor_bridge', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'decor_bridge');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT '47c655dafbd15c238cbcfc96354faf1c', 'Wooden Fence', 'A low fence section for shaping your patch.', 'decoration', 30, 'decor_fence', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'decor_fence');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT '49df5ab9dc795b96ab55be182969c429', 'Flower Gate', 'A welcoming wooden garden gate.', 'decoration', 55, 'decor_gate', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'decor_gate');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT '74f91906e1ca5ec69c4a5788afa9251a', 'Cozy Cottage', 'A warm cottage with a terracotta roof.', 'decoration', 180, 'decor_cottage', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'decor_cottage');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT '7aaff7cf905e5c84b5356eff058a1360', 'Greenhouse', 'A glass greenhouse for special plants.', 'decoration', 160, 'decor_greenhouse', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'decor_greenhouse');

INSERT INTO public.garden_catalog_items
    (id, name, description, item_type, price_points, asset_key, is_active, created_at)
    SELECT '69e9713d91535549949265be67e861ec', 'Garden Shed', 'A tidy wooden shed for garden tools.', 'decoration', 130, 'decor_shed', true, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM public.garden_catalog_items WHERE asset_key = 'decor_shed');

COMMIT;

SELECT name, item_type, price_points, asset_key FROM public.garden_catalog_items WHERE is_active = true ORDER BY item_type, name;
