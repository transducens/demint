#!/bin/bash

# List of directories to clean
DIRS_TO_CLEAN=(
  "./cache"
  "./cache/diarized_transcripts"
  "./cache/raw_sorted_sentence_collection"
  "./cache/errant_all_evaluation"
  "./cache/explained_sentences"
  "./cache/rag_sentences"
)

# List of directories where all subdirectories should be removed
DIRS_TO_CLEAN_SUBDIRS=(
  "./cache/diarized_audios"
)

# Function to remove all files in a specified directory
clean_files() {
  local DIR=$1
  if [ -d "$DIR" ]; then
    echo "Cleaning files in directory: $DIR"
    rm -f "$DIR"/*
    echo "All files removed from: $DIR"
  else
    echo "Directory does not exist: $DIR"
  fi
}

# Function to remove all subdirectories in a specified directory
clean_subdirectories() {
  local DIR=$1
  if [ -d "$DIR" ]; then
    echo "Removing all subdirectories in: $DIR"
    find "$DIR" -mindepth 1 -type d -exec rm -rf {} +
    echo "All subdirectories removed from: $DIR"
  else
    echo "Directory does not exist: $DIR"
  fi
}

# Clean files in specified directories
for DIR in "${DIRS_TO_CLEAN[@]}"; do
  clean_files "$DIR"
done

# Clean subdirectories in specified directories
for DIR in "${DIRS_TO_CLEAN_SUBDIRS[@]}"; do
  clean_subdirectories "$DIR"
done
