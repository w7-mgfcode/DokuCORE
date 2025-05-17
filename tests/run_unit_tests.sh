#!/bin/bash

# Run unit tests in the API container
docker-compose exec api python -m pytest /app/tests/indexing/ -v --tb=short

# Alternative: Run tests using the existing API container
# docker exec -it dokucore_api_1 python -m pytest /app/tests/indexing/ -v