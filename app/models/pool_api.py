from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from typing_extensions import Annotated
from enum import Enum


class BaseApiModel(BaseModel):
    """Base class for API models. It configures the alias generator
    to camel case and strict mode for every model.
    """

    model_config = ConfigDict(alias_generator=to_camel, strict=True)


class PoolUpsertBody(BaseApiModel):
    """The body of the upsert request."""

    pool_id: int
    pool_values: Annotated[
        list[float],
        Field(min_length=1, description="The non-empty list of pool values."),
    ]


class PoolQueryBody(BaseApiModel):
    """The body of the query request."""

    pool_id: int
    percentile: Annotated[
        float,
        Field(
            strict=True,
            gt=0,
            le=100,
            description="The percentile value. Must be in the range (0, 100].",
        ),
    ]


class PoolUpsertStatusEnum(str, Enum):
    """The status Enum of the upsert request."""

    appended = "appended"
    inserted = "inserted"


class PoolUpsertResponse(BaseApiModel):
    """The response of the upsert request."""

    status: PoolUpsertStatusEnum


class PoolQueryResponse(BaseApiModel):
    """The response of the query request."""

    quantile: float
    total_count: int
