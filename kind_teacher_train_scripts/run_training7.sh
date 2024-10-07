#!/bin/bash

CUDA_VISIBLE_DEVICES=0 llamafactory-cli train \
    --stage sft \
    --do_train True \
    --model_name_or_path meta-llama/Meta-Llama-3-8B \
    --finetuning_type lora \
    --quantization_bit 8 \
    --template llama3 \
    --flash_attn fa2 \
    --dataset_dir data \
    --dataset TheBigSix_alpaca_divided_sorted_train \
    --eval_dataset TheBigSix_alpaca_divided_sorted_val \
    --cutoff_len 4096 \
    --learning_rate 0.0001 \
    --num_train_epochs 100 \
    --per_device_train_batch_size 12 \
    --gradient_accumulation_steps 1 \
    --lr_scheduler_type linear \
    --max_grad_norm 1.0 \
    --logging_steps 10 \
    --save_steps 100 \
    --warmup_steps 10 \
    --optim adamw_torch \
    --output_dir saves/LLaMA3-8B/lora/TheBigSix_8_temp \
    --overwrite_output_dir \
    --overwrite_cache True \
    --fp16 True \
    --lora_rank 8 \
    --lora_alpha 16 \
    --lora_dropout 0 \
    --lora_target all \
    --evaluation_strategy steps \
    --eval_steps 100 \
    --per_device_eval_batch_size 12 \
    --load_best_model_at_end True \
    --plot_loss True \
    --save_total_limit 5 \
    --resume_from_checkpoint saves/LLaMA3-8B/lora/TheBigSix_7/checkpoint-4000 \

