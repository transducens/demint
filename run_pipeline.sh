#!/bin/bash

CUDA="CUDA_VISIBLE_DEVICES=1"

eval "${CUDA} python -m app.prepare_sentences"
eval "${CUDA} python -m app.obtain_errors"
eval "${CUDA} python -m app.explain_sentences"
eval "${CUDA} python -m app.rag_sentences"

