#!/bin/bash

set -e

CUDA="CUDA_VISIBLE_DEVICES=1"

eval "${CUDA} python -m app.extract_audio"  # from assets/videos to assets/audios 
eval "${CUDA} python -m app.diarize_audio"  # from assets/audios to cache/diarized_audios
eval "${CUDA} python -m app.whisper_speech"      # from cache/diarized_audios to cache/diarized_transcripts
eval "${CUDA} python -m app.prepare_sentences"  # from cache/diarized_transcripts to cache/raw_sorted_sentece_collection
eval "${CUDA} python -m app.obtain_errors"  # from cache/sentences to cache/errant_all_evaluation
eval "${CUDA} python -m app.explain_sentences"  # from cache/errat_all_evaluation to cache/explained_sentences
eval "${CUDA} python -m app.rag_sentences"  # from cache/explained_sentences to cache/rag_sentences

