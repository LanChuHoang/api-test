from fastapi.testclient import TestClient
import pytest
from app.main import app, pool_manager


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_pool_manager():
    pool_manager._pools = {}
    yield
    pool_manager._pools = {}


class TestPoolUpsert:
    def test_data_type(self):
        """Test the validation of the request body data types."""

        # poolId must be an integer
        invalid_values = ["a", {}, 1.2, None, []]
        for value in invalid_values:
            response = client.post(
                "/pools/upsert",
                json={"poolId": value, "poolValues": [1.0, 2.0, 3.0]},
            )
            assert response.status_code == 422
            assert response.json()["detail"][0]["type"] == "int_type"

        # poolValues must be a list
        invalid_values = ["a", {}, 1, 1.0, None]
        for value in invalid_values:
            response = client.post(
                "/pools/upsert",
                json={"poolId": 1, "poolValues": value},
            )
            assert response.status_code == 422
            assert response.json()["detail"][0]["type"] == "list_type"

        # poolValues must be a list of floats
        invalid_values = [["a"], [1, "a"]]
        for value in invalid_values:
            response = client.post(
                "/pools/upsert",
                json={"poolId": 1, "poolValues": value},
            )
            assert response.status_code == 422
            assert response.json()["detail"][0]["type"] == "float_type"

        # poolValues must have at least one element
        response = client.post(
            "/pools/upsert",
            json={"poolId": 1, "poolValues": []},
        )
        assert response.status_code == 422
        assert response.json()["detail"][0]["type"] == "too_short"

    def test_missing_field(self):
        """Test the validation of the request body missing fields."""

        # poolId and poolValues are required fields
        invalid_body = [
            {"poolValues": [1.0, 2.0, 3.0]},
            {"poolId": 1},
            {"a": 1},
            {"pool_id": 1, "pool_values": [1.0, 2.0, 3.0]},
        ]
        for body in invalid_body:
            response = client.post("/pools/upsert", json=body)
            assert response.status_code == 422
            assert response.json()["detail"][0]["type"] == "missing"

    def test_upsert(self):
        """Test inserting a new pool and appending to this pool"""

        response = client.post(
            "/pools/upsert",
            json={"poolId": 1, "poolValues": [1.0, 2.0, 3.0]},
        )
        assert response.status_code == 201
        assert response.json() == {"status": "inserted"}

        response = client.post(
            "/pools/upsert",
            json={"poolId": 1, "poolValues": [4.0, 5.0]},
        )
        assert response.status_code == 201
        assert response.json() == {"status": "appended"}


class TestPoolQuery:
    def test_data_type(self):
        """Test the validation of the request body data types."""

        # poolId must be an integer
        invalid_values = ["a", {}, 1.2, None, []]
        for value in invalid_values:
            response = client.post(
                "/pools/query",
                json={"poolId": value, "percentile": 50},
            )
            assert response.status_code == 422
            assert response.json()["detail"][0]["type"] == "int_type"

        # percentile must be a float
        invalid_values = ["a", {}, None, []]
        for value in invalid_values:
            response = client.post(
                "/pools/query",
                json={"poolId": 1, "percentile": value},
            )
            assert response.status_code == 422
            assert response.json()["detail"][0]["type"] == "float_type"

        # percentile must be in the range (0, 100]
        configs = [
            (-1, "greater_than"),
            (0, "greater_than"),
            (100.1, "less_than_equal"),
        ]

        for value, expected_type in configs:
            response = client.post(
                "/pools/query",
                json={"poolId": 1, "percentile": value},
            )
            assert response.status_code == 422
            assert response.json()["detail"][0]["type"] == expected_type

    def test_missing_field(self):
        """Test the validation of the request body missing fields."""

        # poolId and percentile are required fields
        invalid_body = [
            {"percentile": 50},
            {"poolId": 1},
            {"a": 1},
            {"pool_id": 1, "percentile": 50},
        ]
        for body in invalid_body:
            response = client.post("/pools/query", json=body)
            assert response.status_code == 422
            assert response.json()["detail"][0]["type"] == "missing"

    def test_query_non_existent_pool(self):
        """Test querying a non-existent pool"""

        response = client.post(
            "/pools/query",
            json={"poolId": 1, "percentile": 50},
        )
        assert response.status_code == 404
        assert response.json() == {"detail": "Pool not found"}

    def test_query_small_pool(self):
        """Test querying a pool with less than or equal to 100 values.

        Test with every 0.1 increment in the percentile range (0, 100].

        Dataset: [15, 20, 35, 40, 50]. Expected quantiles:
        - 0.1 - 20th percentile: 15
        - 20.1 - 40th percentile: 20
        - 40.1 - 60th percentile: 35
        - 60.1 - 80th percentile: 40
        - 80.1 - 100th percentile: 50
        """

        response = client.post(
            "/pools/upsert",
            json={"poolId": 1, "poolValues": [15, 20, 35, 40, 50]},
        )
        assert response.status_code == 201

        expected_quantiles = {20: 15, 40: 20, 60: 35, 80: 40, 100: 50}
        for end in range(20, 101, 20):
            percentile = end - 20 + 0.1
            while percentile <= end:
                response = client.post(
                    "/pools/query",
                    json={"poolId": 1, "percentile": percentile},
                )
                assert response.status_code == 200
                assert response.json() == {
                    "quantile": expected_quantiles[end],
                    "totalCount": 5,
                }
                percentile += 0.1

    def test_query_large_pool(self):
        """Test querying a pool with more than 100 values.

        Dataset: [1, 2, 3, ..., 200]. Expected quantiles:
        - 25th percentile: 50
        - 50th percentile: 100
        - 100th percentile: 200
        """

        response = client.post(
            "/pools/upsert",
            json={"poolId": 1, "poolValues": list(range(1, 201))},
        )
        assert response.status_code == 201

        configs = [(25, 50), (50, 100), (100, 200)]

        for percentile, expected_quantile in configs:
            response = client.post(
                "/pools/query",
                json={"poolId": 1, "percentile": percentile},
            )
            assert response.status_code == 200
            assert response.json() == {
                "quantile": expected_quantile,
                "totalCount": 200,
            }

    def test_query_single_element_pool(self):
        """Test querying a pool with a single element.

        Dataset: [10.0]. Expected quantiles: 10.0 for all percentiles in the range (0, 100].
        """

        response = client.post(
            "/pools/upsert",
            json={"poolId": 1, "poolValues": [10.0]},
        )
        assert response.status_code == 201

        p = 0.1
        while p <= 100:
            response = client.post(
                "/pools/query",
                json={"poolId": 1, "percentile": p},
            )
            assert response.status_code == 200
            assert response.json() == {"quantile": 10.0, "totalCount": 1}
            p += 0.1
