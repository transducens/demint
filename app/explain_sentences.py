import os

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

    for errant_annotation in errant_all_evaluation:
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

        llm_sentence_explained = chat_llm.get_answer(final_sentence_prompt)   # for the whole sentence
        #lt_errors = original_sentence['language_tool']

        
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
            'c_end': errant_annotation['c_start'],
            'corrected_text': corrected_text,
            'error_type': error_type,
            'llm_explanation': errant_llm_explained,
        }

        if last_index != index:
            explained_sentences[index] = {
                'speaker': errant_annotation['speaker'],
                'original_sentence' : original_sentence,
                't5_checked_sentence': corrected_sentence,
                'llm_explanation': llm_sentence_explained,
                'language_tool': lt_errors,
                'errant': [error_description],
            }
        else:
            explained_sentences[index]['errant'].append(error_description)

        last_index = index

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


def main():
    global input_directory, output_directory
    file_manager = FileManager()
    grammar_checker_lt = GrammarChecker("LT_API")
    llm_modelId = "google/gemma-1.1-7b-it"  # "google/gemma-1.1-2b-it"
    llm = ChatFactory.get_instance(llm_modelId)

    explain_sentences_of_directory(
        file_manager, 
        llm, 
        grammar_checker_lt, 
        'en', 
        input_directory, 
        output_directory)


if __name__ == '__main__':
    main()
