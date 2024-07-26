#!/bin/bash

CUDA="CUDA_VISIBLE_DEVICES=1"

eval "${CUDA} python -m app.extract_audio"  # from assets/videos to assets/audios 
eval "${CUDA} python -m app.diarize_audio"  # from assets/audios to cache/diarized_audios
# eval "${CUDA} python -m app.whisper"      # from cache/diarized_audios to cache/diarized_transcripts
eval "${CUDA} python -m app.prepare_sentences"
eval "${CUDA} python -m app.obtain_errors"
eval "${CUDA} python -m app.explain_sentences"
eval "${CUDA} python -m app.rag_sentences"

