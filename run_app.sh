#!/bin/bash

# Default CUDA setting (empty means no CUDA setting)
CUDA=""
GRADIO_SPEAKER=""

# Parse command-line arguments
while [[ "$1" != "" ]]; do
    case $1 in
        --cuda )
            shift
            CUDA="CUDA_VISIBLE_DEVICES=$1"
            ;;
        --speaker )
            shift
            GRADIO_SPEAKER="$1"
            ;;
        * )
            echo "Unknown parameter: $1"
            exit 1
            ;;
    esac
    shift
done

# Set environment variables
export GRADIO_SPEAKER

# Run the Gradio app with optional CUDA setting
eval "${CUDA} gradio user_app.py"

