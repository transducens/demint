#!/bin/bash

# Set environment variables from command-line arguments
export GRADIO_SPEAKER="$1"

# Run the Gradio app
gradio user_app.py

