#!/bin/bash

CUDA_VISIBLE_DEVICES=0 llamafactory-cli export \
    --model_name_or_path meta-llama/Meta-Llama-3-8B \
    --adapter_name_or_path saves/LLaMA3-8B/lora/TheBigSix_6/checkpoint-1600 \
    --template llama3 \
    --finetuning_type lora \
    --export_dir models/llama3_q4_lora_chp1600_TheBigSix \
    --export_size 18 \
    --export_legacy_format False \
