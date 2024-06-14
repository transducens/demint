#!/bin/bash

# List of files or patterns to remove
files_to_remove=(
    "./cache/raw_sorted_sentence_collection.json"
    "./cache/explained_sentences.json"
    "./cache/errant_all_evaluation.json"
    "./cache/errant_detailed_evaluation.json"
    "./cache/errant_corrected_evaluation.json"
    "./cache/errant_simple_evaluation.json"
)

# Removing files
for file in "${files_to_remove[@]}"; do
    # Using the full path for the file pattern
    full_path="${file}"

    # Finding and removing files matching the pattern
    rm ${file} -v

    echo "Removed files matching pattern: $full_path"
done

echo "File removal complete."

