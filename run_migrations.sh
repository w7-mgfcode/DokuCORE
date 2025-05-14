#!/bin/bash

# Change to the project root directory
cd "$(dirname "$0")"

# Check if alembic is installed
if ! command -v alembic &> /dev/null; then
    echo "Installing alembic..."
    pip install alembic
fi

# Install required packages
pip install -r api/requirements.txt

# Run migrations
cd migrations
alembic upgrade head

echo "Migrations completed successfully!"