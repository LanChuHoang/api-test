import pytest
from app.modules.pool_manager import PoolManager


@pytest.fixture
def pool_manager():
    return PoolManager()


def test_pool_existence_checking(pool_manager):
    """Test the contains method."""

    assert not pool_manager.contains(1)
    pool_manager.upsert(1, [1, 2])
    assert pool_manager.contains(1)


def test_upsert_new_pool(pool_manager):
    """Test the upsert method with a new pool."""

    pool_manager.upsert(1, [1.0, 2.0, 3.0])
    assert pool_manager._pools[1] == [1.0, 2.0, 3.0]


def test_upsert_existing_pool(pool_manager):
    """Test the upsert method with an existing pool."""

    pool_manager.upsert(1, [1.0, 2.0, 3.0])
    pool_manager.upsert(1, [4.0, 5.0])
    assert pool_manager._pools[1] == [1.0, 2.0, 3.0, 4.0, 5.0]


def test_upsert_empty_pool(pool_manager):
    """Test the upsert method with an empty pool."""

    pool_manager.upsert(1, [])
    assert pool_manager._pools[1] == []


def test_get_quantile_small_pool(pool_manager):
    """Test the get_quantile method with a small pool.

    Check every 0.1 percentile from 0.1 to 100.0.
    """

    pool_manager.upsert(1, [15, 20, 35, 40, 50])
    expected_quantiles = {20: 15, 40: 20, 60: 35, 80: 40, 100: 50}
    for end in range(20, 101, 20):
        percentile = end - 20 + 0.1
        while percentile <= end:
            assert pool_manager.get_quantile(1, percentile) == expected_quantiles[end]
            percentile += 0.1


def test_get_quantile_large_pool(pool_manager):
    """Test the get_quantile method with a large pool.

    Check the 25th, 50th, and 100th percentiles.
    """

    large_pool = list(range(1, 201))
    pool_manager.upsert(1, large_pool)

    assert pool_manager.get_quantile(1, 25) == 50
    assert pool_manager.get_quantile(1, 50) == 100
    assert pool_manager.get_quantile(1, 100) == 200


def test_get_quantile_non_existent_pool(pool_manager):
    """Test the get_quantile method with a non-existent pool.

    The method should raise a KeyError.
    """

    with pytest.raises(KeyError):
        pool_manager.get_quantile(1, 50)


def test_get_quantile_single_element_pool(pool_manager):
    """Test the get_quantile method with a single-element pool.

    Check every 0.1 percentile from 0.1 to 100. The method should return
    the single element for all percentiles.
    """

    pool_manager.upsert(1, [10.0])

    p = 0.1
    while p <= 100:
        assert pool_manager.get_quantile(1, p) == 10.0
        p += 0.1


def test_get_quantile_empty_pool(pool_manager):
    """Test the get_quantile method with an empty pool.

    The method should raise an IndexError.
    """

    pool_manager.upsert(1, [])
    with pytest.raises(IndexError):
        pool_manager.get_quantile(1, 50)


def test_get_quantile_invalid_percentile(pool_manager):
    """Test the get_quantile method with invalid percentiles.

    The method should raise a ValueError.
    """

    pool_manager.upsert(1, [1, 2, 3])
    invalid_values = [-1, 0, 100.1]
    for value in invalid_values:
        with pytest.raises(ValueError):
            pool_manager.get_quantile(1, value)

    invalid_types = ["a", None, [], {}]
    for value in invalid_types:
        with pytest.raises(TypeError):
            pool_manager.get_quantile(1, value)


def test_get_pool_len(pool_manager):
    """Test the get_pool_len method.

    The method should return the length of the pool in normal cases
    and raise a KeyError if the pool does not exist.
    """

    # Normal case
    pool_manager.upsert(1, [1, 2, 3])
    assert pool_manager.get_pool_len(1) == 3

    # Empty pool
    pool_manager.upsert(2, [])
    assert pool_manager.get_pool_len(2) == 0

    # Non-existent pool
    with pytest.raises(KeyError):
        pool_manager.get_pool_len(3)
