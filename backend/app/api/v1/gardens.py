from typing import List
from uuid import UUID
from fastapi import APIRouter, Request, status
from app.api.dependencies import CurrentUser, DbSession
from app.schemas.common import ResponseEnvelope, SuccessStatus
from app.schemas.garden import (
    GardenResponse,
    GardenCatalogItemResponse,
    GardenItemResponse,
    GardenPurchaseRequest,
    GardenPlaceItemRequest,
    PointTransactionResponse,
)
from app.services.garden_service import GardenService
from app.utils.response import wrap_response

router = APIRouter(tags=["Gardens"])


@router.get("/gardens", response_model=ResponseEnvelope[List[GardenResponse]])
async def list_gardens(
    request: Request,
    current_user: CurrentUser,
    db: DbSession,
):
    service = GardenService(db)
    gardens = service.list_gardens(current_user.id)
    return wrap_response(gardens, request)


@router.get("/gardens/{garden_id}", response_model=ResponseEnvelope[GardenResponse])
async def get_garden(
    request: Request,
    garden_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = GardenService(db)
    garden = service.get_garden(current_user.id, garden_id)
    return wrap_response(garden, request)


@router.get("/gardens/{garden_id}/inventory", response_model=ResponseEnvelope[List[GardenItemResponse]])
async def get_garden_inventory(
    request: Request,
    garden_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = GardenService(db)
    items = service.get_inventory(current_user.id, garden_id)
    return wrap_response(items, request)


@router.get("/gardens/{garden_id}/ledger", response_model=ResponseEnvelope[List[PointTransactionResponse]])
async def get_garden_ledger(
    request: Request,
    garden_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = GardenService(db)
    transactions = service.get_ledger(current_user.id, garden_id)
    return wrap_response(transactions, request)


@router.get("/shop/items", response_model=ResponseEnvelope[List[GardenCatalogItemResponse]])
async def list_shop_items(
    request: Request,
    current_user: CurrentUser,
    db: DbSession,
):
    service = GardenService(db)
    items = service.list_catalog_items()
    return wrap_response(items, request)


@router.post("/gardens/{garden_id}/purchases", response_model=ResponseEnvelope[SuccessStatus], status_code=status.HTTP_201_CREATED)
async def purchase_garden_item(
    request: Request,
    garden_id: UUID,
    payload: GardenPurchaseRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    service = GardenService(db)
    service.purchase_item(current_user.id, garden_id, payload.catalog_item_id, payload.quantity)
    return wrap_response(SuccessStatus(success=True, message="Item purchased successfully"), request)


@router.post("/gardens/{garden_id}/items/{item_id}/place", response_model=ResponseEnvelope[SuccessStatus])
async def place_garden_item(
    request: Request,
    garden_id: UUID,
    item_id: UUID,
    payload: GardenPlaceItemRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    service = GardenService(db)
    service.place_item(current_user.id, garden_id, item_id, payload.position_x, payload.position_y)
    return wrap_response(SuccessStatus(success=True, message="Item placed successfully"), request)
