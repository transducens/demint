import os
import argparse
import torch
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.file_manager import FileManager
from app.grammar_checker import GrammarChecker
import app.obtain_errors as obtain_errors
from app.llm.ChatFactory import ChatFactory


input_directory = "./cache/errant_all_evaluation"
output_directory = "./cache/explained_sentences"


def explain_sentences(file_manager, chat_llm, input_path="", output_path=""):
    print("-" * 50)
    print("Explaining sentences from:", input_path)
    
    if not os.path.isfile(input_path):
        print(f"{input_path} is not found.")
        print(f"Processing {input_path}")
        obtain_errors.main()

    errant_all_evaluation = file_manager.read_from_json_file(input_path)
    explained_sentences = {}
    last_index = -1

    batch_size = 6 # 10 is too much and 5 is too little for 11 GB VRAM. 6 is the sweet spot.
    for errant_annotation in range(0, len(errant_all_evaluation), batch_size):
        errant_annotations = errant_all_evaluation[errant_annotation:errant_annotation+batch_size]
        prompts = []
        errant_prompts = []

        for ea in errant_annotations:
            prompts.append(
                f"You are an English teacher. Please explain briefly and list the errors that were corrected in the following sentence:\n\n"
                f"Original: {ea['original_sentence']}\n"
                f"Corrected: {ea['corrected_sentence']}\n\n"
            )

            error_type = ea['error_type']
            original_text = ea['original_text']  # Only the text of the sentence that was corrected
            corrected_text = ea['corrected_text']
        
            errant_prompts.append(
                f"Please explain the error that was found as briefly as possible, focusing only on the main idea and the broken rule in the English language:\n\n"
                f"Where the error type is {error_type}, " 
                f"the original sentence is {ea['original_sentence']}, " 
                f"the corrected sentence is {ea['corrected_sentence']}. "
                "and supposing that the first character is in position 0, "
                f"the error text is between the characters {ea['o_start']} and {ea['o_end']} in the original sentence, "
                f"and the corrected text is between the characters {ea['c_start']} and {ea['c_end']} in the corrected sentence."
            )

        system_message = "You are an English teacher that will explain briefly the errors in the following sentence."

        llm_sentence_explained = chat_llm.get_answer_batch(contents=prompts, system_message=system_message)   # for the whole sentence
        errant_llm_explained = chat_llm.get_answer_batch(errant_prompts, system_message="")

        for i, ea in enumerate(errant_annotations):
            error_type = ea['error_type']
            original_text = ea['original_text']  # Only the text of the sentence that was corrected
            corrected_text = ea['corrected_text']

            error_description = {
                'index': ea['index'],
                'speaker': ea['speaker'],
                'original_sentence': ea['original_sentence'],
                'corrected_sentence': ea['corrected_sentence'],
                'o_start': ea['o_start'],
                'o_end': ea['o_end'],
                'original_text': original_text,
                'c_start': ea['c_start'],
                'c_end': ea['c_start'],
                'corrected_text': corrected_text,
                'error_type': error_type,
                'llm_explanation': errant_llm_explained[i],
            }

            if last_index != ea['index']:
                explained_sentences[ea['index']] = {
                    'speaker': ea['speaker'],
                    'original_sentence' : ea['original_sentence'],
                    't5_checked_sentence': ea['corrected_sentence'],
                    'llm_explanation': llm_sentence_explained[i],
                    'errant': [error_description],
                }
            else:
                explained_sentences[ea['index']]['errant'].append(error_description)

            last_index = ea['index']

    file_manager.save_to_json_file(output_path, explained_sentences)

    print(f"Explained sentences saved to: {output_path}")
    print("-" * 50)

    return explained_sentences


def explain_sentences_of_directory(
        file_manager: FileManager,
        llm: ChatFactory,
        errant_directory = "cache/errant_all_evaluation", 
        explained_sentences_directory = "cache/explained_sentences", 
    ):
    # Loop through the files in the directory
    for errant_evaluation_file in os.listdir(errant_directory):
        if errant_evaluation_file[0] == ".":
            continue

        errant_evaluation_path = os.path.join(errant_directory, errant_evaluation_file)
        explained_sentences_path = os.path.join(explained_sentences_directory, errant_evaluation_file)

        # Check if it's a file (not a directory)
        if os.path.isfile(errant_evaluation_path):
            # print(f"Found diarized transcript file: {errant_evaluation_path}")

            explain_sentences(
                file_manager,
                llm,
                errant_evaluation_path, 
                explained_sentences_path)
            
    llm.unload_model()


def get_args():
    parser = argparse.ArgumentParser(description="Explain the obtained errors from the errant evaluation files.")
    parser.add_argument("-ef", "--errant_file", type=str, help="Path to where the input errant evaluation file is located.")
    parser.add_argument("-xf", "--explained_file", type=str, help="Path to where the output explained sentences file will be saved.")
    parser.add_argument("-ed", "--errant_directory", type=str, help="Path to the directory containing the input errant evaluation files.")
    parser.add_argument("-xd", "--explained_directory", type=str, help="Path to the directory where the output explained sentences files will be saved.")

    return parser.parse_args()


def main():
    global input_directory, output_directory
    errant_directory = input_directory
    explained_directory = output_directory
    file_manager = FileManager()
    llm_modelId = "meta-llama/Meta-Llama-3.1-8B-Instruct"
    llm = ChatFactory.get_instance(llm_modelId)
    args = get_args()

    #print("Starting to explain sentences...")

    if args.errant_file:
        if args.errant_directory:
            raise ValueError("Error: Please provide either an errant evaluation file or an errant evaluation directory.")
        elif args.explained_file:
            explain_sentences(file_manager, llm, args.errant_file, args.explained_file)
        elif args.explained_directory:
            errant_file = os.path.basename(args.errant_file)
            transcript_name, transcript_extension = os.path.splitext(errant_file)
            explain_sentences(file_manager, llm, args.errant_file, os.path.join(args.explained_directory, transcript_name + ".json"))
        else:
            errant_file = os.path.basename(args.errant_file)
            transcript_name, transcript_extension = os.path.splitext(errant_file)
            explain_sentences(file_manager, llm, args.errant_file, os.path.join(explained_directory, transcript_name + ".json"))

    elif args.errant_directory:
        if args.explained_directory:
            explain_sentences_of_directory(file_manager, llm, args.errant_directory, args.explained_directory)
        elif args.explained_file:
            raise ValueError("Error: Please provide a directory to save the explained sentences files.")
        else:
            explain_sentences_of_directory(file_manager, llm, args.errant_directory, explained_directory)
        
    elif args.explained_file or args.explained_directory:
        raise ValueError("Error: Please provide a transcript file or a transcript directory.")

    else:
        explain_sentences_of_directory(file_manager, llm, errant_directory, explained_directory)


    # Clean GPU VRAM
    if torch.cuda.is_available():
            torch.cuda.empty_cache()

if "__main__" == __name__:
    print("*" * 50)
    print("EXPLANATION OF ERRORS STARTED")
    print("*" * 50)

    start = time.time()
    main()
    end = time.time()
    elapsed_time = end - start
    # Print the time it took to explain the sentences in the format {hh:mm:ss}
    print(f"Time taken to explain sentences: {time.strftime('%H:%M:%S', time.gmtime(elapsed_time))}")

    print("*" * 50)
    print("EXPLANATION OF ERRORS COMPLETED")
    print("*" * 50)