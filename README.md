# API Test

## Overview

This is a FastAPI application that provides an API for creating and querying pools.

The documentation for the source code and the test cases is written in the code itself via comments. The Swagger documentation for the API is available at `http://localhost:8000/docs`.

There are 3 endpoints in this API:

1. `POST /pools/upsert`: This endpoint is used for create or update a pool
2. `POST /pools/query`: This endpoint is used for query pools by id and percentile
   and return the quantile value corresponding to the percentile of the pool
3. `GET /docs`: This endpoint is used for show the API Swagger documentation

The state of the pools is stored in memory and is not persisted. The state is also not shared between multiple instances of the application.

### Project Structure

The project structure is as follows:

```plaintext
app/
├── models/                # Pydantic models for the API
├── modules/               # Modules for the API, including the PoolManager module for managing pools
├── main.py                # FastAPI application, including the API routing logic
tests/
├── test_main.py           # Integration tests for the API
|── test_pool_manager.py   # Unit tests for the PoolManager module
```

Documentation for each module is available in the respective module files.

### Method used for the quantile calculation

The quantile calculation is done using the `nearest rank` method. By [Wikipedia](https://en.wikipedia.org/wiki/Percentile#The_nearest-rank_method), the value of the `p-th` percentile is calculated as:

```math
{\displaystyle n=\left\lceil {\frac {P}{100}}\times N\right\rceil .}
```

where

- `n` is the index of the value in the sorted dataset that corresponds to the `p-th` percentile starting from 1
- `P` is the percentile (0 < P <= 100), 100th percentile is the maximum value in the dataset
- `N` is the number of values in the dataset

For example, if we have a dataset `[15, 20, 35, 40, 50]`, the quantile values are:

- 0.1th to 20th percentile = 15
- 20.1th to 40th percentile = 20
- 40.1th to 60th percentile = 35
- 60.1th to 80th percentile = 40
- 80.1th to 100th percentile = 50

With small datasets (<= 100 values), a custom Python code is used, and for large datasets (> 100 values), the `numpy.percentile(method="inverted_cdf")` method is used for better performance.

## How to run

### Run the application

The application is dockerized, so you need to have Docker installed on your machine, then you can run the following command:

```bash
docker compose up app
```

The API will be available at `http://localhost:8000`. You can access the Swagger documentation at `http://localhost:8000/docs`.

To stop the application, type `Ctrl+C` and then run this command to completely remove the containers:

```bash
docker compose down
```

### Run tests

Test files are located in the `tests` directory, written using `pytest`. To run the tests, you can run the following command:

```bash
docker compose up test
```

The output will show the test results via `stdout`.

## Future improvements

Since the state of the pools is stored in memory, it is not persisted and there will be inconsistent data when multiple instances of the application are running.

To solve this, we can use a shared memory layer like `Redis` with persistence option enabled to store the state of the pools between multiple instances of the application. With this, we can achieve High Availability and Fault Tolerance easily by scaling the application horizontally while maintaining the fast response time.
