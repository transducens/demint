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


def explain_sentences(file_manager, chat_llm, grammar_checker_lt, lang='en', input_path="", output_path=""):
    if not os.path.isfile(input_path):
        print(f"{input_path} is not found.")
        print(f"Processing {input_path}")
        obtain_errors.main()

    errant_all_evaluation = file_manager.read_from_json_file(input_path)
    explained_sentences = {}
    last_index = -1

    # for errant_annotation in errant_all_evaluation:
    #     index = errant_annotation['index']
    #     original_sentence = errant_annotation['original_sentence']
    #     corrected_sentence = errant_annotation['corrected_sentence']

    #     final_sentence_prompt = (
    #         f"You are an English teacher. Please explain the errors that were corrected in the following sentence:\n\n"
    #         f"Original: {original_sentence}\n"
    #         f"Corrected: {corrected_sentence}\n\n"
    #         f"List and explain the errors found in the original sentence and how they were corrected in the revised sentence."
    #     )

    #     lt_errors = grammar_checker_lt.check(original_sentence)

    #     llm_sentence_explained = chat_llm.get_answer(final_sentence_prompt)   # for the whole sentence
    #     #lt_errors = original_sentence['language_tool']

        
    #     error_type = errant_annotation['error_type']
    #     original_text = errant_annotation['original_text']  # Only the text of the sentence that was corrected
    #     corrected_text = errant_annotation['corrected_text']

    #     final_errant_prompt = (
    #         f"Please explain the errors that were found as briefly as possible, focusing only on the main idea and the broken rule in the English language:\n\n"
    #         f"Where the error type is {error_type}, " 
    #         f"the original sentence is {original_sentence}, " 
    #         f"the corrected sentence is {corrected_sentence}, "
    #         "and supposing that the first character is in position 0, "
    #         f"the error text is between the characters {errant_annotation['o_start']} and {errant_annotation['o_end']} in the original sentence, "
    #         f"and the corrected text is between the characters {errant_annotation['c_start']} and {errant_annotation['c_end']} in the corrected sentence."
    #     )

    #     errant_llm_explained = chat_llm.get_answer(final_errant_prompt)

    #     error_description = {
    #         'index': index,
    #         'speaker': errant_annotation['speaker'],
    #         'original_sentence': original_sentence,
    #         'corrected_sentence': corrected_sentence,
    #         'o_start': errant_annotation['o_start'],
    #         'o_end': errant_annotation['o_end'],
    #         'original_text': original_text,
    #         'c_start': errant_annotation['c_start'],
    #         'c_end': errant_annotation['c_start'],
    #         'corrected_text': corrected_text,
    #         'error_type': error_type,
    #         'llm_explanation': errant_llm_explained,
    #     }

    #     if last_index != index:
    #         explained_sentences[index] = {
    #             'speaker': errant_annotation['speaker'],
    #             'original_sentence' : original_sentence,
    #             't5_checked_sentence': corrected_sentence,
    #             'llm_explanation': llm_sentence_explained,
    #             'language_tool': lt_errors,
    #             'errant': [error_description],
    #         }
    #     else:
    #         explained_sentences[index]['errant'].append(error_description)

    #     last_index = index

