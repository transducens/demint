#!/bin/bash

CUDA_VISIBLE_DEVICES=0 llamafactory-cli chat \
    --model_name_or_path models/llama3_q4_lora_chp1600_TheBigSix \
    --template llama3 \
    --quantization_bit 4 \
    --finetuning_type lora \
    --flash_attn fa2 \
    --max_samples 100000 \
    --max_new_tokens 150 \
    --temperature 1.0 \
    --top_p 0.7 \
#    --cutoff_len 32 \
#    --length_penalty 1.5 \
#    --top_k 2 \
#    --model_name_or_path meta-llama/Meta-Llama-3-8B-Instruct \
#    --adapter_name_or_path saves/LLaMA3-8B/lora/TheBigSix_7/checkpoint-2900 \

# Con top_p 0.6 y temp 1.1 no lo hace mal pero se desvia un poco del tema.
# Con top_p 0.6 y temp 0.5 cae en repeticion de palabras facilmente 
# Con top_p 0.6 y temp 1.0 responde bien la pregunta pero luego sigue diciendo cosas aleatorias. 
# Con top_p 0.6 y temp 1.2 puede responder con sentido pero igual no entiende bien la pregunta y te responde a otra intencion. 
# Con top_p 0.7 y temperature 1.0 me han gustado las respuestas. Mas o menos son decentes.
