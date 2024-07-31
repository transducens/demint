#!/bin/bash

# Default settings (empty means no setting)
CUDA=""
GRADIO_SPEAKER=""
PORT=""
CONVER=""

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
        --port )
            shift
            PORT="$1"
            ;;
        --conver )
            shift
            CONVER="$1"
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

# Build the command
COMMAND="${CUDA} gradio user_app.py"

# Append port parameter if set
if [ -n "$PORT" ]; then
    COMMAND="$COMMAND --port $PORT"
fi

# Append conver parameter if set
if [ -n "$CONVER" ]; then
    COMMAND="$COMMAND --conver $CONVER"
fi

# Run the Gradio app with optional CUDA setting, port, and conver
eval $COMMAND

