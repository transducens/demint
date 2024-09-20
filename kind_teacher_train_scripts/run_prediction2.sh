#!/bin/bash

CUDA_VISIBLE_DEVICES=1 llamafactory-cli train \
    --stage sft \
    --model_name_or_path models/llama3_q4_lora_chp1600_TheBigSix \
    --finetuning_type lora \
    --quantization_bit 4 \
    --template llama3 \
    --flash_attn fa2 \
    --rope_scaling linear \
    --dataset_dir data \
    --eval_dataset TheBigSix_alpaca_divided_sorted_test \
    --cutoff_len 4096 \
    --max_samples 100000 \
    --per_device_eval_batch_size 1 \
    --predict_with_generate True \
    --max_new_tokens 256 \
    --output_dir saves/LLaMA3-8B/lora/TheBigSix_8_test_2 \
    --do_predict True \
    --prediction_loss_only False \
    --temperature 1.0 \
    --top_p 0.7 \
    --plot_loss True \
#    --top_k 5 \
