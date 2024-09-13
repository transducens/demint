#!/bin/bash

FILE="C1_Cambridge_vidmp4"

# Set the CUDA environment variable and run the commands, logging the output.
CUDA_VISIBLE_DEVICES=2 time bash -c "
    time python -m app.extract_audio -vf assets/videos/${FILE}.mp4 &&
    time python -m app.diarize_audio -af assets/audios/${FILE}.wav &&
    time python -m app.whisper_speech -ad cache/diarized_audios/${FILE} &&
    time python -m app.prepare_sentences -tf cache/diarized_transcripts/${FILE}.json &&
    time python -m app.obtain_errors -sf cache/raw_sorted_sentence_collection/${FILE}.json &&
    time python -m app.explain_sentences -ef cache/errant_all_evaluation/${FILE}.json &&
    time python -m app.rag_sentences -xf cache/explained_sentences/${FILE}.json
" 2>&1 | tee log/evaluate_pipeline_${FILE}.log

