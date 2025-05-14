#!/bin/bash

# Run the tests
# This script runs the pytest tests with coverage reporting

set -e  # Exit on error

# Change to the project root directory
cd "$(dirname "$0")"

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
  echo "Warning: Not running in a virtual environment. This may cause issues with dependencies."
fi

# Install test requirements if they're not already installed
echo "Installing test requirements..."
pip install -r tests/requirements.txt

# Install the application in development mode if not already installed
if ! pip show api &> /dev/null; then
  echo "Installing the application in development mode..."
  pip install -e .
fi

# Run the tests with coverage
echo "Running tests with coverage..."
python -m pytest tests/ --cov=api --cov-report=term --cov-report=html:coverage_report

# Show test results
echo "Test results:"
echo "Coverage report is available in coverage_report/index.html"