########################

    def process_annotation(errant_annotation):
        index = errant_annotation['index']
        original_sentence = errant_annotation['original_sentence']
        corrected_sentence = errant_annotation['corrected_sentence']

        final_sentence_prompt = (
            f"You are an English teacher. Please explain the errors that were corrected in the following sentence:\n\n"
            f"Original: {original_sentence}\n"
            f"Corrected: {corrected_sentence}\n\n"
            f"List and explain the errors found in the original sentence and how they were corrected in the revised sentence."
        )

        lt_errors = grammar_checker_lt.check(original_sentence)

        llm_sentence_explained = chat_llm.get_answer(final_sentence_prompt)  # for the whole sentence

        error_type = errant_annotation['error_type']
        original_text = errant_annotation['original_text']  # Only the text of the sentence that was corrected
        corrected_text = errant_annotation['corrected_text']

        final_errant_prompt = (
            f"Please explain the errors that were found as briefly as possible, focusing only on the main idea and the broken rule in the English language:\n\n"
            f"Where the error type is {error_type}, "
            f"the original sentence is {original_sentence}, "
            f"the corrected sentence is {corrected_sentence}, "
            "and supposing that the first character is in position 0, "
            f"the error text is between the characters {errant_annotation['o_start']} and {errant_annotation['o_end']} in the original sentence, "
            f"and the corrected text is between the characters {errant_annotation['c_start']} and {errant_annotation['c_end']} in the corrected sentence."
        )

        errant_llm_explained = chat_llm.get_answer(final_errant_prompt)

        error_description = {
            'index': index,
            'speaker': errant_annotation['speaker'],
            'original_sentence': original_sentence,
            'corrected_sentence': corrected_sentence,
            'o_start': errant_annotation['o_start'],
            'o_end': errant_annotation['o_end'],
            'original_text': original_text,
            'c_start': errant_annotation['c_start'],
            'c_end': errant_annotation['c_end'],
            'corrected_text': corrected_text,
            'error_type': error_type,
            'llm_explanation': errant_llm_explained,
        }

        return index, error_description, llm_sentence_explained, lt_errors

    explained_sentences = {}
    last_index = None

    # Maximum number of threads
    max_threads = 5

    with ThreadPoolExecutor(max_threads) as executor:
        future_to_annotation = {executor.submit(process_annotation, errant_annotation): errant_annotation for errant_annotation in errant_all_evaluation}

        for future in as_completed(future_to_annotation):
            errant_annotation = future_to_annotation[future]
            try:
                index, error_description, llm_sentence_explained, lt_errors = future.result()

                if last_index != index:
                    explained_sentences[index] = {
                        'speaker': errant_annotation['speaker'],
                        'original_sentence': errant_annotation['original_sentence'],
                        't5_checked_sentence': errant_annotation['corrected_sentence'],
                        'llm_explanation': llm_sentence_explained,
                        'language_tool': lt_errors,
                        'errant': [error_description],
                    }
                else:
                    explained_sentences[index]['errant'].append(error_description)

                last_index = index
            except Exception as e:
                print(f"Error processing annotation {errant_annotation['index']}: {e}")

    # explained_sentences will contain the processed results

########################
    file_manager.save_to_json_file(output_path, explained_sentences)

    chat_llm.unload_model()
    return explained_sentences

def explain_sentences_of_directory(
        file_manager: FileManager,
        llm: ChatFactory,
        grammar_checker_lt: GrammarChecker,
        lang='en',
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
            print(f"Found diarized transcript file: {errant_evaluation_path}")

            explain_sentences(
                file_manager,
                llm,
                grammar_checker_lt, 
                'en', 
                errant_evaluation_path, 
                explained_sentences_path)


def get_args():
    parser = argparse.ArgumentParser(description="Explain the errors in a sentences collection file.")
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
    grammar_checker_lt = GrammarChecker("LT_API")
    llm_modelId = "google/gemma-1.1-7b-it"  # "google/gemma-1.1-2b-it"
    llm = ChatFactory.get_instance(llm_modelId)
    args = get_args()

    time.sleep(30)

    print("Starting to explain sentences...")

    if args.errant_file:
        if args.errant_directory:
            raise ValueError("Error: Please provide either an errant evaluation file or an errant evaluation directory.")
        elif args.explained_file:
            explain_sentences(file_manager, llm, grammar_checker_lt, 'en', args.errant_file, args.explained_file)
        elif args.explained_directory:
            errant_file = os.path.basename(args.errant_file)
            transcript_name, transcript_extension = os.path.splitext(errant_file)
            explain_sentences(file_manager, llm, grammar_checker_lt, 'en', args.errant_file, os.path.join(args.explained_directory, transcript_name + ".json"))
        else:
            errant_file = os.path.basename(args.errant_file)
            transcript_name, transcript_extension = os.path.splitext(errant_file)
            explain_sentences(file_manager, llm, grammar_checker_lt, 'en', args.errant_file, os.path.join(explained_directory, transcript_name + ".json"))

    elif args.errant_directory:
        if args.explained_directory:
            explain_sentences_of_directory(file_manager, llm, grammar_checker_lt, 'en', args.errant_directory, args.explained_directory)
        elif args.explained_file:
            raise ValueError("Error: Please provide a directory to save the explained sentences files.")
        else:
            explain_sentences_of_directory(file_manager, llm, grammar_checker_lt, 'en', args.errant_directory, explained_directory)
        
    elif args.explained_file or args.explained_directory:
        raise ValueError("Error: Please provide a transcript file or a transcript directory.")

    else:
        explain_sentences_of_directory(file_manager, llm, grammar_checker_lt, 'en', errant_directory, explained_directory)


    # Clean GPU VRAM
    if torch.cuda.is_available():
            torch.cuda.empty_cache()

if "__main__" == __name__:
    start = time.time()
    main()
    end = time.time()
    elapsed_time = end - start
    # Print the time it took to explain the sentences in the format {hh:mm:ss}
    print(f"Time taken to explain sentences: {time.strftime('%H:%M:%S', time.gmtime(elapsed_time))}")