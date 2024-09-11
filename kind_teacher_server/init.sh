#!/bin/bash

# Install the package in editable mode with torch and metrics extras
pip install -e .[torch,metrics]

# Install bitsandbytes with version 0.37.0 or higher
pip install bitsandbytes>=0.37.0

# Install transformers version 4.43.3
pip install transformers==4.43.3

# Install flash attention 2
pip install flash-attn

# Install emoji for processing dataset
pip install emoji

