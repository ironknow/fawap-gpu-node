#!/bin/bash
# Development run script for GPU Node

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the application
python3 -m src.main

