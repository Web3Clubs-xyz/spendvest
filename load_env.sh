#!/bin/bash

# Check if .env file exists
if [ -f .env ]; then
    # Export each variable from the .env file
    export $(grep -v '^#' .env | xargs)
    echo "Environment variables loaded from .env file."
else
    echo ".env file not found."
fi
