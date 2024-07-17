#!/bin/bash

# Set environment variables from command-line arguments
export GRADIO_SPEAKER="$1"

CUDA="CUDA_VISIBLE_DEVICES=1"

# Run the Gradio app
eval "${CUDA} gradio user_app.py"

