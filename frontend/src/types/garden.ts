import { GardenType, GardenItemType, PointTransactionType } from "@/types/enums";

export interface GardenCatalogItem {
  id: string;
  name: string;
  description: string;
  item_type: GardenItemType;
  price_points: number;
  asset_key: string;
  is_active: boolean;
}

export interface GardenItem {
  id: string;
  garden_id: string;
  catalog_item_id: string;
  catalog_item?: GardenCatalogItem;
  quantity: number;
  position_x?: number | null;
  position_y?: number | null;
  placed_at?: string | null;
}

export interface Garden {
  id: string;
  garden_type: GardenType;
  owner_user_id?: string | null;
  owner_group_id?: string | null;
  name: string;
  points_balance: number;
  growth_level: number;
  created_at: string;
  updated_at: string;
}

export interface PointTransaction {
  id: string;
  garden_id: string;
  user_id: string;
  activity_participant_id?: string | null;
  transaction_type: PointTransactionType;
  amount: number;
  reason: string;
  created_at: string;
}
