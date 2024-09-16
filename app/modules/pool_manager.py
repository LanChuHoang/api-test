import numpy as np
import math


class PoolManager:
    """
    PoolManager is a class that manages pools of values and provides methods to query quantiles of the pools.

    Pools are stored in a dictionary where the key is the pool_id and the value is a list of floats.

    Pools are not stored in a database, so they are lost when the application is restarted.
    """

    def __init__(self) -> None:
        self._pools: dict[int, list[float]] = dict()

    def contains(self, pool_id: int) -> bool:
        """Check if a pool exists.

        Args:
            pool_id (int): The id of the pool

        Returns:
            bool: True if the pool exists, False otherwise
        """
        return pool_id in self._pools

    def upsert(self, pool_id: int, pool_values: list[float]):
        """Upsert a pool of values. If the pool already exists,
        append the values to the pool, otherwise create a new pool.

        Args:
            pool_id (int): The id of the pool
            pool_values (list[float]): THE values to upsert
        """

        if pool_id not in self._pools:
            self._pools[pool_id] = pool_values
        else:
            self._pools[pool_id].extend(pool_values)

    def get_quantile(self, pool_id: int, percentile: float) -> float:
        """Get the quantile of a pool given a percentile using the `nearest rank` method.

        If the pool has less than or equal to 100 values, the method sorts the values
        and returns the value at the index corresponding to the percentile. Otherwise, it
        uses the `inverted_cdf` method of the `numpy.percentile` function.

        Args:
            pool_id (int): The id of the pool
            percentile (float): The percentile value in the range (0, 100]

        Raises:
            KeyError: If the pool does not exist
            ValueError: If the percentile is not in the range (0, 100]
            TypeError: If the percentile is not a float


        Returns:
            float: The quantile value corresponding to the percentile of the pool
        """

        if percentile <= 0 or percentile > 100:
            raise ValueError("Percentile must be in the range (0, 100]")

        values = self._pools[pool_id]
        n = len(values)

        if n > 100:
            return np.percentile(values, percentile, method="inverted_cdf")

        sorted_values = sorted(values)
        index = math.ceil(percentile / 100 * n) - 1
        return sorted_values[index]

    def get_pool_len(self, pool_id: int):
        return len(self._pools[pool_id])
