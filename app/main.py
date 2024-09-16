from fastapi import FastAPI, HTTPException
from app.models.pool_api import (
    PoolUpsertBody,
    PoolUpsertResponse,
    PoolQueryBody,
    PoolQueryResponse,
    PoolUpsertStatusEnum,
)
from app.modules.pool_manager import PoolManager

app = FastAPI()
pool_manager = PoolManager()


@app.post("/pools/upsert", status_code=201)
async def upsert_pool(body: PoolUpsertBody) -> PoolUpsertResponse:
    """Upsert a pool, if the pool already exists, append the values to the pool.
    If the pool is inserted, return status "inserted", otherwise return status "appended".
    Status code 201 is returned in both cases.

    Args:
        body `PoolUpsertBody`: The body of the request

    Raises:
        `HTTPException` status code 422 if the body is invalid

    Returns:
        `PoolUpsertResponse` The response of the request
    """
    status = (
        PoolUpsertStatusEnum.appended
        if pool_manager.contains(body.pool_id)
        else PoolUpsertStatusEnum.inserted
    )
    pool_manager.upsert(body.pool_id, body.pool_values)
    return PoolUpsertResponse(status=status)


@app.post("/pools/query", status_code=200)
async def query_quantile(body: PoolQueryBody) -> PoolQueryResponse:
    """Query the quantile of a pool given a percentile. If the pool does not exist, return a 404.


    Args:
        body `PoolQueryBody`: The body of the request

    Raises:
        `HTTPException` status 404 if the pool does not exist
        `HTTPException` status 422 if the body is invalid

    Returns:
        `PoolQueryResponse` The response of the request
    """

    if not pool_manager.contains(body.pool_id):
        raise HTTPException(status_code=404, detail="Pool not found")

    quantile = pool_manager.get_quantile(body.pool_id, body.percentile)
    total_count = pool_manager.get_pool_len(body.pool_id)

    return PoolQueryResponse(quantile=quantile, totalCount=total_count)
