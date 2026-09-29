from decimal import Decimal
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from pydantic import UUID4

from store.core.exceptions import CreateException, NotFoundException
from store.schemas.product import ProductIn, ProductOut, ProductUpdate, ProductUpdateOut
from store.usecases.product import ProductUsecase

router = APIRouter(tags=["products"])


@router.post(path="/", status_code=status.HTTP_201_CREATED)
async def post(body: ProductIn = Body(...), usecase: ProductUsecase = Depends()) -> ProductOut:
    try:
        return await usecase.create(body=body)
    except CreateException as exc:
        raise HTTPException(status_code=500, detail=exc.message) from exc


@router.get(path="/{id}", status_code=status.HTTP_200_OK)
async def get(id: UUID4 = Path(alias="id"), usecase: ProductUsecase = Depends()) -> ProductOut:
    try:
        return await usecase.get(id=id)
    except NotFoundException as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc


@router.get(path="/", status_code=status.HTTP_200_OK)
async def query(
    min_price: Decimal | None = Query(None, description="Exclusive lower price bound"),
    max_price: Decimal | None = Query(None, description="Exclusive upper price bound"),
    price_gt: Decimal | None = Query(None, description="Alias for min_price"),
    price_lt: Decimal | None = Query(None, description="Alias for max_price"),
    usecase: ProductUsecase = Depends(),
) -> List[ProductOut]:
    return await usecase.query(
        min_price=min_price if min_price is not None else price_gt,
        max_price=max_price if max_price is not None else price_lt,
    )


@router.patch(path="/{id}", status_code=status.HTTP_200_OK)
async def patch(
    id: UUID4 = Path(alias="id"),
    body: ProductUpdate = Body(...),
    usecase: ProductUsecase = Depends(),
) -> ProductUpdateOut:
    try:
        return await usecase.update(id=id, body=body)
    except NotFoundException as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc


@router.delete(path="/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: UUID4 = Path(alias="id"), usecase: ProductUsecase = Depends()) -> None:
    try:
        await usecase.delete(id=id)
    except NotFoundException as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc
