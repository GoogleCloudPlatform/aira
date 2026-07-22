#!/bin/bash

# Set PYTHONPATH to include the current directory (so 'tools' is discoverable as a top-level module)
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Load local environment variables
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Run the Google ADK playground web server pointing to the current directory
echo "Starting Google ADK Playground for local testing..."
poetry run adk web .
