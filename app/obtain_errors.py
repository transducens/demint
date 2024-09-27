import errant
import os
import argparse

from app.file_manager import FileManager
import app.prepare_sentences as prepare_sentences
from app.grammar_checker import GrammarChecker


input_directory = "./cache/raw_sorted_sentence_collection"
# Only using the all errors version for now
output_directories = {
    'errant_all_errors':                './cache/errant_all_evaluation',
    'errant_detailed_errors':           './cache/errant_detailed_evaluation',
    'errant_corrected_errors':          './cache/errant_corrected_evaluation',
    'errant_simple_errors':             './cache/errant_simple_evaluation',       
}
ignore_errors_list = [
    "R:SPELL", "M:SPELL", "U:SPELL",
    "R:ORTH", "U:ORTH", "M:ORTH",
    "R:PUNCT", "U:PUNCT", "M:PUNCT",
    "R:OTHER", "U:OTHER", "M:OTHER",
]


def obtain_errors(file_manager, grammar_checker_t5, lang='en', input_path="", output_path=""):
    print("-" * 50, flush=True)
    print("Obtaining errors from:", input_path, flush=True)

    if not os.path.isfile(input_path):
        print(f"{input_path} is not found.", flush=True)
        print(f"Processing {input_path}", flush=True)
        prepare_sentences.main()

    raw_sentence_collection = file_manager.read_from_json_file(input_path)
    if raw_sentence_collection is None:
        print(f"Error: {input_path} not found.", flush=True)
        return None
    
    annotator = errant.load(lang)

    detailed_errors = {}
    corrected_errors = {}
    simple_errors = {}

    all_errors = []
    for index, value in raw_sentence_collection.items(): 
        original_sentence = value['original_sentence']

        t5_checked_sentence = grammar_checker_t5.correct_sentences([original_sentence])[0]

        if original_sentence == t5_checked_sentence:
            continue

        annotated_original_sentence = annotator.parse(original_sentence)
        annotated_t5_checked_sentence = annotator.parse(t5_checked_sentence)
        annotations = annotator.annotate(annotated_original_sentence, annotated_t5_checked_sentence)            

        for e in annotations:
            error_type = e.type

            if error_type in ignore_errors_list:
                #print(f"Ignoring error type: {error_type}", flush=True)
                continue

            print(e, flush=True)

            original_text = e.o_str
            corrected_text = e.c_str

            error_description = {
                'index': index,
                'speaker': value['speaker'],
                'original_sentence': original_sentence,
                'corrected_sentence': t5_checked_sentence,
                'o_start': e.o_start,
                'o_end': e.o_end,
                'original_text': original_text,
                'c_start': e.c_start,
                'c_end': e.c_end,
                'corrected_text': corrected_text,
                'error_type': error_type,
            }
            
            all_errors.append(error_description)

    file_manager.save_to_json_file(output_path, all_errors)

    print(f"Saved all errors to: {output_path}", flush=True)
    print("-" * 50, flush=True)

    return all_errors, detailed_errors, corrected_errors, simple_errors

def obtain_errors_of_directory(
        file_manager: FileManager,
        grammar_checker_t5: GrammarChecker,
        lang='en',
        sentence_collection_directory="cache/raw_sorted_sentence_collection", 
        errant_directory="cache/errant_all_evaluation", 
    ):
    # Loop through the files in the directory
    for sentence_collection_file in os.listdir(sentence_collection_directory):
        if sentence_collection_file[0] == ".":
            continue

        sentence_collection_path = os.path.join(sentence_collection_directory, sentence_collection_file)
        errant_evaluation_path = os.path.join(errant_directory, sentence_collection_file)

        # Check if it's a file (not a directory)
        if os.path.isfile(sentence_collection_path):
            #print(f"Found diarized transcript file: {sentence_collection_path}", flush=True)

            obtain_errors(
                file_manager, 
                grammar_checker_t5, 
                'en', 
                sentence_collection_path, 
                errant_evaluation_path)


def get_args():
    parser = argparse.ArgumentParser(description="Obtain errors from a sentences collection file.")
    parser.add_argument("-sf", "--sentences_file", type=str, help="Path to where the input sentences collection file is located.")
    parser.add_argument("-ef", "--errant_file", type=str, help="Path to where the output errant evaluation file will be saved.")
    parser.add_argument("-sd", "--sentences_directory", type=str, help="Path to the directory containing the input sentences collection files.")
    parser.add_argument("-ed", "--errant_directory", type=str, help="Path to the directory where the output errant evaluation files will be saved.")

    return parser.parse_args()


def main():
    global input_directory, output_directories
    file_manager = FileManager()
    grammar_checker_t5 = GrammarChecker(gec_model="T5")
    sentences_directory = input_directory
    errant_directory = output_directories['errant_all_errors']
    args = get_args()

    if args.sentences_file:
        if args.sentences_directory:
            raise ValueError("Error: Please provide either a sentences file or a sentences directory.")
        elif args.errant_file:
            obtain_errors(file_manager, grammar_checker_t5, 'en', args.sentences_file, args.errant_file)
        elif args.errant_directory:
            sentences_file = os.path.basename(args.sentences_file)
            transcript_name, transcript_extension = os.path.splitext(sentences_file)
            obtain_errors(file_manager, grammar_checker_t5, 'en', args.sentences_file, os.path.join(args.errant_directory, transcript_name + ".json"))
        else:
            sentences_file = os.path.basename(args.sentences_file)
            transcript_name, transcript_extension = os.path.splitext(sentences_file)
            obtain_errors(file_manager, grammar_checker_t5, 'en', args.sentences_file, os.path.join(errant_directory, transcript_name + ".json"))

    elif args.sentences_directory:
        if args.errant_directory:
            obtain_errors_of_directory(file_manager, grammar_checker_t5, 'en', args.sentences_directory, args.errant_directory)
        elif args.errant_file:
            raise ValueError("Error: Please provide a directory to save the sentences collection files.")
        else:
            obtain_errors_of_directory(file_manager, grammar_checker_t5, 'en', args.sentences_directory, errant_directory)
        
    elif args.errant_file or args.errant_directory:
        raise ValueError("Error: Please provide a transcript file or a transcript directory.")

    else:
        obtain_errors_of_directory(file_manager, grammar_checker_t5, 'en', sentences_directory, errant_directory)


if "__main__" == __name__:
    print("*" * 50, flush=True)
    print("OBTAINING ERRORS STARTED", flush=True)
    print("*" * 50, flush=True)

    main()

    print("*" * 50, flush=True)
    print("OBTAINING ERRORS COMPLETED", flush=True)
    print("*" * 50, flush=True)